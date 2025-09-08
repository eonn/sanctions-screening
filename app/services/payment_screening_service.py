"""
Payment screening service for real-time payment processing.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""
import logging
import time
import asyncio
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import (
    PaymentMessage, 
    PaymentScreeningResult, 
    PaymentStatus, 
    DecisionType,
    EntityCreate,
    EntityType
)
from app.services.screening_service import ScreeningService
from app.services.messaging.mq_service import mq_service
from app.services.messaging.kafka_service import kafka_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class PaymentScreeningService:
    """Service for real-time payment screening."""
    
    def __init__(self):
        """Initialize the payment screening service."""
        self.screening_service = ScreeningService()
        self.processing_stats = {
            "total_processed": 0,
            "approved": 0,
            "rejected": 0,
            "blocked": 0,
            "errors": 0,
            "avg_processing_time_ms": 0
        }
        self.processing_times = []
        
    async def initialize(self) -> None:
        """Initialize the payment screening service."""
        try:
            # Initialize screening service
            await self.screening_service.initialize()
            
            # Connect to messaging services
            await mq_service.connect()
            await kafka_service.connect_producer()
            
            # Set up message handlers
            await self._setup_message_handlers()
            
            logger.info("Payment screening service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize payment screening service: {str(e)}")
            raise
    
    async def _setup_message_handlers(self) -> None:
        """Set up message handlers for MQ and Kafka."""
        try:
            # Set up MQ consumer for payment messages
            await mq_service.declare_queue(
                settings.mq_payment_queue,
                routing_key="payment.*"
            )
            
            await mq_service.start_consumer(
                settings.mq_payment_queue,
                self._process_payment_message
            )
            
            # Set up Kafka consumer for payment messages
            await kafka_service.start_consumer(
                settings.kafka_payment_topic,
                self._process_payment_message
            )
            
            logger.info("Message handlers set up successfully")
            
        except Exception as e:
            logger.error(f"Failed to set up message handlers: {str(e)}")
            raise
    
    async def _process_payment_message(self, payment_message: PaymentMessage) -> None:
        """Process a payment message for screening."""
        start_time = time.time()
        
        try:
            logger.info(f"Processing payment message: {payment_message.payment_id}")
            
            # Screen both sender and recipient
            sender_screening, recipient_screening = await asyncio.gather(
                self._screen_entity(payment_message.sender_name, payment_message.sender_country),
                self._screen_entity(payment_message.recipient_name, payment_message.recipient_country),
                return_exceptions=True
            )
            
            # Determine overall risk and decision
            overall_risk_score, decision, status = self._determine_payment_decision(
                sender_screening, recipient_screening
            )
            
            # Create screening result
            processing_time_ms = int((time.time() - start_time) * 1000)
            screening_result = PaymentScreeningResult(
                payment_id=payment_message.payment_id,
                transaction_id=payment_message.transaction_id,
                screening_id=int(time.time() * 1000),  # Simple ID generation
                sender_screening=sender_screening if not isinstance(sender_screening, Exception) else None,
                recipient_screening=recipient_screening if not isinstance(recipient_screening, Exception) else None,
                overall_risk_score=overall_risk_score,
                decision=decision,
                status=status,
                processing_time_ms=processing_time_ms,
                metadata={
                    "payment_type": payment_message.payment_type,
                    "amount": payment_message.amount,
                    "currency": payment_message.currency
                }
            )
            
            # Update statistics
            self._update_statistics(screening_result)
            
            # Publish result to output queues
            await self._publish_screening_result(screening_result)
            
            # Store result in database
            await self._store_screening_result(screening_result)
            
            logger.info(f"Payment {payment_message.payment_id} processed: {decision.value}")
            
        except Exception as e:
            logger.error(f"Error processing payment message {payment_message.payment_id}: {str(e)}")
            self.processing_stats["errors"] += 1
            
            # Publish error result
            error_result = PaymentScreeningResult(
                payment_id=payment_message.payment_id,
                transaction_id=payment_message.transaction_id,
                screening_id=int(time.time() * 1000),
                overall_risk_score=1.0,  # High risk due to error
                decision=DecisionType.BLOCK,
                status=PaymentStatus.ERROR,
                processing_time_ms=int((time.time() - start_time) * 1000),
                metadata={"error": str(e)}
            )
            
            await self._publish_screening_result(error_result)
    
    async def _screen_entity(self, name: str, country: Optional[str] = None) -> Any:
        """Screen an entity against sanctions lists."""
        try:
            # Create entity data
            entity_data = EntityCreate(
                name=name,
                entity_type=EntityType.INDIVIDUAL,  # Default to individual
                nationality=country
            )
            
            # Perform screening
            result = await self.screening_service.screen_entity_async(entity_data)
            return result
            
        except Exception as e:
            logger.error(f"Error screening entity {name}: {str(e)}")
            raise
    
    def _determine_payment_decision(
        self, 
        sender_screening: Any, 
        recipient_screening: Any
    ) -> Tuple[float, DecisionType, PaymentStatus]:
        """Determine the overall decision for a payment based on screening results."""
        try:
            # Extract risk scores
            sender_risk = sender_screening.overall_risk_score if sender_screening and not isinstance(sender_screening, Exception) else 0.0
            recipient_risk = recipient_screening.overall_risk_score if recipient_screening and not isinstance(recipient_screening, Exception) else 0.0
            
            # Calculate overall risk (max of sender and recipient risk)
            overall_risk_score = max(sender_risk, recipient_risk)
            
            # Determine decision based on risk thresholds
            if overall_risk_score >= settings.high_risk_threshold:
                decision = DecisionType.BLOCK
                status = PaymentStatus.BLOCKED
            elif overall_risk_score >= settings.medium_risk_threshold:
                decision = DecisionType.REVIEW
                status = PaymentStatus.SCREENING
            else:
                decision = DecisionType.CLEAR
                status = PaymentStatus.APPROVED
            
            return overall_risk_score, decision, status
            
        except Exception as e:
            logger.error(f"Error determining payment decision: {str(e)}")
            return 1.0, DecisionType.BLOCK, PaymentStatus.ERROR
    
    def _update_statistics(self, result: PaymentScreeningResult) -> None:
        """Update processing statistics."""
        self.processing_stats["total_processed"] += 1
        self.processing_times.append(result.processing_time_ms)
        
        # Keep only last 1000 processing times for average calculation
        if len(self.processing_times) > 1000:
            self.processing_times = self.processing_times[-1000:]
        
        # Update decision counts
        if result.decision == DecisionType.CLEAR:
            self.processing_stats["approved"] += 1
        elif result.decision == DecisionType.REVIEW:
            self.processing_stats["rejected"] += 1
        elif result.decision == DecisionType.BLOCK:
            self.processing_stats["blocked"] += 1
        
        # Update average processing time
        self.processing_stats["avg_processing_time_ms"] = sum(self.processing_times) // len(self.processing_times)
    
    async def _publish_screening_result(self, result: PaymentScreeningResult) -> None:
        """Publish screening result to output queues."""
        try:
            # Publish to MQ result queue
            await mq_service.publish_message(
                PaymentMessage(
                    payment_id=result.payment_id,
                    transaction_id=result.transaction_id,
                    sender_name="",  # Not needed for result
                    sender_account="",
                    recipient_name="",
                    recipient_account="",
                    amount=0.0,
                    currency="",
                    payment_type="wire_transfer"  # Default
                ),
                routing_key=f"screening.result.{result.decision.value}"
            )
            
            # Publish to Kafka result topic
            await kafka_service.publish_message(
                settings.kafka_result_topic,
                PaymentMessage(
                    payment_id=result.payment_id,
                    transaction_id=result.transaction_id,
                    sender_name="",
                    sender_account="",
                    recipient_name="",
                    recipient_account="",
                    amount=0.0,
                    currency="",
                    payment_type="wire_transfer"
                ),
                key=result.payment_id
            )
            
        except Exception as e:
            logger.error(f"Error publishing screening result: {str(e)}")
    
    async def _store_screening_result(self, result: PaymentScreeningResult) -> None:
        """Store screening result in database."""
        try:
            # This would typically store the result in a database
            # For now, we'll just log it
            logger.info(f"Stored screening result for payment {result.payment_id}")
            
        except Exception as e:
            logger.error(f"Error storing screening result: {str(e)}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            **self.processing_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            await mq_service.disconnect()
            await kafka_service.disconnect()
            await self.screening_service.cleanup()
            
            logger.info("Payment screening service cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


# Global payment screening service instance
payment_screening_service = PaymentScreeningService()

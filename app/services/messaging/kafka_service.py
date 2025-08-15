"""
Kafka service for handling payment message streaming.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""
import logging
import json
import asyncio
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError
from app.models.schemas import PaymentMessage, KafkaMessage
from app.core.config import settings

logger = logging.getLogger(__name__)


class KafkaService:
    """Kafka service for handling payment message streaming."""
    
    def __init__(self):
        """Initialize the Kafka service."""
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.consumer_tasks: Dict[str, asyncio.Task] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
    async def connect_producer(self) -> None:
        """Connect to Kafka as a producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                enable_idempotence=True
            )
            
            await self.producer.start()
            logger.info("Successfully connected to Kafka as producer")
            
        except Exception as e:
            logger.error(f"Failed to connect to Kafka as producer: {str(e)}")
            raise
    
    async def connect_consumer(
        self, 
        topic: str, 
        group_id: str,
        auto_offset_reset: str = 'earliest'
    ) -> None:
        """Connect to Kafka as a consumer for a specific topic."""
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None
            )
            
            await consumer.start()
            self.consumers[topic] = consumer
            
            logger.info(f"Successfully connected to Kafka as consumer for topic: {topic}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Kafka as consumer for topic {topic}: {str(e)}")
            raise
    
    async def publish_message(
        self, 
        topic: str, 
        message: PaymentMessage, 
        key: Optional[str] = None
    ) -> None:
        """Publish a payment message to a Kafka topic."""
        try:
            if not self.producer:
                await self.connect_producer()
            
            message_data = message.model_dump()
            message_data['timestamp'] = message_data['timestamp'].isoformat()
            
            await self.producer.send_and_wait(
                topic=topic,
                value=message_data,
                key=key
            )
            
            logger.info(f"Published message to Kafka topic: {topic}")
            
        except Exception as e:
            logger.error(f"Failed to publish message to Kafka topic {topic}: {str(e)}")
            raise
    
    async def start_consumer(
        self, 
        topic: str, 
        handler: Callable[[PaymentMessage], None],
        group_id: Optional[str] = None
    ) -> None:
        """Start consuming messages from a Kafka topic."""
        try:
            if group_id is None:
                group_id = f"sanctions-screening-{topic}"
            
            if topic not in self.consumers:
                await self.connect_consumer(topic, group_id)
            
            consumer = self.consumers[topic]
            
            # Start consuming
            consumer_task = asyncio.create_task(
                self._consume_messages(consumer, handler)
            )
            
            self.consumer_tasks[topic] = consumer_task
            self.message_handlers[topic] = handler
            
            logger.info(f"Started consumer for Kafka topic: {topic}")
            
        except Exception as e:
            logger.error(f"Failed to start consumer for Kafka topic {topic}: {str(e)}")
            raise
    
    async def _consume_messages(
        self, 
        consumer: AIOKafkaConsumer, 
        handler: Callable[[PaymentMessage], None]
    ) -> None:
        """Consume messages from a Kafka topic."""
        try:
            async for message in consumer:
                try:
                    # Parse message
                    message_data = message.value
                    message_data['timestamp'] = datetime.fromisoformat(message_data['timestamp'])
                    payment_message = PaymentMessage.model_validate(message_data)
                    
                    # Process message
                    await asyncio.create_task(
                        self._process_message(payment_message, handler)
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {str(e)}")
                    # Continue processing other messages
                    
        except Exception as e:
            logger.error(f"Error in Kafka consumer: {str(e)}")
            raise
    
    async def _process_message(
        self, 
        payment_message: PaymentMessage, 
        handler: Callable[[PaymentMessage], None]
    ) -> None:
        """Process a payment message."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(payment_message)
            else:
                handler(payment_message)
                
        except Exception as e:
            logger.error(f"Error in Kafka message handler: {str(e)}")
            raise
    
    async def stop_consumer(self, topic: str) -> None:
        """Stop consuming messages from a Kafka topic."""
        if topic in self.consumer_tasks:
            self.consumer_tasks[topic].cancel()
            del self.consumer_tasks[topic]
            del self.message_handlers[topic]
            
        if topic in self.consumers:
            await self.consumers[topic].stop()
            del self.consumers[topic]
            
        logger.info(f"Stopped consumer for Kafka topic: {topic}")
    
    async def stop_all_consumers(self) -> None:
        """Stop all Kafka consumers."""
        for topic in list(self.consumer_tasks.keys()):
            await self.stop_consumer(topic)
    
    async def disconnect(self) -> None:
        """Disconnect from Kafka."""
        try:
            await self.stop_all_consumers()
            
            if self.producer:
                await self.producer.stop()
                
            logger.info("Disconnected from Kafka")
            
        except Exception as e:
            logger.error(f"Error disconnecting from Kafka: {str(e)}")
    
    async def get_topic_info(self, topic: str) -> Dict[str, Any]:
        """Get information about a Kafka topic."""
        try:
            if topic not in self.consumers:
                return {"error": "Topic not found"}
            
            consumer = self.consumers[topic]
            # Note: This is a simplified version. In production, you'd use Kafka admin API
            return {
                "topic": topic,
                "consumer_group": consumer.group_id,
                "active": topic in self.consumer_tasks
            }
            
        except Exception as e:
            logger.error(f"Error getting topic info: {str(e)}")
            return {"error": str(e)}


# Global Kafka service instance
kafka_service = KafkaService()

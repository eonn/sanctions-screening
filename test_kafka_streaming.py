#!/usr/bin/env python3
"""
Test script for Kafka message streaming with payment screening.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""
import asyncio
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Any
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from app.models.schemas import PaymentMessage, PaymentType
from app.services.screening_service import ScreeningService

class KafkaStreamingTest:
    """Test class for Kafka streaming functionality."""
    
    def __init__(self):
        """Initialize the Kafka streaming test."""
        self.bootstrap_servers = 'localhost:9092'
        self.payment_topic = 'payment_messages'
        self.result_topic = 'screening_results'
        self.consumer_group = 'test-consumer-group'
        
        # Sample payment data for testing
        self.sample_payments = [
            {
                "sender_name": "John Doe",
                "recipient_name": "Jane Smith",
                "amount": 1000.00,
                "risk_level": "low"
            },
            {
                "sender_name": "Mohammed Ali",
                "recipient_name": "Sarah Johnson", 
                "amount": 2500.00,
                "risk_level": "medium"
            },
            {
                "sender_name": "Osama Bin Laden",
                "recipient_name": "John Smith",
                "amount": 5000.00,
                "risk_level": "high"
            },
            {
                "sender_name": "Alice Johnson",
                "recipient_name": "Bob Wilson",
                "amount": 750.00,
                "risk_level": "low"
            },
            {
                "sender_name": "Carlos Rodriguez",
                "recipient_name": "Maria Garcia",
                "amount": 3000.00,
                "risk_level": "medium"
            }
        ]
        
        self.screening_service = None
        self.producer = None
        self.consumer = None
        self.processed_messages = []
        
    async def initialize(self):
        """Initialize the test environment."""
        print("🚀 Initializing Kafka Streaming Test...")
        
        # Initialize screening service
        print("📋 Initializing screening service...")
        self.screening_service = ScreeningService()
        await self.screening_service.initialize()
        
        # Initialize Kafka producer
        print("📤 Initializing Kafka producer...")
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        
        # Initialize Kafka consumer
        print("📥 Initializing Kafka consumer...")
        self.consumer = KafkaConsumer(
            self.result_topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.consumer_group,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        print("✅ Kafka streaming test initialized successfully!")
        
    def create_payment_message(self, payment_data: Dict[str, Any], payment_id: str) -> PaymentMessage:
        """Create a payment message from payment data."""
        return PaymentMessage(
            payment_id=payment_id,
            transaction_id=f"TXN_{payment_id}",
            sender_name=payment_data["sender_name"],
            sender_account=f"ACC_{random.randint(100000, 999999)}",
            sender_bank="TESTBANK",
            sender_country="US",
            recipient_name=payment_data["recipient_name"],
            recipient_account=f"ACC_{random.randint(100000, 999999)}",
            recipient_bank="RECIPIENTBANK",
            recipient_country="CA",
            amount=payment_data["amount"],
            currency="USD",
            payment_type=random.choice(list(PaymentType)),
            timestamp=datetime.utcnow(),
            metadata={
                "test_case": True,
                "expected_risk": payment_data["risk_level"]
            }
        )
    
    async def produce_payment_messages(self, num_messages: int = 10):
        """Produce payment messages to Kafka topic."""
        print(f"\n📤 Producing {num_messages} payment messages to Kafka...")
        
        for i in range(num_messages):
            # Select random payment data
            payment_data = random.choice(self.sample_payments)
            payment_id = f"PAY_STREAM_{i+1:03d}"
            
            # Create payment message
            payment_message = self.create_payment_message(payment_data, payment_id)
            
            # Convert to dict for Kafka
            message_data = payment_message.model_dump()
            message_data['timestamp'] = message_data['timestamp'].isoformat()
            
            # Send to Kafka
            try:
                future = self.producer.send(
                    self.payment_topic,
                    value=message_data,
                    key=payment_id
                )
                
                # Wait for the message to be sent
                record_metadata = future.get(timeout=10)
                
                print(f"  ✅ Sent payment {payment_id}: {payment_data['sender_name']} → {payment_data['recipient_name']} (${payment_data['amount']})")
                print(f"     Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
                
            except KafkaError as e:
                print(f"  ❌ Failed to send payment {payment_id}: {str(e)}")
            
            # Small delay between messages
            await asyncio.sleep(0.5)
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        print(f"✅ Successfully produced {num_messages} payment messages to Kafka")
    
    async def consume_and_process_messages(self, timeout_seconds: int = 30):
        """Consume messages from Kafka and process them."""
        print(f"\n📥 Consuming and processing messages from Kafka (timeout: {timeout_seconds}s)...")
        
        start_time = time.time()
        processed_count = 0
        
        try:
            for message in self.consumer:
                try:
                    # Parse message
                    message_data = message.value
                    payment_id = message.key.decode('utf-8') if message.key else "unknown"
                    
                    print(f"\n📨 Received message for payment: {payment_id}")
                    print(f"   Topic: {message.topic}, Partition: {message.partition}, Offset: {message.offset}")
                    
                    # Process the payment message
                    await self.process_payment_message(message_data, payment_id)
                    processed_count += 1
                    
                    # Check timeout
                    if time.time() - start_time > timeout_seconds:
                        print(f"⏰ Timeout reached ({timeout_seconds}s)")
                        break
                        
                except Exception as e:
                    print(f"❌ Error processing message: {str(e)}")
                    
        except KeyboardInterrupt:
            print("\n⏹️  Stopping message consumption...")
        
        print(f"✅ Processed {processed_count} messages from Kafka")
    
    async def process_payment_message(self, message_data: Dict[str, Any], payment_id: str):
        """Process a payment message for screening."""
        try:
            # Convert back to PaymentMessage
            message_data['timestamp'] = datetime.fromisoformat(message_data['timestamp'])
            payment_message = PaymentMessage.model_validate(message_data)
            
            print(f"  🔍 Screening payment: {payment_message.sender_name} → {payment_message.recipient_name}")
            
            # Screen both sender and recipient
            from app.models.schemas import EntityCreate, ScreeningRequest
            
            sender_screening = await self.screening_service.screen_entity_async(
                ScreeningRequest(
                    entity=EntityCreate(
                        name=payment_message.sender_name,
                        entity_type="individual",
                        nationality=payment_message.sender_country
                    )
                )
            )
            
            recipient_screening = await self.screening_service.screen_entity_async(
                ScreeningRequest(
                    entity=EntityCreate(
                        name=payment_message.recipient_name,
                        entity_type="individual",
                        nationality=payment_message.recipient_country
                    )
                )
            )
            
            # Calculate overall risk
            overall_risk_score = max(
                sender_screening['overall_risk_score'],
                recipient_screening['overall_risk_score']
            )
            
            # Determine decision
            if overall_risk_score >= 0.9:
                decision = "block"
                status = "blocked"
                emoji = "🚫"
            elif overall_risk_score >= 0.7:
                decision = "review"
                status = "screening"
                emoji = "⚠️"
            else:
                decision = "clear"
                status = "approved"
                emoji = "✅"
            
            # Create result
            result = {
                "payment_id": payment_id,
                "transaction_id": payment_message.transaction_id,
                "sender_risk": sender_screening['overall_risk_score'],
                "recipient_risk": recipient_screening['overall_risk_score'],
                "overall_risk_score": overall_risk_score,
                "decision": decision,
                "status": status,
                "processing_time": time.time(),
                "metadata": {
                    "payment_type": payment_message.payment_type,
                    "amount": payment_message.amount,
                    "currency": payment_message.currency
                }
            }
            
            # Send result back to Kafka
            self.producer.send(
                self.result_topic,
                value=result,
                key=payment_id
            )
            
            print(f"  {emoji} Result: {decision.upper()} (Risk: {overall_risk_score:.3f})")
            print(f"     Sender Risk: {sender_screening['overall_risk_score']:.3f}")
            print(f"     Recipient Risk: {recipient_screening['overall_risk_score']:.3f}")
            
            # Store processed message
            self.processed_messages.append(result)
            
        except Exception as e:
            print(f"  ❌ Error processing payment {payment_id}: {str(e)}")
    
    def print_statistics(self):
        """Print test statistics."""
        print(f"\n📊 KAFKA STREAMING TEST STATISTICS")
        print(f"{'='*50}")
        print(f"Total messages processed: {len(self.processed_messages)}")
        
        if self.processed_messages:
            decisions = [msg['decision'] for msg in self.processed_messages]
            risk_scores = [msg['overall_risk_score'] for msg in self.processed_messages]
            
            print(f"Decisions:")
            print(f"  ✅ Approved: {decisions.count('clear')}")
            print(f"  ⚠️  Review: {decisions.count('review')}")
            print(f"  🚫 Blocked: {decisions.count('block')}")
            
            print(f"Risk Scores:")
            print(f"  Average: {sum(risk_scores) / len(risk_scores):.3f}")
            print(f"  Min: {min(risk_scores):.3f}")
            print(f"  Max: {max(risk_scores):.3f}")
    
    async def cleanup(self):
        """Cleanup resources."""
        print("\n🧹 Cleaning up resources...")
        
        if self.producer:
            self.producer.close()
        
        if self.consumer:
            self.consumer.close()
        
        if self.screening_service:
            await self.screening_service.cleanup()
        
        print("✅ Cleanup completed")

async def main():
    """Main test function."""
    print("🎯 KAFKA STREAMING TEST FOR SANCTIONS SCREENING")
    print("=" * 60)
    
    test = KafkaStreamingTest()
    
    try:
        # Initialize
        await test.initialize()
        
        # Produce messages
        await test.produce_payment_messages(num_messages=15)
        
        # Consume and process messages
        await test.consume_and_process_messages(timeout_seconds=45)
        
        # Print statistics
        test.print_statistics()
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await test.cleanup()
    
    print("\n🎉 Kafka streaming test completed!")

if __name__ == "__main__":
    asyncio.run(main())

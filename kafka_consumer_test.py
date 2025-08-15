#!/usr/bin/env python3
"""
Simple Kafka consumer for testing payment message processing.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""
import json
import time
from datetime import datetime
from kafka import KafkaConsumer
from app.services.screening_service import ScreeningService
from app.models.schemas import EntityCreate, ScreeningRequest
import asyncio

class KafkaConsumerTest:
    """Kafka consumer for payment message processing."""
    
    def __init__(self):
        self.bootstrap_servers = 'localhost:9092'
        self.payment_topic = 'payment_messages'
        self.result_topic = 'screening_results'
        self.consumer_group = 'test-consumer-group'
        self.screening_service = None
        
    async def initialize(self):
        """Initialize the consumer and screening service."""
        print("🚀 Initializing Kafka Consumer Test")
        
        # Initialize screening service
        self.screening_service = ScreeningService()
        await self.screening_service.initialize()
        
        # Initialize consumer
        self.consumer = KafkaConsumer(
            self.payment_topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.consumer_group,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        print("✅ Consumer initialized successfully")
    
    async def process_messages(self, timeout_seconds=30):
        """Process messages from Kafka."""
        print(f"📥 Starting to consume messages (timeout: {timeout_seconds}s)...")
        
        start_time = time.time()
        processed_count = 0
        
        try:
            for message in self.consumer:
                try:
                    # Parse message
                    message_data = message.value
                    payment_id = message.key.decode('utf-8') if message.key else "unknown"
                    
                    print(f"\n📨 Processing payment: {payment_id}")
                    print(f"   Topic: {message.topic}, Partition: {message.partition}, Offset: {message.offset}")
                    
                    # Convert timestamp
                    message_data['timestamp'] = datetime.fromisoformat(message_data['timestamp'])
                    
                    # Process payment
                    await self.process_payment(message_data, payment_id)
                    processed_count += 1
                    
                    # Check timeout
                    if time.time() - start_time > timeout_seconds:
                        print(f"⏰ Timeout reached ({timeout_seconds}s)")
                        break
                        
                except Exception as e:
                    print(f"❌ Error processing message: {str(e)}")
                    
        except KeyboardInterrupt:
            print("\n⏹️  Stopping consumer...")
        
        print(f"✅ Processed {processed_count} messages")
    
    async def process_payment(self, message_data, payment_id):
        """Process a single payment message."""
        try:
            sender_name = message_data['sender_name']
            recipient_name = message_data['recipient_name']
            amount = message_data['amount']
            
            print(f"  🔍 Screening: {sender_name} → {recipient_name} (${amount:.2f})")
            
            # Screen sender
            sender_screening = await self.screening_service.screen_entity_async(
                ScreeningRequest(
                    entity=EntityCreate(
                        name=sender_name,
                        entity_type="individual",
                        nationality=message_data.get('sender_country', 'US')
                    )
                )
            )
            
            # Screen recipient
            recipient_screening = await self.screening_service.screen_entity_async(
                ScreeningRequest(
                    entity=EntityCreate(
                        name=recipient_name,
                        entity_type="individual",
                        nationality=message_data.get('recipient_country', 'CA')
                    )
                )
            )
            
            # Calculate overall risk
            overall_risk = max(
                sender_screening['overall_risk_score'],
                recipient_screening['overall_risk_score']
            )
            
            # Determine decision
            if overall_risk >= 0.9:
                decision = "BLOCK"
                emoji = "🚫"
            elif overall_risk >= 0.7:
                decision = "REVIEW"
                emoji = "⚠️"
            else:
                decision = "APPROVE"
                emoji = "✅"
            
            print(f"  {emoji} Decision: {decision} (Risk: {overall_risk:.3f})")
            print(f"     Sender Risk: {sender_screening['overall_risk_score']:.3f}")
            print(f"     Recipient Risk: {recipient_screening['overall_risk_score']:.3f}")
            
        except Exception as e:
            print(f"  ❌ Error processing payment {payment_id}: {str(e)}")
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.consumer:
            self.consumer.close()
        
        if self.screening_service:
            await self.screening_service.cleanup()

async def main():
    """Main function."""
    consumer = KafkaConsumerTest()
    
    try:
        await consumer.initialize()
        await consumer.process_messages(timeout_seconds=45)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await consumer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

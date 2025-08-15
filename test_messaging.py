#!/usr/bin/env python3
"""
Test script for messaging functionality.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""
import asyncio
import json
import time
from datetime import datetime
from app.models.schemas import PaymentMessage, PaymentType
from app.services.messaging.mq_service import mq_service
from app.services.messaging.kafka_service import kafka_service
from app.core.config import settings

async def test_mq_publishing():
    """Test MQ message publishing."""
    print("Testing MQ message publishing...")
    
    try:
        await mq_service.connect()
        
        # Create a test payment message
        payment = PaymentMessage(
            payment_id=f"test_payment_{int(time.time())}",
            transaction_id=f"txn_{int(time.time())}",
            sender_name="John Doe",
            sender_account="1234567890",
            sender_bank="TESTBANK",
            sender_country="US",
            recipient_name="Jane Smith",
            recipient_account="0987654321",
            recipient_bank="RECIPIENTBANK",
            recipient_country="CA",
            amount=1000.00,
            currency="USD",
            payment_type=PaymentType.WIRE_TRANSFER
        )
        
        # Publish to MQ
        await mq_service.publish_message(
            payment,
            routing_key="payment.wire_transfer"
        )
        
        print("✓ MQ message published successfully")
        
    except Exception as e:
        print(f"✗ MQ publishing failed: {str(e)}")
    finally:
        await mq_service.disconnect()

async def test_kafka_publishing():
    """Test Kafka message publishing."""
    print("Testing Kafka message publishing...")
    
    try:
        await kafka_service.connect_producer()
        
        # Create a test payment message
        payment = PaymentMessage(
            payment_id=f"test_kafka_payment_{int(time.time())}",
            transaction_id=f"kafka_txn_{int(time.time())}",
            sender_name="Alice Johnson",
            sender_account="1111111111",
            sender_bank="KAFKABANK",
            sender_country="UK",
            recipient_name="Bob Wilson",
            recipient_account="2222222222",
            recipient_bank="DESTBANK",
            recipient_country="DE",
            amount=500.00,
            currency="EUR",
            payment_type=PaymentType.SEPA
        )
        
        # Publish to Kafka
        await kafka_service.publish_message(
            settings.kafka_payment_topic,
            payment,
            key=payment.payment_id
        )
        
        print("✓ Kafka message published successfully")
        
    except Exception as e:
        print(f"✗ Kafka publishing failed: {str(e)}")
    finally:
        await kafka_service.disconnect()

async def test_message_consumption():
    """Test message consumption."""
    print("Testing message consumption...")
    
    received_messages = []
    
    async def message_handler(payment: PaymentMessage):
        """Handle received payment messages."""
        received_messages.append(payment)
        print(f"Received payment: {payment.payment_id} - {payment.sender_name} -> {payment.recipient_name}")
    
    try:
        # Test MQ consumption
        await mq_service.connect()
        await mq_service.declare_queue("test_consumption_queue", "payment.*")
        await mq_service.start_consumer("test_consumption_queue", message_handler)
        
        # Test Kafka consumption
        await kafka_service.connect_consumer(
            settings.kafka_payment_topic,
            "test-consumer-group"
        )
        await kafka_service.start_consumer(
            settings.kafka_payment_topic,
            message_handler
        )
        
        # Wait for messages
        print("Waiting for messages (30 seconds)...")
        await asyncio.sleep(30)
        
        print(f"✓ Received {len(received_messages)} messages")
        
    except Exception as e:
        print(f"✗ Message consumption failed: {str(e)}")
    finally:
        await mq_service.disconnect()
        await kafka_service.disconnect()

async def main():
    """Main test function."""
    print("Starting messaging tests...")
    print("=" * 50)
    
    # Test MQ publishing
    await test_mq_publishing()
    print()
    
    # Test Kafka publishing
    await test_kafka_publishing()
    print()
    
    # Test message consumption
    await test_message_consumption()
    print()
    
    print("Messaging tests completed!")

if __name__ == "__main__":
    asyncio.run(main())

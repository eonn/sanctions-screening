#!/usr/bin/env python3
"""
Simple Kafka producer for testing payment message streaming.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""
import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from app.models.schemas import PaymentMessage, PaymentType

def create_test_payment(payment_id: str) -> PaymentMessage:
    """Create a test payment message."""
    senders = ["John Doe", "Jane Smith", "Bob Wilson", "Alice Johnson", "Carlos Rodriguez"]
    recipients = ["Sarah Johnson", "Mike Brown", "Lisa Davis", "David Miller", "Emma Wilson"]
    
    return PaymentMessage(
        payment_id=payment_id,
        transaction_id=f"TXN_{payment_id}",
        sender_name=random.choice(senders),
        sender_account=f"ACC_{random.randint(100000, 999999)}",
        sender_bank="TESTBANK",
        sender_country="US",
        recipient_name=random.choice(recipients),
        recipient_account=f"ACC_{random.randint(100000, 999999)}",
        recipient_bank="RECIPIENTBANK",
        recipient_country="CA",
        amount=random.uniform(100, 10000),
        currency="USD",
        payment_type=random.choice(list(PaymentType)),
        timestamp=datetime.utcnow(),
        metadata={"test": True, "timestamp": time.time()}
    )

def main():
    """Main function to produce test messages."""
    print("🚀 Starting Kafka Producer Test")
    
    # Initialize producer
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )
    
    topic = 'payment_messages'
    
    try:
        for i in range(10):
            # Create payment message
            payment_id = f"PAY_KAFKA_{i+1:03d}"
            payment = create_test_payment(payment_id)
            
            # Convert to dict
            message_data = payment.model_dump()
            message_data['timestamp'] = message_data['timestamp'].isoformat()
            
            # Send to Kafka
            future = producer.send(topic, value=message_data, key=payment_id)
            record_metadata = future.get(timeout=10)
            
            print(f"✅ Sent payment {payment_id}: {payment.sender_name} → {payment.recipient_name} (${payment.amount:.2f})")
            print(f"   Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
            
            time.sleep(1)  # Wait 1 second between messages
        
        # Flush to ensure all messages are sent
        producer.flush()
        print(f"\n🎉 Successfully sent 10 payment messages to Kafka topic: {topic}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        producer.close()

if __name__ == "__main__":
    main()

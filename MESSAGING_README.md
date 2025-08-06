# Real-Time Payment Screening with MQ and Kafka Integration

This document describes the real-time payment screening capabilities added to the Sanctions Screening Platform using Message Queue (MQ) and Kafka integration.

## Overview

The platform now supports real-time payment screening through:
- **RabbitMQ**: For reliable message queuing and routing
- **Apache Kafka**: For high-throughput streaming of payment messages
- **Payment Screening Service**: For processing payment messages and performing sanctions screening

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Payment       │    │   RabbitMQ      │    │   Kafka         │
│   Systems       │───▶│   (MQ)          │───▶│   (Streaming)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────────────────────────────┐
                       │     Payment Screening Service           │
                       │                                         │
                       │  • MQ Consumer                          │
                       │  • Kafka Consumer                       │
                       │  • Entity Screening                     │
                       │  • Risk Assessment                      │
                       │  • Decision Engine                      │
                       └─────────────────────────────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Results       │    │   Database      │
                       │   Queue/Topic   │    │   Storage       │
                       └─────────────────┘    └─────────────────┘
```

## Features

### 1. Message Queue (RabbitMQ) Integration
- **Reliable Message Delivery**: Ensures no payment messages are lost
- **Message Routing**: Routes messages based on payment type and priority
- **Dead Letter Queues**: Handles failed message processing
- **Message Persistence**: Survives broker restarts

### 2. Kafka Streaming Integration
- **High Throughput**: Handles thousands of payment messages per second
- **Event Streaming**: Maintains order and provides replay capabilities
- **Scalability**: Supports horizontal scaling
- **Fault Tolerance**: Replicates messages across brokers

### 3. Real-Time Payment Screening
- **Dual Entity Screening**: Screens both sender and recipient
- **Risk Scoring**: Calculates overall risk based on multiple factors
- **Decision Engine**: Automatically approves, flags for review, or blocks payments
- **Performance Monitoring**: Tracks processing times and statistics

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# RabbitMQ Configuration
MQ_HOST=localhost
MQ_PORT=5672
MQ_USERNAME=guest
MQ_PASSWORD=guest
MQ_VIRTUAL_HOST=/
MQ_EXCHANGE_NAME=sanctions_screening
MQ_PAYMENT_QUEUE=payment_screening
MQ_MESSAGE_TTL=86400000
MQ_MAX_QUEUE_LENGTH=10000

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_PAYMENT_TOPIC=payment_messages
KAFKA_RESULT_TOPIC=screening_results
KAFKA_CONSUMER_GROUP=sanctions-screening-group

# Risk Thresholds
LOW_RISK_THRESHOLD=0.3
MEDIUM_RISK_THRESHOLD=0.7
HIGH_RISK_THRESHOLD=0.9
```

## Setup and Installation

### 1. Start Infrastructure Services

```bash
# Start RabbitMQ and Kafka
docker-compose -f docker-compose.messaging.yml up -d

# Verify services are running
docker-compose -f docker-compose.messaging.yml ps
```

### 2. Install Dependencies

```bash
# Install new messaging dependencies
pip install -r requirements.txt
```

### 3. Start the Application

```bash
# Start the sanctions screening platform
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Payment Screening

#### POST `/api/v1/payment/screen`
Screen a payment message for sanctions compliance.

**Request Body:**
```json
{
  "payment_id": "payment_123",
  "transaction_id": "txn_456",
  "sender_name": "John Doe",
  "sender_account": "1234567890",
  "sender_bank": "TESTBANK",
  "sender_country": "US",
  "recipient_name": "Jane Smith",
  "recipient_account": "0987654321",
  "recipient_bank": "RECIPIENTBANK",
  "recipient_country": "CA",
  "amount": 1000.00,
  "currency": "USD",
  "payment_type": "wire_transfer"
}
```

**Response:**
```json
{
  "payment_id": "payment_123",
  "transaction_id": "txn_456",
  "screening_id": 1234567890,
  "overall_risk_score": 0.15,
  "decision": "clear",
  "status": "approved",
  "processing_time_ms": 150,
  "metadata": {
    "payment_type": "wire_transfer",
    "amount": 1000.00,
    "currency": "USD"
  }
}
```

#### GET `/api/v1/payment/stats`
Get payment screening statistics.

**Response:**
```json
{
  "total_processed": 1250,
  "approved": 1100,
  "rejected": 100,
  "blocked": 50,
  "errors": 0,
  "avg_processing_time_ms": 145,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET `/api/v1/messaging/status`
Get messaging services status.

**Response:**
```json
{
  "mq_connected": true,
  "kafka_producer_connected": true,
  "kafka_consumers": 2,
  "active_queues": ["payment_screening"],
  "active_topics": ["payment_messages"]
}
```

## Message Formats

### Payment Message Schema

```python
class PaymentMessage(BaseModel):
    payment_id: str                    # Unique payment identifier
    transaction_id: str                # Transaction identifier
    sender_name: str                   # Sender entity name
    sender_account: str                # Sender account number
    sender_bank: Optional[str]         # Sender bank code
    sender_country: Optional[str]      # Sender country code
    recipient_name: str                # Recipient entity name
    recipient_account: str             # Recipient account number
    recipient_bank: Optional[str]      # Recipient bank code
    recipient_country: Optional[str]   # Recipient country code
    amount: float                      # Payment amount
    currency: str                      # Currency code (3 chars)
    payment_type: PaymentType          # Type of payment
    timestamp: datetime                # Payment timestamp
    metadata: Optional[Dict[str, Any]] # Additional metadata
```

### Payment Types

- `wire_transfer`: Wire transfers
- `ach`: Automated Clearing House
- `swift`: SWIFT transfers
- `sepa`: SEPA transfers
- `card_payment`: Card payments
- `crypto`: Cryptocurrency transfers

## Testing

### Test Messaging Functionality

```bash
# Run the messaging test script
python test_messaging.py
```

### Manual Testing

1. **Start the infrastructure:**
   ```bash
   docker-compose -f docker-compose.messaging.yml up -d
   ```

2. **Start the application:**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

3. **Send a test payment:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/payment/screen" \
        -H "Content-Type: application/json" \
        -d '{
          "payment_id": "test_001",
          "transaction_id": "txn_001",
          "sender_name": "Test Sender",
          "sender_account": "1234567890",
          "recipient_name": "Test Recipient",
          "recipient_account": "0987654321",
          "amount": 100.00,
          "currency": "USD",
          "payment_type": "wire_transfer"
        }'
   ```

4. **Check statistics:**
   ```bash
   curl "http://localhost:8000/api/v1/payment/stats"
   ```

## Monitoring

### RabbitMQ Management UI
- URL: http://localhost:15672
- Username: guest
- Password: guest

### Kafka UI
- URL: http://localhost:8080

### Application Metrics
- Health check: `GET /health`
- Messaging status: `GET /api/v1/messaging/status`
- Payment stats: `GET /api/v1/payment/stats`

## Production Considerations

### 1. Security
- Use strong passwords for MQ and Kafka
- Enable SSL/TLS encryption
- Implement proper authentication and authorization
- Use dedicated service accounts

### 2. Performance
- Configure appropriate queue sizes and TTL
- Set up monitoring and alerting
- Implement circuit breakers for external services
- Use connection pooling

### 3. Reliability
- Set up message persistence
- Configure dead letter queues
- Implement retry mechanisms
- Use message acknowledgments

### 4. Scalability
- Use multiple Kafka brokers
- Implement consumer groups
- Set up load balancing
- Monitor resource usage

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify infrastructure services are running
   - Check network connectivity
   - Validate configuration settings

2. **Message Processing Errors**
   - Check application logs
   - Verify message format
   - Monitor queue/topic health

3. **Performance Issues**
   - Monitor processing times
   - Check resource usage
   - Review configuration settings

### Logs

Check application logs for detailed error information:
```bash
# Application logs
tail -f logs/app.log

# Docker logs
docker-compose -f docker-compose.messaging.yml logs -f
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Verify configuration settings
4. Test with the provided test scripts

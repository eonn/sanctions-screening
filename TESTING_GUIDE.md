# Complete Testing Guide for Sanctions Screening Platform with Kafka

## 🎯 **Overview**

This guide will walk you through testing the complete sanctions screening platform with Kafka streaming functionality. You'll learn how to start the infrastructure, run the application, and test real-time payment screening.

## 📋 **Prerequisites**

Before starting, ensure you have:
- Docker installed and running
- Python 3.8+ installed
- Git (to clone the repository)

## 🚀 **Step 1: Environment Setup**

### 1.1 Start Docker
```bash
# Start Docker daemon
sudo systemctl start docker
# OR if using snap
sudo snap start docker

# Verify Docker is running
docker --version
docker ps
```

### 1.2 Navigate to Project Directory
```bash
cd /home/eon/projects/sanctions-screening-platform
```

### 1.3 Activate Virtual Environment
```bash
source venv/bin/activate
```

## 🏗️ **Step 2: Start Infrastructure Services**

### 2.1 Start Kafka and RabbitMQ
```bash
# Start all messaging infrastructure
docker-compose -f docker-compose.messaging.yml up -d

# Verify services are running
docker-compose -f docker-compose.messaging.yml ps
```

### 2.2 Check Service Health
```bash
# Check if all services are healthy
docker-compose -f docker-compose.messaging.yml ps | grep "healthy"
```

**Expected Output**: You should see all services (zookeeper, kafka, rabbitmq) showing as "healthy"

## 🐍 **Step 3: Install Dependencies**

### 3.1 Install Required Packages
```bash
# Install Kafka dependencies
pip install kafka-python aiokafka

# Install other dependencies (if not already installed)
pip install fastapi uvicorn pydantic python-multipart sqlalchemy redis python-dotenv
```

## 🚀 **Step 4: Start the Application**

### 4.1 Start the Sanctions Screening Platform
```bash
# Start the application
python -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output**: You should see the application start with messages like:
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:app.main_simple:Starting Sanctions Screening Platform...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🧪 **Step 5: Test Basic Functionality**

### 5.1 Test Health Check
Open a new terminal and run:
```bash
curl http://localhost:8000/health
```

**Expected Output**:
```json
{"status":"healthy","service":"sanctions-screening-platform"}
```

### 5.2 Test Payment Screening API
```bash
curl -X POST "http://localhost:8000/api/v1/payment/screen" \
     -H "Content-Type: application/json" \
     -d '{
       "payment_id": "test_001",
       "transaction_id": "txn_001",
       "sender_name": "John Doe",
       "sender_account": "1234567890",
       "recipient_name": "Jane Smith",
       "recipient_account": "0987654321",
       "amount": 1000.00,
       "currency": "USD",
       "payment_type": "wire_transfer"
     }'
```

**Expected Output**: JSON response with screening results

## 📊 **Step 6: Test Kafka Streaming**

### 6.1 Run Kafka Producer Test
Open a new terminal and run:
```bash
# Navigate to project directory
cd /home/eon/projects/sanctions-screening-platform
source venv/bin/activate

# Run the producer test
python kafka_producer_test.py
```

**Expected Output**: You should see messages like:
```
🚀 Starting Kafka Producer Test
✅ Sent payment PAY_KAFKA_001: John Doe → Sarah Johnson ($1234.56)
   Topic: payment_messages, Partition: 0, Offset: 0
...
🎉 Successfully sent 10 payment messages to Kafka topic: payment_messages
```

### 6.2 Run Kafka Consumer Test
In another terminal, run:
```bash
# Navigate to project directory
cd /home/eon/projects/sanctions-screening-platform
source venv/bin/activate

# Run the consumer test
python kafka_consumer_test.py
```

**Expected Output**: You should see real-time processing of payment messages:
```
🚀 Initializing Kafka Consumer Test
✅ Consumer initialized successfully
📥 Starting to consume messages (timeout: 45s)...
📨 Processing payment: PAY_KAFKA_001
   Topic: payment_messages, Partition: 0, Offset: 0
  🔍 Screening: John Doe → Sarah Johnson ($1234.56)
  ✅ Decision: APPROVE (Risk: 0.000)
     Sender Risk: 0.000
     Recipient Risk: 0.000
```

## 🎯 **Step 7: Test Different Scenarios**

### 7.1 Test Low-Risk Payment
```bash
curl -X POST "http://localhost:8000/api/v1/payment/screen" \
     -H "Content-Type: application/json" \
     -d '{
       "payment_id": "low_risk_001",
       "transaction_id": "txn_low_001",
       "sender_name": "Alice Johnson",
       "sender_account": "1111111111",
       "recipient_name": "Bob Wilson",
       "recipient_account": "2222222222",
       "amount": 500.00,
       "currency": "USD",
       "payment_type": "wire_transfer"
     }'
```

### 7.2 Test High-Risk Payment
```bash
curl -X POST "http://localhost:8000/api/v1/payment/screen" \
     -H "Content-Type: application/json" \
     -d '{
       "payment_id": "high_risk_001",
       "transaction_id": "txn_high_001",
       "sender_name": "John Doe",
       "sender_account": "3333333333",
       "recipient_name": "Osama Bin Laden",
       "recipient_account": "4444444444",
       "amount": 5000.00,
       "currency": "USD",
       "payment_type": "wire_transfer"
     }'
```

**Expected Output**: This should show a BLOCKED decision with high risk score.

## 🌐 **Step 8: Access Monitoring Interfaces**

### 8.1 Kafka UI
Open your web browser and go to:
```
http://localhost:8080
```

You can:
- View topics and messages
- Monitor consumer groups
- Browse message content
- Check cluster health

### 8.2 RabbitMQ Management
Open your web browser and go to:
```
http://localhost:15672
```

Login with:
- Username: `guest`
- Password: `guest`

You can:
- Monitor queues
- Check message rates
- View connections
- Manage exchanges

## 🔧 **Step 9: Advanced Testing**

### 9.1 Run Comprehensive Streaming Test
```bash
python test_kafka_streaming.py
```

This will:
- Produce 15 payment messages
- Consume and process them in real-time
- Show detailed screening results
- Display statistics

### 9.2 Test Payment Screening with Different Names
```bash
python test_sanctioned_payment.py
```

This will test various scenarios including:
- Normal names (low risk)
- Common names (medium risk)
- High-risk names (blocked)

## 🐛 **Troubleshooting**

### Common Issues and Solutions

#### Issue 1: Docker Permission Denied
```bash
# Fix Docker permissions
sudo chmod 666 /var/run/docker.sock
```

#### Issue 2: Python Command Not Found
```bash
# Use python3 instead of python
python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000
```

#### Issue 3: Kafka Connection Failed
```bash
# Check if Kafka is running
docker-compose -f docker-compose.messaging.yml ps

# Restart Kafka if needed
docker-compose -f docker-compose.messaging.yml restart kafka
```

#### Issue 4: Application Won't Start
```bash
# Check if virtual environment is activated
source venv/bin/activate

# Install missing dependencies
pip install -r requirements.txt
```

## 📊 **Expected Test Results**

### Successful Test Indicators

1. **Infrastructure**: All Docker containers showing "healthy"
2. **Application**: FastAPI server running on port 8000
3. **Health Check**: Returns `{"status":"healthy"}`
4. **Kafka Producer**: Successfully sends messages
5. **Kafka Consumer**: Real-time processing of messages
6. **Screening**: Risk scores and decisions generated
7. **UI Access**: Kafka UI and RabbitMQ management accessible

### Sample Output Patterns

#### Low-Risk Payment
```json
{
  "payment_id": "test_001",
  "overall_risk_score": 0.0,
  "decision": "clear",
  "status": "approved"
}
```

#### High-Risk Payment
```json
{
  "payment_id": "high_risk_001", 
  "overall_risk_score": 1.0,
  "decision": "block",
  "status": "blocked"
}
```

## 🎉 **Success Criteria**

You've successfully tested the platform when:

✅ All Docker services are running and healthy  
✅ Application starts without errors  
✅ Health check returns healthy status  
✅ Payment screening API responds with results  
✅ Kafka producer sends messages successfully  
✅ Kafka consumer processes messages in real-time  
✅ Risk assessment generates appropriate scores  
✅ Decision engine makes correct approve/block decisions  
✅ Monitoring UIs are accessible  

## 🚀 **Next Steps**

Once testing is complete, you can:

1. **Scale the system**: Add more Kafka partitions
2. **Add monitoring**: Set up Prometheus/Grafana
3. **Implement alerts**: Configure risk threshold alerts
4. **Add more data sources**: Integrate additional sanctions lists
5. **Performance testing**: Load test with high message volumes

## 📞 **Support**

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are met
3. Check Docker and service logs
4. Ensure virtual environment is activated
5. Verify all dependencies are installed

Happy testing! 🎯

# Testing Checklist for Sanctions Screening Platform

## ✅ **Pre-Testing Checklist**

- [ ] Docker is installed and running
- [ ] Python 3.8+ is installed
- [ ] You're in the project directory: `/home/eon/projects/sanctions-screening-platform`
- [ ] Virtual environment is available

## 🚀 **Step-by-Step Testing Guide**

### **Step 1: Start Infrastructure**
```bash
# Start Kafka and RabbitMQ
docker-compose -f docker-compose.messaging.yml up -d

# Wait 30 seconds for services to be ready
sleep 30

# Check if services are healthy
docker-compose -f docker-compose.messaging.yml ps
```

**Expected**: All services should show "healthy" status

### **Step 2: Activate Environment**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install kafka-python aiokafka requests
```

### **Step 3: Start Application**
```bash
# Start the application
python -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload
```

**Expected**: Application starts with "Uvicorn running on http://0.0.0.0:8000"

### **Step 4: Run Verification Script**
```bash
# In a new terminal, run the verification script
python verify_setup.py
```

**Expected**: All tests should pass

### **Step 5: Test Basic API**
```bash
# Test health check
curl http://localhost:8000/health

# Test payment screening
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

### **Step 6: Test Kafka Streaming**
```bash
# Test Kafka producer
python kafka_producer_test.py

# Test Kafka consumer (in another terminal)
python kafka_consumer_test.py
```

### **Step 7: Access Web Interfaces**
- **Kafka UI**: http://localhost:8080
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 🎯 **Success Indicators**

- [ ] All Docker services are healthy
- [ ] Application starts without errors
- [ ] Health check returns `{"status":"healthy"}`
- [ ] Payment screening API responds with results
- [ ] Kafka producer sends messages successfully
- [ ] Kafka consumer processes messages in real-time
- [ ] Web UIs are accessible
- [ ] Risk assessment generates appropriate scores
- [ ] Decision engine makes correct decisions

## 🐛 **Common Issues & Solutions**

### Issue: Docker Permission Denied
```bash
sudo chmod 666 /var/run/docker.sock
```

### Issue: Python Command Not Found
```bash
# Use python3 instead
python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000
```

### Issue: Services Not Healthy
```bash
# Restart services
docker-compose -f docker-compose.messaging.yml down
docker-compose -f docker-compose.messaging.yml up -d
```

### Issue: Application Won't Start
```bash
# Check virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 📞 **Getting Help**

If you encounter issues:
1. Check the troubleshooting section
2. Verify all prerequisites are met
3. Check Docker logs: `docker-compose -f docker-compose.messaging.yml logs`
4. Ensure virtual environment is activated
5. Verify all dependencies are installed

## 🎉 **Completion**

Once all tests pass, your sanctions screening platform with Kafka streaming is ready for use!

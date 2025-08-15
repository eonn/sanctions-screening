#!/bin/bash

# Quick Test Script for Sanctions Screening Platform with Kafka
# This script will help you test the complete setup
# Author: Eon (Himanshu Shekhar)
# Email: himanshu.shekhar@example.com
# GitHub: https://github.com/eon-himanshu
# Created: 2024

echo "🎯 SANCTIONS SCREENING PLATFORM - QUICK TEST SCRIPT"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Check Docker
print_status "Step 1: Checking Docker..."
if ! docker --version > /dev/null 2>&1; then
    print_error "Docker is not installed or not running"
    echo "Please install Docker and start it first"
    exit 1
fi
print_success "Docker is available"

# Step 2: Start Infrastructure
print_status "Step 2: Starting Kafka and RabbitMQ infrastructure..."
if docker-compose -f docker-compose.messaging.yml up -d > /dev/null 2>&1; then
    print_success "Infrastructure services started"
else
    print_error "Failed to start infrastructure services"
    exit 1
fi

# Step 3: Wait for services to be ready
print_status "Step 3: Waiting for services to be ready..."
sleep 30

# Step 4: Check service health
print_status "Step 4: Checking service health..."
if docker-compose -f docker-compose.messaging.yml ps | grep -q "healthy"; then
    print_success "All services are healthy"
else
    print_warning "Some services may not be fully ready yet"
fi

# Step 5: Activate virtual environment
print_status "Step 5: Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    print_success "Virtual environment activated"
else
    print_error "Virtual environment not found"
    echo "Please create a virtual environment first: python3 -m venv venv"
    exit 1
fi

# Step 6: Install dependencies
print_status "Step 6: Installing dependencies..."
pip install kafka-python aiokafka fastapi uvicorn pydantic python-multipart sqlalchemy redis python-dotenv > /dev/null 2>&1
print_success "Dependencies installed"

# Step 7: Test health check
print_status "Step 7: Testing application health..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Application is running and healthy"
else
    print_warning "Application may not be running yet"
    echo "You can start it with: python -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000"
fi

# Step 8: Display access information
echo ""
echo "🌐 ACCESS INFORMATION"
echo "===================="
echo "Kafka UI: http://localhost:8080"
echo "RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo "Application Health: http://localhost:8000/health"
echo "Payment Screening API: http://localhost:8000/api/v1/payment/screen"
echo ""

# Step 9: Provide testing commands
echo "🧪 TESTING COMMANDS"
echo "=================="
echo "1. Test basic payment screening:"
echo "   curl -X POST \"http://localhost:8000/api/v1/payment/screen\" \\"
echo "        -H \"Content-Type: application/json\" \\"
echo "        -d '{\"payment_id\":\"test_001\",\"transaction_id\":\"txn_001\",\"sender_name\":\"John Doe\",\"sender_account\":\"1234567890\",\"recipient_name\":\"Jane Smith\",\"recipient_account\":\"0987654321\",\"amount\":1000.00,\"currency\":\"USD\",\"payment_type\":\"wire_transfer\"}'"
echo ""
echo "2. Test Kafka producer:"
echo "   python kafka_producer_test.py"
echo ""
echo "3. Test Kafka consumer:"
echo "   python kafka_consumer_test.py"
echo ""
echo "4. Run comprehensive test:"
echo "   python test_kafka_streaming.py"
echo ""

print_success "Quick test setup completed!"
echo "You can now run the testing commands above to verify the system."

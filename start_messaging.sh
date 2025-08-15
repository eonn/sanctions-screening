#!/bin/bash

# Start script for the Sanctions Screening Platform with Messaging
# Author: Eon (Himanshu Shekhar)
# Email: eonhimanshu@gmail.com
# GitHub: https://github.com/eonn/sanctions-screening
# Created: 2024

echo "Starting Sanctions Screening Platform with MQ and Kafka integration..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start infrastructure services
echo "Starting infrastructure services (RabbitMQ, Kafka, Zookeeper)..."
docker-compose -f docker-compose.messaging.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Check if services are healthy
echo "Checking service health..."
if ! docker-compose -f docker-compose.messaging.yml ps | grep -q "healthy"; then
    echo "Warning: Some services may not be fully ready yet."
fi

# Install dependencies if needed
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start the application
echo "Starting the Sanctions Screening Platform..."
echo "Application will be available at: http://localhost:8000"
echo "RabbitMQ Management UI: http://localhost:15672 (guest/guest)"
echo "Kafka UI: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the application"

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

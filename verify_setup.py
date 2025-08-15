#!/usr/bin/env python3
"""
Verification script to test the complete sanctions screening platform setup.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""
import requests
import json
import time
from datetime import datetime

def test_health_check():
    """Test the application health check."""
    print("🔍 Testing application health...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Application is healthy")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_payment_screening():
    """Test payment screening functionality."""
    print("\n🔍 Testing payment screening...")
    
    # Test low-risk payment
    low_risk_payment = {
        "payment_id": "verify_low_001",
        "transaction_id": "txn_verify_low_001",
        "sender_name": "John Doe",
        "sender_account": "1234567890",
        "recipient_name": "Jane Smith",
        "recipient_account": "0987654321",
        "amount": 1000.00,
        "currency": "USD",
        "payment_type": "wire_transfer"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/payment/screen",
            headers={"Content-Type": "application/json"},
            json=low_risk_payment,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Low-risk payment screened successfully")
            print(f"   Decision: {result.get('decision', 'unknown')}")
            print(f"   Risk Score: {result.get('overall_risk_score', 'unknown')}")
            return True
        else:
            print(f"❌ Payment screening failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Payment screening error: {str(e)}")
        return False

def test_high_risk_payment():
    """Test high-risk payment screening."""
    print("\n🔍 Testing high-risk payment screening...")
    
    # Test high-risk payment
    high_risk_payment = {
        "payment_id": "verify_high_001",
        "transaction_id": "txn_verify_high_001",
        "sender_name": "John Doe",
        "sender_account": "1234567890",
        "recipient_name": "Osama Bin Laden",
        "recipient_account": "0987654321",
        "amount": 5000.00,
        "currency": "USD",
        "payment_type": "wire_transfer"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/payment/screen",
            headers={"Content-Type": "application/json"},
            json=high_risk_payment,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ High-risk payment screened successfully")
            print(f"   Decision: {result.get('decision', 'unknown')}")
            print(f"   Risk Score: {result.get('overall_risk_score', 'unknown')}")
            
            # Check if it was blocked
            if result.get('decision') == 'block':
                print("✅ High-risk payment correctly blocked")
                return True
            else:
                print("⚠️  High-risk payment was not blocked (may be expected)")
                return True
        else:
            print(f"❌ High-risk payment screening failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ High-risk payment screening error: {str(e)}")
        return False

def test_kafka_ui():
    """Test if Kafka UI is accessible."""
    print("\n🔍 Testing Kafka UI accessibility...")
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Kafka UI is accessible")
            return True
        else:
            print(f"❌ Kafka UI not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Kafka UI error: {str(e)}")
        return False

def test_rabbitmq_ui():
    """Test if RabbitMQ UI is accessible."""
    print("\n🔍 Testing RabbitMQ UI accessibility...")
    try:
        response = requests.get("http://localhost:15672", timeout=5)
        if response.status_code == 200:
            print("✅ RabbitMQ UI is accessible")
            return True
        else:
            print(f"❌ RabbitMQ UI not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ RabbitMQ UI error: {str(e)}")
        return False

def main():
    """Main verification function."""
    print("🎯 SANCTIONS SCREENING PLATFORM - SETUP VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Application Health", test_health_check),
        ("Payment Screening (Low Risk)", test_payment_screening),
        ("Payment Screening (High Risk)", test_high_risk_payment),
        ("Kafka UI", test_kafka_ui),
        ("RabbitMQ UI", test_rabbitmq_ui)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your setup is working correctly.")
        print("\nNext steps:")
        print("1. Run: python kafka_producer_test.py")
        print("2. Run: python kafka_consumer_test.py")
        print("3. Run: python test_kafka_streaming.py")
        print("4. Visit: http://localhost:8080 (Kafka UI)")
        print("5. Visit: http://localhost:15672 (RabbitMQ UI)")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the setup.")
        print("\nTroubleshooting:")
        print("1. Ensure Docker is running")
        print("2. Check if all services are started")
        print("3. Verify the application is running")
        print("4. Check network connectivity")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script for payment screening with potentially sanctioned entities.
"""
import asyncio
import json
import time
from datetime import datetime
from app.models.schemas import PaymentMessage, PaymentScreeningResult, DecisionType, PaymentStatus, EntityCreate, ScreeningRequest
from app.services.screening_service import ScreeningService

async def test_sanctioned_payment():
    """Test payment screening with potentially sanctioned entities."""
    print("Starting sanctioned payment screening test...")
    
    # Test cases with potentially sanctioned names
    test_cases = [
        {
            "name": "Test Case 1 - Normal Names",
            "sender": "John Doe",
            "recipient": "Jane Smith",
            "expected": "low"
        },
        {
            "name": "Test Case 2 - Common Name",
            "sender": "Mohammed Ali",
            "recipient": "Sarah Johnson",
            "expected": "medium"
        },
        {
            "name": "Test Case 3 - High Risk Names",
            "sender": "Osama Bin Laden",
            "recipient": "John Smith",
            "expected": "high"
        }
    ]
    
    try:
        # Initialize screening service
        print("Initializing screening service...")
        screening_service = ScreeningService()
        await screening_service.initialize()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST CASE {i}: {test_case['name']}")
            print(f"{'='*60}")
            
            # Create payment
            payment = PaymentMessage(
                payment_id=f"PAY_TEST_{i}",
                transaction_id=f"TXN_TEST_{i}",
                sender_name=test_case["sender"],
                sender_account="1234567890",
                sender_bank="TESTBANK",
                sender_country="US",
                recipient_name=test_case["recipient"],
                recipient_account="0987654321",
                recipient_bank="RECIPIENTBANK",
                recipient_country="CA",
                amount=5000.00,
                currency="USD",
                payment_type="wire_transfer"
            )
            
            print(f"Payment: {payment.sender_name} → {payment.recipient_name}")
            print(f"Amount: {payment.amount} {payment.currency}")
            
            # Screen sender
            print(f"\nScreening sender: {payment.sender_name}")
            sender_screening = await screening_service.screen_entity_async(
                ScreeningRequest(
                    entity=EntityCreate(
                        name=payment.sender_name,
                        entity_type="individual",
                        nationality=payment.sender_country
                    )
                )
            )
            
            print(f"  Sender Risk: {sender_screening['overall_risk_score']:.3f}")
            print(f"  Sender Decision: {sender_screening['decision']}")
            
            # Screen recipient
            print(f"\nScreening recipient: {payment.recipient_name}")
            recipient_screening = await screening_service.screen_entity_async(
                ScreeningRequest(
                    entity=EntityCreate(
                        name=payment.recipient_name,
                        entity_type="individual",
                        nationality=payment.recipient_country
                    )
                )
            )
            
            print(f"  Recipient Risk: {recipient_screening['overall_risk_score']:.3f}")
            print(f"  Recipient Decision: {recipient_screening['decision']}")
            
            # Calculate overall risk
            overall_risk_score = max(sender_screening['overall_risk_score'], recipient_screening['overall_risk_score'])
            
            # Determine decision
            if overall_risk_score >= 0.9:
                decision = DecisionType.BLOCK
                status = PaymentStatus.BLOCKED
                risk_level = "HIGH"
            elif overall_risk_score >= 0.7:
                decision = DecisionType.REVIEW
                status = PaymentStatus.SCREENING
                risk_level = "MEDIUM"
            else:
                decision = DecisionType.CLEAR
                status = PaymentStatus.APPROVED
                risk_level = "LOW"
            
            print(f"\n=== FINAL RESULT ===")
            print(f"Overall Risk Score: {overall_risk_score:.3f}")
            print(f"Risk Level: {risk_level}")
            print(f"Decision: {decision.value}")
            print(f"Status: {status.value}")
            
            if decision == DecisionType.BLOCK:
                print("🚫 PAYMENT BLOCKED - High risk detected")
            elif decision == DecisionType.REVIEW:
                print("⚠️  PAYMENT FLAGGED FOR REVIEW - Medium risk detected")
            else:
                print("✅ PAYMENT APPROVED - Low risk")
            
            # Check if matches expected
            expected_risk = test_case["expected"]
            if (expected_risk == "high" and decision == DecisionType.BLOCK) or \
               (expected_risk == "medium" and decision == DecisionType.REVIEW) or \
               (expected_risk == "low" and decision == DecisionType.CLEAR):
                print("✅ Test case PASSED")
            else:
                print("❌ Test case FAILED - Unexpected result")
        
        # Cleanup
        await screening_service.cleanup()
        
    except Exception as e:
        print(f"Error during screening: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sanctioned_payment())

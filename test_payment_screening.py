#!/usr/bin/env python3
"""
Simple test script for payment screening functionality.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""
import asyncio
import json
import time
from datetime import datetime
from app.models.schemas import PaymentMessage, PaymentScreeningResult, DecisionType, PaymentStatus, EntityCreate, ScreeningRequest
from app.services.screening_service import ScreeningService

async def test_payment_screening():
    """Test payment screening functionality."""
    print("Starting payment screening test...")
    
    # Create a sample payment
    payment = PaymentMessage(
        payment_id="PAY_2024_001",
        transaction_id="TXN_2024_001",
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
        payment_type="wire_transfer"
    )
    
    print(f"Payment created: {payment.payment_id}")
    print(f"Sender: {payment.sender_name} ({payment.sender_country})")
    print(f"Recipient: {payment.recipient_name} ({payment.recipient_country})")
    print(f"Amount: {payment.amount} {payment.currency}")
    print()
    
    try:
        # Initialize screening service
        print("Initializing screening service...")
        screening_service = ScreeningService()
        await screening_service.initialize()
        
        # Screen sender
        print("Screening sender...")
        sender_screening = await screening_service.screen_entity_async(
            ScreeningRequest(
                entity=EntityCreate(
                    name=payment.sender_name,
                    entity_type="individual",
                    nationality=payment.sender_country
                )
            )
        )
        
        print(f"Sender screening result: {sender_screening['decision']} (risk: {sender_screening['overall_risk_score']:.3f})")
        
        # Screen recipient
        print("Screening recipient...")
        recipient_screening = await screening_service.screen_entity_async(
            ScreeningRequest(
                entity=EntityCreate(
                    name=payment.recipient_name,
                    entity_type="individual",
                    nationality=payment.recipient_country
                )
            )
        )
        
        print(f"Recipient screening result: {recipient_screening['decision']} (risk: {recipient_screening['overall_risk_score']:.3f})")
        
        # Calculate overall risk
        overall_risk_score = max(sender_screening['overall_risk_score'], recipient_screening['overall_risk_score'])
        
        # Determine decision
        if overall_risk_score >= 0.9:
            decision = DecisionType.BLOCK
            status = PaymentStatus.BLOCKED
        elif overall_risk_score >= 0.7:
            decision = DecisionType.REVIEW
            status = PaymentStatus.SCREENING
        else:
            decision = DecisionType.CLEAR
            status = PaymentStatus.APPROVED
        
        # Create result
        result = PaymentScreeningResult(
            payment_id=payment.payment_id,
            transaction_id=payment.transaction_id,
            screening_id=int(time.time() * 1000),
            sender_screening=sender_screening,
            recipient_screening=recipient_screening,
            overall_risk_score=overall_risk_score,
            decision=decision,
            status=status,
            processing_time_ms=0,
            metadata={
                "payment_type": payment.payment_type,
                "amount": payment.amount,
                "currency": payment.currency
            }
        )
        
        print()
        print("=== PAYMENT SCREENING RESULT ===")
        print(f"Payment ID: {result.payment_id}")
        print(f"Overall Risk Score: {result.overall_risk_score:.3f}")
        print(f"Decision: {result.decision.value}")
        print(f"Status: {result.status.value}")
        print(f"Sender Risk: {sender_screening['overall_risk_score']:.3f}")
        print(f"Recipient Risk: {recipient_screening['overall_risk_score']:.3f}")
        
        if result.decision == DecisionType.BLOCK:
            print("🚫 PAYMENT BLOCKED - High risk detected")
        elif result.decision == DecisionType.REVIEW:
            print("⚠️  PAYMENT FLAGGED FOR REVIEW - Medium risk detected")
        else:
            print("✅ PAYMENT APPROVED - Low risk")
        
        # Cleanup
        await screening_service.cleanup()
        
    except Exception as e:
        print(f"Error during screening: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_payment_screening())

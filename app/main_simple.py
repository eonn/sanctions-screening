"""
Simplified FastAPI application for the Sanctions Screening Platform.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""
import logging
import uuid
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.services.screening_service import ScreeningService
from app.models.schemas import EntityCreate, ScreeningRequest, ScreeningResponse, PaymentMessage, PaymentScreeningResult, DecisionType, PaymentStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
screening_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global screening_service
    
    # Startup
    logger.info("Starting Sanctions Screening Platform...")
    
    # Initialize screening service
    screening_service = ScreeningService()
    await screening_service.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Sanctions Screening Platform...")
    
    if screening_service:
        await screening_service.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Sanctions Screening Platform",
    description="A production-quality platform for screening entities against sanctions lists",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track requests with unique IDs."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.error(f"Request {request_id} failed: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "sanctions-screening-platform"}

@app.post("/api/v1/screen", response_model=ScreeningResponse)
async def screen_entity(request: ScreeningRequest):
    """Screen an entity against sanctions lists."""
    if not screening_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        result = await screening_service.screen_entity_async(request)
        return result
    except Exception as e:
        logger.error(f"Screening failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Screening failed: {str(e)}")

@app.post("/api/v1/payment/screen", response_model=PaymentScreeningResult)
async def screen_payment(payment: PaymentMessage):
    """Screen a payment message for sanctions compliance."""
    if not screening_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        import time
        start_time = time.time()
        
        # Screen both sender and recipient
        sender_screening = await screening_service.screen_entity_async(
            ScreeningRequest(entity=EntityCreate(
                name=payment.sender_name,
                entity_type="individual",
                nationality=payment.sender_country
            )
        )
        
        recipient_screening = await screening_service.screen_entity_async(
            ScreeningRequest(entity=EntityCreate(
                name=payment.recipient_name,
                entity_type="individual", 
                nationality=payment.recipient_country
            )
        )
        
        # Calculate overall risk score
        overall_risk_score = max(
            sender_screening.overall_risk_score,
            recipient_screening.overall_risk_score
        )
        
        # Determine decision based on risk
        if overall_risk_score >= settings.high_risk_threshold:
            decision = DecisionType.BLOCK
            status = PaymentStatus.BLOCKED
        elif overall_risk_score >= settings.medium_risk_threshold:
            decision = DecisionType.REVIEW
            status = PaymentStatus.SCREENING
        else:
            decision = DecisionType.CLEAR
            status = PaymentStatus.APPROVED
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        result = PaymentScreeningResult(
            payment_id=payment.payment_id,
            transaction_id=payment.transaction_id,
            screening_id=int(time.time() * 1000),
            sender_screening=sender_screening,
            recipient_screening=recipient_screening,
            overall_risk_score=overall_risk_score,
            decision=decision,
            status=status,
            processing_time_ms=processing_time_ms,
            metadata={
                "payment_type": payment.payment_type,
                "amount": payment.amount,
                "currency": payment.currency
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Payment screening failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Payment screening failed: {str(e)}")

@app.get("/api/v1/stats")
async def get_screening_stats():
    """Get screening statistics."""
    if not screening_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        stats = await screening_service.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.get("/api/v1/sanctions-lists")
async def get_sanctions_lists():
    """Get available sanctions lists."""
    if not screening_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        lists = await screening_service.get_sanctions_lists()
        return {"lists": lists}
    except Exception as e:
        logger.error(f"Failed to get sanctions lists: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get sanctions lists: {str(e)}")

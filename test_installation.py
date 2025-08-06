#!/usr/bin/env python3
"""
Test script to verify the sanctions screening platform installation.
"""

import sys
import os
import subprocess
import requests
import time

def test_imports():
    """Test if all required packages can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import transformers
        print("✅ Transformers imported successfully")
    except ImportError as e:
        print(f"❌ Transformers import failed: {e}")
        return False
    
    try:
        import sentence_transformers
        print("✅ Sentence Transformers imported successfully")
    except ImportError as e:
        print(f"❌ Sentence Transformers import failed: {e}")
        return False
    
    try:
        import fuzzywuzzy
        print("✅ FuzzyWuzzy imported successfully")
    except ImportError as e:
        print(f"❌ FuzzyWuzzy import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    return True

def test_app_imports():
    """Test if application modules can be imported."""
    print("\n🔍 Testing application imports...")
    
    try:
        from app.core.config import settings
        print("✅ Configuration imported successfully")
    except ImportError as e:
        print(f"❌ Configuration import failed: {e}")
        return False
    
    try:
        from app.models.database import Base
        print("✅ Database models imported successfully")
    except ImportError as e:
        print(f"❌ Database models import failed: {e}")
        return False
    
    try:
        from app.services.nlp_service import nlp_service
        print("✅ NLP service imported successfully")
    except ImportError as e:
        print(f"❌ NLP service import failed: {e}")
        return False
    
    try:
        from app.services.fuzzy_service import fuzzy_service
        print("✅ Fuzzy service imported successfully")
    except ImportError as e:
        print(f"❌ Fuzzy service import failed: {e}")
        return False
    
    try:
        from app.services.screening_service import screening_service
        print("✅ Screening service imported successfully")
    except ImportError as e:
        print(f"❌ Screening service import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database initialization."""
    print("\n🔍 Testing database...")
    
    try:
        from app.core.database import init_db
        init_db()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def test_bert_model():
    """Test BERT model loading."""
    print("\n🔍 Testing BERT model...")
    
    try:
        from app.services.nlp_service import nlp_service
        if nlp_service.is_model_loaded():
            print("✅ BERT model loaded successfully")
            return True
        else:
            print("❌ BERT model not loaded")
            return False
    except Exception as e:
        print(f"❌ BERT model test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints if server is running."""
    print("\n🔍 Testing API endpoints...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Health endpoint test skipped (server not running): {e}")
        return True  # Not a failure if server isn't running
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Root endpoint working")
        else:
            print(f"❌ Root endpoint returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Root endpoint test skipped (server not running): {e}")
        return True
    
    return True

def main():
    """Run all tests."""
    print("🚀 Sanctions Screening Platform - Installation Test")
    print("=" * 50)
    
    tests = [
        ("Package Imports", test_imports),
        ("Application Imports", test_app_imports),
        ("Database", test_database),
        ("BERT Model", test_bert_model),
        ("API Endpoints", test_api_endpoints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Installation is successful.")
        print("\n🚀 To start the application:")
        print("   python main.py")
        print("   or")
        print("   ./start.sh")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
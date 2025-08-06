"""
Integration tests for the sanctions screening platform.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db
from app.models.database import Base
from app.services.data_loader import load_sample_sanctions_data


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    
    # Load sample data
    db = TestingSessionLocal()
    try:
        load_sample_sanctions_data(db)
    finally:
        db.close()
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create test client."""
    return TestClient(app)


class TestScreeningIntegration:
    """Integration tests for screening functionality."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "database_connected" in data
        assert "bert_model_loaded" in data
    
    def test_screen_entity_clear(self, client):
        """Test screening an entity that should be cleared."""
        request_data = {
            "entity": {
                "name": "Alice Johnson",
                "aliases": ["A. Johnson"],
                "date_of_birth": "1990-01-01",
                "nationality": "Canadian",
                "passport_number": "CAN123456",
                "entity_type": "individual"
            },
            "include_metadata": True
        }
        
        response = client.post("/screen", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["decision"] == "clear"
        assert data["overall_risk_score"] == 0.0
        assert data["confidence_score"] == 1.0
        assert "screening_id" in data
        assert "entity_id" in data
        assert "processing_time_ms" in data
    
    def test_screen_entity_exact_match(self, client):
        """Test screening an entity with exact match."""
        request_data = {
            "entity": {
                "name": "John Smith",
                "aliases": ["Johnny Smith", "J. Smith"],
                "date_of_birth": "1980-05-15",
                "nationality": "American",
                "passport_number": "A12345678",
                "entity_type": "individual"
            },
            "include_metadata": True
        }
        
        response = client.post("/screen", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["decision"] == "block"
        assert data["overall_risk_score"] > 0.9
        assert len(data["matches"]) > 0
        
        # Check match details
        match = data["matches"][0]
        assert match["entity_name"] == "John Smith"
        assert match["source"] == "OFAC"
        assert match["match_type"] == "exact"
        assert match["match_score"] == 1.0
    
    def test_screen_entity_fuzzy_match(self, client):
        """Test screening an entity with fuzzy match."""
        request_data = {
            "entity": {
                "name": "Johnny Smith",  # Slight variation
                "aliases": ["John Smith"],
                "date_of_birth": "1980-05-15",
                "nationality": "American",
                "passport_number": "A12345678",
                "entity_type": "individual"
            },
            "include_metadata": True
        }
        
        response = client.post("/screen", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["decision"] in ["block", "review"]
        assert len(data["matches"]) > 0
    
    def test_screen_entity_organization(self, client):
        """Test screening an organization."""
        request_data = {
            "entity": {
                "name": "Hezbollah",
                "aliases": ["Hizballah"],
                "entity_type": "organization"
            },
            "include_metadata": True
        }
        
        response = client.post("/screen", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["decision"] == "block"
        assert len(data["matches"]) > 0
        
        match = data["matches"][0]
        assert match["entity_name"] == "Hezbollah"
        assert match["source"] == "OFAC"
    
    def test_batch_screening(self, client):
        """Test batch screening functionality."""
        request_data = [
            {
                "entity": {
                    "name": "Alice Johnson",
                    "entity_type": "individual"
                }
            },
            {
                "entity": {
                    "name": "John Smith",
                    "entity_type": "individual"
                }
            }
        ]
        
        response = client.post("/screen/batch", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # First entity should be clear
        assert data[0]["decision"] == "clear"
        
        # Second entity should have matches
        assert data[1]["decision"] in ["block", "review"]
    
    def test_screening_with_threshold_override(self, client):
        """Test screening with custom threshold."""
        request_data = {
            "entity": {
                "name": "John Smith",
                "entity_type": "individual"
            },
            "threshold_override": 0.95  # Very high threshold
        }
        
        response = client.post("/screen", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # With high threshold, should only match exact matches
        assert data["decision"] == "block"
    
    def test_invalid_entity_data(self, client):
        """Test screening with invalid entity data."""
        request_data = {
            "entity": {
                "name": "",  # Empty name
                "entity_type": "individual"
            }
        }
        
        response = client.post("/screen", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_date_format(self, client):
        """Test screening with invalid date format."""
        request_data = {
            "entity": {
                "name": "Test User",
                "date_of_birth": "invalid-date",
                "entity_type": "individual"
            }
        }
        
        response = client.post("/screen", json=request_data)
        assert response.status_code == 422  # Validation error


class TestEntityManagement:
    """Integration tests for entity management."""
    
    def test_get_entities(self, client):
        """Test getting list of entities."""
        response = client.get("/entities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_entity_by_id(self, client):
        """Test getting entity by ID."""
        # First create an entity through screening
        request_data = {
            "entity": {
                "name": "Test Entity",
                "entity_type": "individual"
            }
        }
        
        screening_response = client.post("/screen", json=request_data)
        assert screening_response.status_code == 200
        
        entity_id = screening_response.json()["entity_id"]
        
        # Get entity by ID
        response = client.get(f"/entities/{entity_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == entity_id
        assert data["name"] == "Test Entity"
    
    def test_get_nonexistent_entity(self, client):
        """Test getting non-existent entity."""
        response = client.get("/entities/99999")
        assert response.status_code == 404


class TestSanctionsManagement:
    """Integration tests for sanctions list management."""
    
    def test_get_sanctions_list(self, client):
        """Test getting sanctions list."""
        response = client.get("/sanctions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have sample data
    
    def test_get_sanctions_by_source(self, client):
        """Test getting sanctions by source."""
        response = client.get("/sanctions?source=OFAC")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # All entries should be from OFAC
        for entry in data:
            assert entry["source"] == "OFAC"
    
    def test_get_sanctions_entry_by_id(self, client):
        """Test getting sanctions entry by ID."""
        # First get list to get an ID
        list_response = client.get("/sanctions?limit=1")
        assert list_response.status_code == 200
        
        entries = list_response.json()
        if entries:
            entry_id = entries[0]["id"]
            
            response = client.get(f"/sanctions/{entry_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == entry_id
    
    def test_get_nonexistent_sanctions_entry(self, client):
        """Test getting non-existent sanctions entry."""
        response = client.get("/sanctions/99999")
        assert response.status_code == 404


class TestAnalytics:
    """Integration tests for analytics endpoints."""
    
    def test_get_screening_analytics(self, client):
        """Test getting screening analytics."""
        response = client.get("/analytics/screenings")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_screenings" in data
        assert "clear_decisions" in data
        assert "review_decisions" in data
        assert "block_decisions" in data
        assert "average_processing_time_ms" in data
        assert "average_risk_score" in data
    
    def test_get_screening_analytics_with_dates(self, client):
        """Test getting screening analytics with date range."""
        response = client.get("/analytics/screenings?start_date=2023-01-01&end_date=2023-12-31")
        assert response.status_code == 200
        
        data = response.json()
        assert "period_start" in data
        assert "period_end" in data
    
    def test_get_screening_analytics_invalid_date(self, client):
        """Test getting screening analytics with invalid date."""
        response = client.get("/analytics/screenings?start_date=invalid-date")
        assert response.status_code == 400


class TestSystemEndpoints:
    """Integration tests for system endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Should return Prometheus metrics
        content = response.text
        assert "http_requests_total" in content
        assert "screenings_total" in content 
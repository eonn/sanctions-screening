"""
Unit tests for the screening service.

Author: Eon (Himanshu Shekhar)
Email: himanshu.shekhar@example.com
GitHub: https://github.com/eon-himanshu
Created: 2024
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.services.screening_service import ScreeningService
from app.models.schemas import EntityCreate, EntityType, DecisionType, MatchType
from app.models.database import Entity, SanctionsList


class TestScreeningService:
    """Test cases for ScreeningService."""
    
    @pytest.fixture
    def screening_service(self):
        """Create screening service instance."""
        return ScreeningService()
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_entity_data(self):
        """Sample entity data for testing."""
        return EntityCreate(
            name="John Smith",
            aliases=["Johnny Smith", "J. Smith"],
            date_of_birth="1980-05-15",
            nationality="American",
            passport_number="A12345678",
            entity_type=EntityType.INDIVIDUAL
        )
    
    @pytest.fixture
    def sample_sanctions_entry(self):
        """Sample sanctions entry for testing."""
        return SanctionsList(
            id=1,
            list_name="OFAC SDN List",
            source="OFAC",
            country="United States",
            entity_name="John Smith",
            aliases=["Johnny Smith", "J. Smith"],
            date_of_birth="1980-05-15",
            nationality="American",
            passport_number="A12345678",
            entity_type=EntityType.INDIVIDUAL,
            designation_date="2023-01-15",
            reason="Money laundering",
            is_active=True
        )
    
    def test_get_or_create_entity_new(self, screening_service, mock_db, sample_entity_data):
        """Test creating a new entity."""
        # Mock database query to return None (entity doesn't exist)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        entity = screening_service._get_or_create_entity(mock_db, sample_entity_data)
        
        # Verify entity was created
        assert entity.name == sample_entity_data.name
        assert entity.entity_type == sample_entity_data.entity_type
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_get_or_create_entity_existing(self, screening_service, mock_db, sample_entity_data):
        """Test getting an existing entity."""
        # Mock existing entity
        existing_entity = Entity(
            id=1,
            name=sample_entity_data.name,
            entity_type=sample_entity_data.entity_type
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_entity
        
        entity = screening_service._get_or_create_entity(mock_db, sample_entity_data)
        
        # Verify existing entity was returned
        assert entity.id == 1
        assert entity.name == sample_entity_data.name
        mock_db.add.assert_not_called()
    
    def test_check_exact_match_true(self, screening_service, sample_entity_data):
        """Test exact match detection."""
        entity = Entity(name="John Smith")
        entry = SanctionsList(entity_name="John Smith")
        
        result = screening_service._check_exact_match(entity, entry)
        assert result is True
    
    def test_check_exact_match_false(self, screening_service, sample_entity_data):
        """Test exact match detection with different names."""
        entity = Entity(name="John Smith")
        entry = SanctionsList(entity_name="Jane Smith")
        
        result = screening_service._check_exact_match(entity, entry)
        assert result is False
    
    def test_check_exact_match_with_aliases(self, screening_service, sample_entity_data):
        """Test exact match detection with aliases."""
        entity = Entity(name="John Smith", aliases=["Johnny Smith"])
        entry = SanctionsList(entity_name="Johnny Smith", aliases=["J. Smith"])
        
        result = screening_service._check_exact_match(entity, entry)
        assert result is True
    
    @patch('app.services.screening_service.fuzzy_service')
    def test_calculate_fuzzy_score(self, mock_fuzzy_service, screening_service):
        """Test fuzzy score calculation."""
        entity = Entity(name="John Smith", aliases=["Johnny"])
        entry = SanctionsList(entity_name="John Smith", aliases=["J. Smith"])
        
        # Mock fuzzy service responses
        mock_fuzzy_service.calculate_weighted_average_ratio.return_value = 85.0
        mock_fuzzy_service.normalize_score.return_value = 0.85
        
        score = screening_service._calculate_fuzzy_score(entity, entry)
        
        assert score == 0.85
        mock_fuzzy_service.calculate_weighted_average_ratio.assert_called()
    
    @patch('app.services.screening_service.nlp_service')
    def test_calculate_bert_score(self, mock_nlp_service, screening_service):
        """Test BERT score calculation."""
        entity = Entity(name="John Smith", aliases=["Johnny"])
        entry = SanctionsList(entity_name="John Smith", aliases=["J. Smith"])
        
        # Mock NLP service responses
        mock_nlp_service.calculate_similarity.return_value = 0.9
        
        score = screening_service._calculate_bert_score(entity, entry)
        
        assert score == 0.9
        mock_nlp_service.calculate_similarity.assert_called()
    
    def test_check_additional_fields_exact_dob(self, screening_service):
        """Test additional fields matching with exact DOB."""
        entity = Entity(date_of_birth="1980-05-15")
        entry = SanctionsList(date_of_birth="1980-05-15")
        
        score = screening_service._check_additional_fields(entity, entry)
        assert score == 0.9
    
    def test_check_additional_fields_exact_passport(self, screening_service):
        """Test additional fields matching with exact passport."""
        entity = Entity(passport_number="A12345678")
        entry = SanctionsList(passport_number="A12345678")
        
        score = screening_service._check_additional_fields(entity, entry)
        assert score == 0.95
    
    def test_identify_matched_fields(self, screening_service):
        """Test identification of matched fields."""
        entity = Entity(
            name="John Smith",
            date_of_birth="1980-05-15",
            nationality="American",
            passport_number="A12345678"
        )
        entry = SanctionsList(
            entity_name="John Smith",
            date_of_birth="1980-05-15",
            nationality="American",
            passport_number="A12345678"
        )
        
        matched_fields = screening_service._identify_matched_fields(entity, entry)
        
        expected_fields = ['name', 'date_of_birth', 'nationality', 'passport_number']
        assert set(matched_fields) == set(expected_fields)
    
    def test_calculate_risk_and_decision_clear(self, screening_service):
        """Test risk calculation with clear decision."""
        matches = []  # No matches
        
        risk_score, decision, confidence = screening_service._calculate_risk_and_decision(matches)
        
        assert risk_score == 0.0
        assert decision == DecisionType.CLEAR
        assert confidence == 1.0
    
    def test_calculate_risk_and_decision_block(self, screening_service):
        """Test risk calculation with block decision."""
        matches = [{'risk_score': 0.95}]  # High risk match
        
        risk_score, decision, confidence = screening_service._calculate_risk_and_decision(matches)
        
        assert risk_score > 0.9
        assert decision == DecisionType.BLOCK
        assert confidence == 0.95
    
    def test_calculate_risk_and_decision_review(self, screening_service):
        """Test risk calculation with review decision."""
        matches = [{'risk_score': 0.75}]  # Medium risk match
        
        risk_score, decision, confidence = screening_service._calculate_risk_and_decision(matches)
        
        assert 0.7 <= risk_score < 0.9
        assert decision == DecisionType.REVIEW
        assert confidence == 0.85
    
    def test_create_match_result(self, screening_service):
        """Test creation of match result."""
        entity = Entity(name="John Smith")
        entry = SanctionsList(
            id=1,
            entity_name="John Smith",
            source="OFAC",
            list_name="SDN List",
            designation_date="2023-01-15",
            reason="Money laundering",
            country="United States",
            entity_type=EntityType.INDIVIDUAL
        )
        
        result = screening_service._create_match_result(
            entity, entry, 0.9, MatchType.EXACT, 0.9
        )
        
        assert result['sanctions_entry_id'] == 1
        assert result['entity_name'] == "John Smith"
        assert result['source'] == "OFAC"
        assert result['match_score'] == 0.9
        assert result['match_type'] == MatchType.EXACT
        assert result['risk_score'] == 0.9 
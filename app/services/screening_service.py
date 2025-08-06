"""
Main screening service that combines BERT and fuzzy logic for sanctions screening.
"""
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import Entity, SanctionsList, ScreeningResult, ScreeningMatch
from app.models.schemas import EntityCreate, DecisionType, MatchType
from app.services.nlp_service import nlp_service
from app.services.fuzzy_service import fuzzy_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class ScreeningService:
    """Main screening service for sanctions checking."""
    
    def __init__(self):
        """Initialize the screening service."""
        self.similarity_threshold = settings.similarity_threshold
        self.fuzzy_threshold = settings.fuzzy_threshold
    
    def screen_entity(
        self, 
        db: Session, 
        entity_data: EntityCreate,
        threshold_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Screen an entity against sanctions lists.
        
        Args:
            db: Database session
            entity_data: Entity data to screen
            threshold_override: Optional threshold override
            
        Returns:
            Screening result dictionary
        """
        start_time = time.time()
        
        try:
            # Create or get entity
            entity = self._get_or_create_entity(db, entity_data)
            
            # Get active sanctions entries
            sanctions_entries = self._get_active_sanctions_entries(db)
            
            # Perform screening
            matches = self._perform_screening(entity, sanctions_entries, threshold_override)
            
            # Calculate overall risk score and decision
            risk_score, decision, confidence = self._calculate_risk_and_decision(matches)
            
            # Create screening result
            processing_time_ms = int((time.time() - start_time) * 1000)
            screening_result = self._create_screening_result(
                db, entity, risk_score, decision, confidence, processing_time_ms, matches
            )
            
            # Prepare response
            response = self._prepare_screening_response(screening_result, matches)
            
            logger.info(
                f"Screening completed for entity {entity.name}: "
                f"decision={decision}, risk_score={risk_score:.3f}, "
                f"processing_time={processing_time_ms}ms"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error during screening: {e}")
            raise
    
    def _get_or_create_entity(self, db: Session, entity_data: EntityCreate) -> Entity:
        """Get existing entity or create new one."""
        # Check if entity already exists
        existing_entity = db.query(Entity).filter(
            Entity.name == entity_data.name,
            Entity.entity_type == entity_data.entity_type
        ).first()
        
        if existing_entity:
            return existing_entity
        
        # Create new entity
        entity = Entity(
            name=entity_data.name,
            aliases=entity_data.aliases,
            date_of_birth=entity_data.date_of_birth,
            nationality=entity_data.nationality,
            passport_number=entity_data.passport_number,
            entity_type=entity_data.entity_type
        )
        
        db.add(entity)
        db.commit()
        db.refresh(entity)
        
        return entity
    
    def _get_active_sanctions_entries(self, db: Session) -> List[SanctionsList]:
        """Get all active sanctions entries."""
        return db.query(SanctionsList).filter(SanctionsList.is_active == True).all()
    
    def _perform_screening(
        self, 
        entity: Entity, 
        sanctions_entries: List[SanctionsList],
        threshold_override: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform comprehensive screening using multiple matching algorithms.
        
        Args:
            entity: Entity to screen
            sanctions_entries: List of sanctions entries to check against
            threshold_override: Optional threshold override
            
        Returns:
            List of matches found
        """
        matches = []
        threshold = threshold_override or self.similarity_threshold
        
        for entry in sanctions_entries:
            match_result = self._check_single_entry(entity, entry, threshold)
            if match_result:
                matches.append(match_result)
        
        # Sort matches by risk score (descending)
        matches.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return matches
    
    def _check_single_entry(
        self, 
        entity: Entity, 
        entry: SanctionsList,
        threshold: float
    ) -> Optional[Dict[str, Any]]:
        """
        Check a single entity against a single sanctions entry.
        
        Args:
            entity: Entity to check
            entry: Sanctions entry to check against
            threshold: Similarity threshold
            
        Returns:
            Match result if found, None otherwise
        """
        # Check exact match first
        if self._check_exact_match(entity, entry):
            return self._create_match_result(entity, entry, 1.0, MatchType.EXACT, 1.0)
        
        # Check fuzzy match
        fuzzy_score = self._calculate_fuzzy_score(entity, entry)
        if fuzzy_score >= threshold:
            return self._create_match_result(entity, entry, fuzzy_score, MatchType.FUZZY, fuzzy_score)
        
        # Check BERT similarity
        bert_score = self._calculate_bert_score(entity, entry)
        if bert_score >= threshold:
            return self._create_match_result(entity, entry, bert_score, MatchType.BERT, bert_score)
        
        # Check additional fields if available
        additional_score = self._check_additional_fields(entity, entry)
        if additional_score >= threshold:
            return self._create_match_result(entity, entry, additional_score, MatchType.FUZZY, additional_score)
        
        return None
    
    def _check_exact_match(self, entity: Entity, entry: SanctionsList) -> bool:
        """Check for exact name match."""
        # Check main name
        if entity.name.lower() == entry.entity_name.lower():
            return True
        
        # Check aliases
        entity_aliases = [alias.lower() for alias in (entity.aliases or [])]
        entry_aliases = [alias.lower() for alias in (entry.aliases or [])]
        
        for entity_alias in entity_aliases:
            if entity_alias in entry_aliases or entity_alias == entry.entity_name.lower():
                return True
        
        for entry_alias in entry_aliases:
            if entry_alias == entity.name.lower():
                return True
        
        return False
    
    def _calculate_fuzzy_score(self, entity: Entity, entry: SanctionsList) -> float:
        """Calculate fuzzy matching score."""
        # Calculate fuzzy similarity for main name
        main_score = fuzzy_service.calculate_weighted_average_ratio(
            entity.name, entry.entity_name
        )
        main_score = fuzzy_service.normalize_score(main_score)
        
        # Calculate fuzzy similarity for aliases
        alias_scores = []
        entity_aliases = entity.aliases or []
        entry_aliases = entry.aliases or []
        
        for entity_alias in entity_aliases:
            for entry_alias in entry_aliases:
                score = fuzzy_service.calculate_weighted_average_ratio(entity_alias, entry_alias)
                alias_scores.append(fuzzy_service.normalize_score(score))
        
        # Return the maximum score
        all_scores = [main_score] + alias_scores
        return max(all_scores) if all_scores else 0.0
    
    def _calculate_bert_score(self, entity: Entity, entry: SanctionsList) -> float:
        """Calculate BERT similarity score."""
        try:
            # Calculate BERT similarity for main name
            main_score = nlp_service.calculate_similarity(entity.name, entry.entity_name)
            
            # Calculate BERT similarity for aliases
            alias_scores = []
            entity_aliases = entity.aliases or []
            entry_aliases = entry.aliases or []
            
            for entity_alias in entity_aliases:
                for entry_alias in entry_aliases:
                    score = nlp_service.calculate_similarity(entity_alias, entry_alias)
                    alias_scores.append(score)
            
            # Return the maximum score
            all_scores = [main_score] + alias_scores
            return max(all_scores) if all_scores else 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating BERT score: {e}")
            return 0.0
    
    def _check_additional_fields(self, entity: Entity, entry: SanctionsList) -> float:
        """Check additional fields like DOB, nationality, passport."""
        scores = []
        
        # Check date of birth
        if entity.date_of_birth and entry.date_of_birth:
            if entity.date_of_birth == entry.date_of_birth:
                scores.append(0.9)  # High score for exact DOB match
        
        # Check nationality
        if entity.nationality and entry.nationality:
            nationality_score = fuzzy_service.calculate_weighted_average_ratio(
                entity.nationality, entry.nationality
            )
            scores.append(fuzzy_service.normalize_score(nationality_score) * 0.7)
        
        # Check passport number
        if entity.passport_number and entry.passport_number:
            if entity.passport_number == entry.passport_number:
                scores.append(0.95)  # Very high score for exact passport match
        
        return max(scores) if scores else 0.0
    
    def _create_match_result(
        self, 
        entity: Entity, 
        entry: SanctionsList,
        match_score: float,
        match_type: MatchType,
        risk_score: float
    ) -> Dict[str, Any]:
        """Create a match result dictionary."""
        return {
            'sanctions_entry_id': entry.id,
            'entity_name': entry.entity_name,
            'source': entry.source,
            'list_name': entry.list_name,
            'match_score': match_score,
            'match_type': match_type,
            'matched_fields': self._identify_matched_fields(entity, entry),
            'risk_score': risk_score,
            'match_details': {
                'designation_date': entry.designation_date,
                'reason': entry.reason,
                'country': entry.country,
                'entity_type': entry.entity_type
            }
        }
    
    def _identify_matched_fields(self, entity: Entity, entry: SanctionsList) -> List[str]:
        """Identify which fields matched."""
        matched_fields = []
        
        # Check name match
        if entity.name.lower() == entry.entity_name.lower():
            matched_fields.append('name')
        
        # Check DOB match
        if entity.date_of_birth and entry.date_of_birth:
            if entity.date_of_birth == entry.date_of_birth:
                matched_fields.append('date_of_birth')
        
        # Check nationality match
        if entity.nationality and entry.nationality:
            if entity.nationality.lower() == entry.nationality.lower():
                matched_fields.append('nationality')
        
        # Check passport match
        if entity.passport_number and entry.passport_number:
            if entity.passport_number == entry.passport_number:
                matched_fields.append('passport_number')
        
        return matched_fields
    
    def _calculate_risk_and_decision(
        self, 
        matches: List[Dict[str, Any]]
    ) -> Tuple[float, DecisionType, float]:
        """
        Calculate overall risk score and decision based on matches.
        
        Args:
            matches: List of matches found
            
        Returns:
            Tuple of (risk_score, decision, confidence)
        """
        if not matches:
            return 0.0, DecisionType.CLEAR, 1.0
        
        # Calculate overall risk score (weighted average of match scores)
        total_weight = 0
        weighted_sum = 0
        
        for match in matches:
            weight = match['risk_score']
            weighted_sum += match['risk_score'] * weight
            total_weight += weight
        
        overall_risk_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Determine decision based on risk score
        if overall_risk_score >= 0.9:
            decision = DecisionType.BLOCK
            confidence = 0.95
        elif overall_risk_score >= 0.7:
            decision = DecisionType.REVIEW
            confidence = 0.85
        else:
            decision = DecisionType.CLEAR
            confidence = 0.9
        
        return overall_risk_score, decision, confidence
    
    def _create_screening_result(
        self,
        db: Session,
        entity: Entity,
        risk_score: float,
        decision: DecisionType,
        confidence: float,
        processing_time_ms: int,
        matches: List[Dict[str, Any]]
    ) -> ScreeningResult:
        """Create and save screening result."""
        screening_result = ScreeningResult(
            entity_id=entity.id,
            overall_risk_score=risk_score,
            decision=decision,
            confidence_score=confidence,
            processing_time_ms=processing_time_ms,
            screening_metadata={
                'total_matches': len(matches),
                'match_types': [match['match_type'] for match in matches],
                'sources': list(set(match['source'] for match in matches))
            }
        )
        
        db.add(screening_result)
        db.commit()
        db.refresh(screening_result)
        
        # Create individual match records
        for match in matches:
            screening_match = ScreeningMatch(
                screening_result_id=screening_result.id,
                sanctions_entry_id=match['sanctions_entry_id'],
                match_score=match['match_score'],
                match_type=match['match_type'],
                matched_fields=match['matched_fields'],
                risk_score=match['risk_score'],
                match_details=match['match_details']
            )
            db.add(screening_match)
        
        db.commit()
        
        return screening_result
    
    def _prepare_screening_response(
        self, 
        screening_result: ScreeningResult,
        matches: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare the final screening response."""
        return {
            'screening_id': screening_result.id,
            'entity_id': screening_result.entity_id,
            'entity_name': screening_result.entity.name,
            'screening_date': screening_result.screening_date,
            'overall_risk_score': screening_result.overall_risk_score,
            'decision': screening_result.decision,
            'confidence_score': screening_result.confidence_score,
            'processing_time_ms': screening_result.processing_time_ms,
            'matches': matches,
            'metadata': screening_result.screening_metadata
        }


# Global screening service instance
screening_service = ScreeningService() 
# Global screening service instance
screening_service = ScreeningService()

# Add async wrapper methods
async def initialize(self):
    """Initialize the screening service."""
    logger.info("Initializing screening service...")
    # Initialize any async resources here
    pass

async def cleanup(self):
    """Cleanup the screening service."""
    logger.info("Cleaning up screening service...")
    # Cleanup any async resources here
    pass

async def screen_entity_async(self, request):
    """Async wrapper for screening an entity."""
    from app.core.database import get_db
    db = next(get_db())
    try:
        result = self.screen_entity(db, request.entity, request.threshold_override)
        return result
    finally:
        db.close()

async def get_statistics(self):
    """Get screening statistics."""
    from app.core.database import get_db
    db = next(get_db())
    try:
        # Get basic statistics
        total_screenings = db.query(ScreeningResult).count()
        clear_decisions = db.query(ScreeningResult).filter(ScreeningResult.decision == DecisionType.CLEAR).count()
        review_decisions = db.query(ScreeningResult).filter(ScreeningResult.decision == DecisionType.REVIEW).count()
        block_decisions = db.query(ScreeningResult).filter(ScreeningResult.decision == DecisionType.BLOCK).count()
        
        return {
            'total_screenings': total_screenings,
            'clear_decisions': clear_decisions,
            'review_decisions': review_decisions,
            'block_decisions': block_decisions,
            'average_processing_time_ms': 0,  # TODO: Calculate actual average
            'average_risk_score': 0,  # TODO: Calculate actual average
        }
    finally:
        db.close()

async def get_sanctions_lists(self):
    """Get available sanctions lists."""
    from app.core.database import get_db
    db = next(get_db())
    try:
        lists = db.query(SanctionsList).distinct(SanctionsList.list_name).all()
        return [{'name': list.list_name, 'source': list.source} for list in lists]
    finally:
        db.close()

# Add methods to ScreeningService class
ScreeningService.initialize = initialize
ScreeningService.cleanup = cleanup
ScreeningService.screen_entity_async = screen_entity_async
ScreeningService.get_statistics = get_statistics
ScreeningService.get_sanctions_lists = get_sanctions_lists

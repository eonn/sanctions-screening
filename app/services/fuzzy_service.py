"""
Fuzzy logic service for name similarity matching.
"""
import logging
from typing import List, Dict, Tuple, Optional
from fuzzywuzzy import fuzz
from rapidfuzz import fuzz as rapid_fuzz
from app.core.config import settings

logger = logging.getLogger(__name__)


class FuzzyService:
    """Fuzzy logic service for name matching."""
    
    def __init__(self):
        """Initialize the fuzzy service."""
        self.threshold = settings.fuzzy_threshold
        
    def calculate_levenshtein_distance(self, str1: str, str2: str) -> int:
        """
        Calculate Levenshtein distance between two strings.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Levenshtein distance
        """
        if not str1 or not str2:
            return max(len(str1), len(str2))
        
        return fuzz.ratio(str1.lower(), str2.lower())
    
    def calculate_similarity_ratio(self, str1: str, str2: str) -> float:
        """
        Calculate similarity ratio using fuzzywuzzy.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity ratio between 0 and 100
        """
        if not str1 or not str2:
            return 0.0
        
        return fuzz.ratio(str1.lower(), str2.lower())
    
    def calculate_partial_ratio(self, str1: str, str2: str) -> float:
        """
        Calculate partial ratio for substring matching.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Partial ratio between 0 and 100
        """
        if not str1 or not str2:
            return 0.0
        
        return fuzz.partial_ratio(str1.lower(), str2.lower())
    
    def calculate_token_sort_ratio(self, str1: str, str2: str) -> float:
        """
        Calculate token sort ratio for word order independent matching.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Token sort ratio between 0 and 100
        """
        if not str1 or not str2:
            return 0.0
        
        return fuzz.token_sort_ratio(str1.lower(), str2.lower())
    
    def calculate_token_set_ratio(self, str1: str, str2: str) -> float:
        """
        Calculate token set ratio for partial word matching.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Token set ratio between 0 and 100
        """
        if not str1 or not str2:
            return 0.0
        
        return fuzz.token_set_ratio(str1.lower(), str2.lower())
    
    def calculate_weighted_average_ratio(self, str1: str, str2: str) -> float:
        """
        Calculate weighted average of multiple fuzzy ratios.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Weighted average ratio between 0 and 100
        """
        if not str1 or not str2:
            return 0.0
        
        # Calculate different ratios
        simple_ratio = fuzz.ratio(str1.lower(), str2.lower())
        partial_ratio = fuzz.partial_ratio(str1.lower(), str2.lower())
        token_sort_ratio = fuzz.token_sort_ratio(str1.lower(), str2.lower())
        token_set_ratio = fuzz.token_set_ratio(str1.lower(), str2.lower())
        
        # Weighted average (can be adjusted based on requirements)
        weights = [0.3, 0.2, 0.25, 0.25]  # Simple, Partial, Token Sort, Token Set
        ratios = [simple_ratio, partial_ratio, token_sort_ratio, token_set_ratio]
        
        weighted_avg = sum(w * r for w, r in zip(weights, ratios))
        
        return weighted_avg
    
    def calculate_rapid_fuzz_ratio(self, str1: str, str2: str) -> float:
        """
        Calculate similarity using rapidfuzz (faster implementation).
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity ratio between 0 and 100
        """
        if not str1 or not str2:
            return 0.0
        
        return rapid_fuzz.ratio(str1.lower(), str2.lower())
    
    def extract_tokens(self, text: str) -> List[str]:
        """
        Extract tokens from text for token-based matching.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        # Split by whitespace and filter out empty tokens
        tokens = [token.strip() for token in text.split() if token.strip()]
        
        # Remove common stop words (can be expanded)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among'
        }
        
        tokens = [token for token in tokens if token.lower() not in stop_words]
        
        return tokens
    
    def calculate_token_overlap(self, str1: str, str2: str) -> float:
        """
        Calculate token overlap ratio.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Token overlap ratio between 0 and 1
        """
        tokens1 = set(self.extract_tokens(str1))
        tokens2 = set(self.extract_tokens(str2))
        
        if not tokens1 and not tokens2:
            return 1.0
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union)
    
    def normalize_score(self, score: float) -> float:
        """
        Normalize score to 0-1 range.
        
        Args:
            score: Raw score (0-100)
            
        Returns:
            Normalized score (0-1)
        """
        return score / 100.0
    
    def is_match(self, str1: str, str2: str, threshold: Optional[float] = None) -> Tuple[bool, float]:
        """
        Determine if two strings match based on fuzzy logic.
        
        Args:
            str1: First string
            str2: Second string
            threshold: Custom threshold (optional)
            
        Returns:
            Tuple of (is_match, confidence_score)
        """
        if threshold is None:
            threshold = self.threshold
        
        # Calculate weighted average ratio
        score = self.calculate_weighted_average_ratio(str1, str2)
        normalized_score = self.normalize_score(score)
        
        is_match_result = normalized_score >= threshold
        
        return is_match_result, normalized_score
    
    def find_best_matches(
        self, 
        query: str, 
        candidates: List[str], 
        threshold: Optional[float] = None,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find best matches for a query among candidates.
        
        Args:
            query: Query string
            candidates: List of candidate strings
            threshold: Minimum threshold for matches
            top_k: Number of top matches to return
            
        Returns:
            List of (candidate, score) tuples sorted by score
        """
        if threshold is None:
            threshold = self.threshold
        
        matches = []
        
        for candidate in candidates:
            score = self.calculate_weighted_average_ratio(query, candidate)
            normalized_score = self.normalize_score(score)
            
            if normalized_score >= threshold:
                matches.append((candidate, normalized_score))
        
        # Sort by score (descending) and return top_k
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_k]
    
    def calculate_name_similarity(
        self, 
        name1: str, 
        name2: str,
        include_variations: bool = True
    ) -> Dict[str, float]:
        """
        Calculate comprehensive name similarity using multiple methods.
        
        Args:
            name1: First name
            name2: Second name
            include_variations: Whether to include name variations
            
        Returns:
            Dictionary with different similarity scores
        """
        results = {
            'simple_ratio': self.normalize_score(self.calculate_similarity_ratio(name1, name2)),
            'partial_ratio': self.normalize_score(self.calculate_partial_ratio(name1, name2)),
            'token_sort_ratio': self.normalize_score(self.calculate_token_sort_ratio(name1, name2)),
            'token_set_ratio': self.normalize_score(self.calculate_token_set_ratio(name1, name2)),
            'weighted_average': self.normalize_score(self.calculate_weighted_average_ratio(name1, name2)),
            'rapid_fuzz': self.normalize_score(self.calculate_rapid_fuzz_ratio(name1, name2)),
            'token_overlap': self.calculate_token_overlap(name1, name2)
        }
        
        if include_variations:
            # Calculate similarity with name variations
            from app.services.nlp_service import nlp_service
            
            variations1 = nlp_service.get_name_variations(name1)
            variations2 = nlp_service.get_name_variations(name2)
            
            max_variation_score = 0.0
            for var1 in variations1:
                for var2 in variations2:
                    score = self.normalize_score(self.calculate_weighted_average_ratio(var1, var2))
                    max_variation_score = max(max_variation_score, score)
            
            results['variation_score'] = max_variation_score
        
        return results


# Global fuzzy service instance
fuzzy_service = FuzzyService() 
"""
BERT-based NLP service for semantic similarity and name processing.

Author: Eon (Himanshu Shekhar)
Email: himanshu.shekhar@example.com
GitHub: https://github.com/eon-himanshu
Created: 2024
"""
import logging
import time
from typing import List, Dict, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch
from app.core.config import settings

logger = logging.getLogger(__name__)


class NLPService:
    """BERT-based NLP service for sanctions screening."""
    
    def __init__(self):
        """Initialize the NLP service with BERT model."""
        self.model = None
        self.model_name = settings.bert_model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()
    
    def _load_model(self):
        """Load the BERT model."""
        try:
            logger.info(f"Loading BERT model: {self.model_name}")
            start_time = time.time()
            
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            load_time = time.time() - start_time
            logger.info(f"BERT model loaded successfully in {load_time:.2f}s on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load BERT model: {e}")
            raise
    
    def preprocess_name(self, name: str) -> str:
        """
        Preprocess entity name for better matching.
        
        Args:
            name: Raw entity name
            
        Returns:
            Preprocessed name
        """
        if not name:
            return ""
        
        # Convert to lowercase
        name = name.lower().strip()
        
        # Remove extra whitespace
        name = " ".join(name.split())
        
        # Remove common prefixes/suffixes that might affect matching
        prefixes_to_remove = ["mr.", "mrs.", "ms.", "dr.", "prof.", "sir", "madam"]
        suffixes_to_remove = ["jr.", "sr.", "i", "ii", "iii", "iv", "v"]
        
        for prefix in prefixes_to_remove:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
        
        for suffix in suffixes_to_remove:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
        
        return name
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Get BERT embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        try:
            # Preprocess texts
            processed_texts = [self.preprocess_name(text) for text in texts]
            
            # Get embeddings
            embeddings = self.model.encode(processed_texts, convert_to_numpy=True)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts using BERT.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            embeddings = self.get_embeddings([text1, text2])
            
            if len(embeddings) < 2:
                return 0.0
            
            # Calculate cosine similarity
            similarity = cosine_similarity(
                embeddings[0:1], embeddings[1:2]
            )[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def batch_similarity(self, query_text: str, candidate_texts: List[str]) -> List[float]:
        """
        Calculate similarity between query text and multiple candidates.
        
        Args:
            query_text: Query text
            candidate_texts: List of candidate texts
            
        Returns:
            List of similarity scores
        """
        if not candidate_texts:
            return []
        
        try:
            all_texts = [query_text] + candidate_texts
            embeddings = self.get_embeddings(all_texts)
            
            if len(embeddings) < 2:
                return [0.0] * len(candidate_texts)
            
            query_embedding = embeddings[0:1]
            candidate_embeddings = embeddings[1:]
            
            # Calculate cosine similarities
            similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]
            
            return [float(sim) for sim in similarities]
            
        except Exception as e:
            logger.error(f"Error in batch similarity: {e}")
            return [0.0] * len(candidate_texts)
    
    def extract_name_components(self, full_name: str) -> Dict[str, str]:
        """
        Extract name components (first, middle, last) from full name.
        
        Args:
            full_name: Full name string
            
        Returns:
            Dictionary with name components
        """
        if not full_name:
            return {"first": "", "middle": "", "last": ""}
        
        # Clean the name
        name = full_name.strip()
        parts = name.split()
        
        if len(parts) == 1:
            return {"first": parts[0], "middle": "", "last": ""}
        elif len(parts) == 2:
            return {"first": parts[0], "middle": "", "last": parts[1]}
        else:
            return {
                "first": parts[0],
                "middle": " ".join(parts[1:-1]),
                "last": parts[-1]
            }
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize name for consistent comparison.
        
        Args:
            name: Raw name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Convert to lowercase and remove extra spaces
        normalized = " ".join(name.lower().split())
        
        # Remove punctuation except spaces
        import re
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized
    
    def get_name_variations(self, name: str) -> List[str]:
        """
        Generate common name variations for matching.
        
        Args:
            name: Original name
            
        Returns:
            List of name variations
        """
        variations = [name]
        
        if not name:
            return variations
        
        # Add normalized version
        normalized = self.normalize_name(name)
        if normalized != name:
            variations.append(normalized)
        
        # Add components
        components = self.extract_name_components(name)
        
        # Add first + last
        if components["first"] and components["last"]:
            first_last = f"{components['first']} {components['last']}"
            if first_last not in variations:
                variations.append(first_last)
        
        # Add last + first
        if components["first"] and components["last"]:
            last_first = f"{components['last']} {components['first']}"
            if last_first not in variations:
                variations.append(last_first)
        
        # Add initials
        if components["first"] and components["last"]:
            initials = f"{components['first'][0]}. {components['last']}"
            if initials not in variations:
                variations.append(initials)
        
        return variations
    
    def is_model_loaded(self) -> bool:
        """Check if the BERT model is loaded."""
        return self.model is not None


# Global NLP service instance
nlp_service = NLPService() 
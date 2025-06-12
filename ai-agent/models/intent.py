"""
Intent analysis related models - Focus on academic research scenarios
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass

class IntentType(Enum):
    """Academic research intent type enumeration"""
    # Paper related
    SEARCH_PAPERS = "search_papers"
    GET_PAPER_DETAILS = "get_paper_details"
    GET_PAPER_CITATIONS = "get_paper_citations"

    # Author related
    SEARCH_AUTHORS = "search_authors"
    GET_AUTHOR_DETAILS = "search_authors"
    GET_AUTHOR_PAPERS = "get_author_papers"
    
    # Network analysis
    CITATION_NETWORK = "citation_network"
    COLLABORATION_NETWORK = "collaboration_network"
    
    # Trend analysis
    GET_TRENDING_PAPERS = "get_trending_papers"
    GET_TOP_KEYWORDS = "get_top_keywords"
    RESEARCH_TRENDS = "unknown"  # todo
    RESEARCH_LANDSCAPE = "unknown"  # todo

    # General chat
    GENERAL_CHAT = "general_chat"
    
    # Unknown intent
    UNKNOWN = "unknown"

@dataclass
class Intent:
    """Single intent"""
    type: IntentType
    confidence: float = 0.0
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type.value,
            "confidence": self.confidence,
            "parameters": self.parameters
        }

class IntentAnalysisResult(BaseModel):
    """Intent analysis result"""
    primary_intent: Intent
    confidence_threshold: float = Field(default=0.7)
    needs_clarification: bool = Field(default=False)
    clarification_question: Optional[str] = Field(default=None)
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def is_confident(self) -> bool:
        """Determine if there is enough confidence"""
        return self.primary_intent.confidence >= self.confidence_threshold
    
    @property
    def is_academic_query(self) -> bool:
        """Determine if it is an academic query"""
        academic_intents = {
            IntentType.SEARCH_PAPERS,
            IntentType.GET_PAPER_DETAILS,
            IntentType.SEARCH_AUTHORS,
            IntentType.GET_AUTHOR_DETAILS,
            IntentType.CITATION_NETWORK,
            IntentType.COLLABORATION_NETWORK,
            IntentType.RESEARCH_TRENDS,
            IntentType.RESEARCH_LANDSCAPE
        }
        return self.primary_intent.type in academic_intents
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "primary_intent": self.primary_intent.to_dict(),
            "confidence_threshold": self.confidence_threshold,
            "needs_clarification": self.needs_clarification,
            "clarification_question": self.clarification_question,
            "extracted_entities": self.extracted_entities,
            "is_confident": self.is_confident,
            "is_academic_query": self.is_academic_query
        }

# Predefined intent templates
class IntentTemplates:
    """Intent template class"""
    
    @staticmethod
    def search_papers(query: str, confidence: float = 0.8) -> Intent:
        """Search papers intent"""
        return Intent(
            type=IntentType.SEARCH_PAPERS,
            confidence=confidence,
            parameters={"query": query}
        )
    
    @staticmethod
    def search_authors(query: str, confidence: float = 0.8) -> Intent:
        """Search authors intent"""
        return Intent(
            type=IntentType.SEARCH_AUTHORS,
            confidence=confidence,
            parameters={"query": query}
        )
    
    @staticmethod
    def get_author_details(query: str, confidence: float = 0.8) -> Intent:
        """Get author details intent - Use the same search_authors tool"""
        return Intent(
            type=IntentType.GET_AUTHOR_DETAILS,
            confidence=confidence,
            parameters={
                "query": query,
                "detailed": True,  # Mark as detailed query
                "include_coauthors": True,
                "include_papers": True
            }
        )
    
    @staticmethod
    def get_paper_details(paper_id: str, confidence: float = 0.9) -> Intent:
        """Get paper details intent"""
        return Intent(
            type=IntentType.GET_PAPER_DETAILS,
            confidence=confidence,
            parameters={"title": paper_id}
        )
    
    @staticmethod
    def general_chat(confidence: float = 0.6) -> Intent:
        """General chat intent"""
        return Intent(
            type=IntentType.GENERAL_CHAT,
            confidence=confidence,
            parameters={}
        )
    
    @staticmethod
    def unknown(confidence: float = 0.3) -> Intent:
        """Unknown intent"""
        return Intent(
            type=IntentType.UNKNOWN,
            confidence=confidence,
            parameters={}
        )

"""
Research-related result models
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class PaperInfo(BaseModel):
    """Paper Information Model"""
    id: str = Field(..., description="Paper ID")
    title: str = Field(..., description="Paper Title")
    authors: List[str] = Field(..., description="Author List")
    year: Optional[int] = Field(None, description="Publication Year")
    venue: Optional[str] = Field(None, description="Conference/Journal")
    citations: Optional[int] = Field(None, description="Citation Count")
    abstract: Optional[str] = Field(None, description="Abstract")
    url: Optional[str] = Field(None, description="Paper URL")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "paper_123",
                "title": "Attention Is All You Need",
                "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
                "year": 2017,
                "venue": "NeurIPS",
                "citations": 50000,
                "abstract": "The dominant sequence transduction models...",
                "url": "https://arxiv.org/abs/1706.03762"
            }
        }
    }

class AuthorInfo(BaseModel):
    """Author Information Model"""
    id: str = Field(..., description="Author ID")
    name: str = Field(..., description="Author Name")
    affiliation: Optional[str] = Field(None, description="Affiliation")
    h_index: Optional[int] = Field(None, description="H-index")
    paper_count: Optional[int] = Field(None, description="Number of Papers")
    citation_count: Optional[int] = Field(None, description="Total Citations")
    research_interests: List[str] = Field(default_factory=list, description="Research Interests")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "author_123",
                "name": "Ashish Vaswani",
                "affiliation": "Google Research",
                "h_index": 45,
                "paper_count": 50,
                "citation_count": 100000,
                "research_interests": ["machine learning", "natural language processing", "attention mechanisms"]
            }
        }
    }

class SearchResult(BaseModel):
    """Search Result Model"""
    query: str = Field(..., description="Search Query")
    total_count: int = Field(..., description="Total Result Count")
    papers: List[PaperInfo] = Field(default_factory=list, description="Paper List")
    authors: List[AuthorInfo] = Field(default_factory=list, description="Author List")
    search_time: float = Field(..., description="Search Time")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Applied Filters")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "transformer attention mechanism",
                "total_count": 1500,
                "papers": [],
                "authors": [],
                "search_time": 1.2,
                "filters": {
                    "year_range": [2017, 2024],
                    "min_citations": 10
                }
            }
        }
    }

class NetworkNode(BaseModel):
    """Network Node Model"""
    id: str = Field(..., description="Node ID")
    label: str = Field(..., description="Node Label")
    type: str = Field(..., description="Node Type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node Properties")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "paper_123",
                "label": "Attention Is All You Need",
                "type": "paper",
                "properties": {
                    "year": 2017,
                    "citations": 50000,
                    "venue": "NeurIPS"
                }
            }
        }
    }

class NetworkEdge(BaseModel):
    """Network Edge Model"""
    source: str = Field(..., description="Source Node ID")
    target: str = Field(..., description="Target Node ID")
    type: str = Field(..., description="Edge Type")
    weight: Optional[float] = Field(None, description="Edge Weight")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge Properties")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "source": "paper_123",
                "target": "paper_456",
                "type": "citation",
                "weight": 1.0,
                "properties": {
                    "citation_context": "building upon the transformer architecture"
                }
            }
        }
    }

class NetworkAnalysisResult(BaseModel):
    """Network Analysis Result Model"""
    nodes: List[NetworkNode] = Field(..., description="Network Nodes")
    edges: List[NetworkEdge] = Field(..., description="Network Edges")
    metrics: Dict[str, Any] = Field(..., description="Network Metrics")
    analysis_type: str = Field(..., description="Analysis Type")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "nodes": [],
                "edges": [],
                "metrics": {
                    "node_count": 50,
                    "edge_count": 75,
                    "density": 0.15,
                    "clustering_coefficient": 0.3
                },
                "analysis_type": "citation_network"
            }
        }
    }

class TrendData(BaseModel):
    """Trend Data Model"""
    period: str = Field(..., description="Time Period")
    value: float = Field(..., description="Value")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "period": "2023",
                "value": 1500.0,
                "metadata": {
                    "paper_count": 1500,
                    "top_keywords": ["transformer", "attention", "bert"]
                }
            }
        }
    }

class TrendAnalysisResult(BaseModel):
    """Trend Analysis Result Model"""
    topic: str = Field(..., description="Analysis Topic")
    time_range: Dict[str, str] = Field(..., description="Time Range")
    trends: List[TrendData] = Field(..., description="Trend Data")
    analysis_type: str = Field(..., description="Analysis Type")
    insights: List[str] = Field(default_factory=list, description="Analysis Insights")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "topic": "transformer architecture",
                "time_range": {"start": "2017", "end": "2024"},
                "trends": [],
                "analysis_type": "research_trends",
                "insights": [
                    "Rapid growth in Transformer papers after 2020",
                    "Attention mechanism becomes a research hotspot"
                ]
            }
        }
    }

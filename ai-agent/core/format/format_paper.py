"""
Paper formatting utilities for displaying research paper information.
"""

from typing import Dict, List, Any
from datetime import datetime


def format_paper_list(papers_data: Dict[str, Any]) -> str:
    """
    Format a list of papers for display.
    
    Args:
        papers_data: Dictionary containing 'count' and 'papers' list
        
    Returns:
        Formatted string representation of papers
    """
    if not papers_data or 'papers' not in papers_data:
        return "No papers found."
    
    papers = papers_data['papers']
    count = papers_data.get('count', len(papers))
    
    result = f"Found {count} papers:\n\n"
    
    for i, paper in enumerate(papers, 1):
        result += format_single_paper(paper, index=i)
        result += "\n\n"
    
    return result.strip()


def format_single_paper(paper: Dict[str, Any], index: int = None) -> str:
    """
    Format a single paper for display.
    
    Args:
        paper: Dictionary containing paper information
        index: Optional index number for the paper
        
    Returns:
        Formatted string representation of the paper
    """
    title = paper.get('title', 'No title')
    authors = format_authors(paper.get('authors', []))
    abstract = paper.get('abstract', 'No abstract available')
    venue = paper.get('venue_name', 'Unknown venue')
    published_date = format_date(paper.get('published_at'))
    citations = paper.get('citations', 0)
    keywords = ', '.join(paper.get('keywords', []))
    doi = paper.get('doi', 'No DOI')
    url = paper.get('url', 'No URL')
    
    # Truncate abstract to 150 characters
    if len(abstract) > 120:
        abstract = abstract[:120] + "..."
    
    result = ""
    if index:
        result += f"[{index}] "
    
    result += f"**{title}**\n\n"
    result += f"Authors: {authors}\n"
    result += f"Venue: {venue}\n"
    result += f"Published: {published_date}\n"
    result += f"Citations: {citations}\n"
    
    if keywords:
        result += f"Keywords: {keywords}\n"
    
    result += f"DOI: {doi}\n"
    result += f"URL: {url}\n\n"
    result += f"Abstract:\n{abstract}\n"
    
    return result


def format_authors(authors: List[Dict[str, Any]]) -> str:
    """
    Format author list for display.
    
    Args:
        authors: List of author dictionaries with 'name' field
        
    Returns:
        Comma-separated string of author names
    """
    if not authors:
        return "No authors listed"
    
    author_names = [author.get('name', 'Unknown') for author in authors]
    return ', '.join(author_names)


def format_date(timestamp: int) -> str:
    """
    Format timestamp to readable date.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted date string
    """
    if not timestamp:
        return "Unknown date"
    
    try:
        date = datetime.fromtimestamp(timestamp)
        return date.strftime("%B %d, %Y")
    except (ValueError, OSError):
        return "Invalid date"


def format_paper_summary(papers_data: Dict[str, Any]) -> str:
    """
    Format a brief summary of papers.
    
    Args:
        papers_data: Dictionary containing 'count' and 'papers' list
        
    Returns:
        Brief summary string
    """
    if not papers_data or 'papers' not in papers_data:
        return "No papers found."
    
    papers = papers_data['papers']
    count = papers_data.get('count', len(papers))
    
    result = f"Summary of {count} papers:\n\n"
    
    for i, paper in enumerate(papers, 1):
        title = paper.get('title', 'No title')
        authors = format_authors(paper.get('authors', []))
        venue = paper.get('venue_name', 'Unknown venue')
        citations = paper.get('citations', 0)
        
        result += f"{i}. {title}\n"
        result += f"   Authors: {authors}\n"
        result += f"   Venue: {venue} | Citations: {citations}\n\n"
    
    return result.strip()


def format_paper_titles_only(papers_data: Dict[str, Any]) -> str:
    """
    Format only paper titles for quick overview.
    
    Args:
        papers_data: Dictionary containing 'count' and 'papers' list
        
    Returns:
        List of paper titles
    """
    if not papers_data or 'papers' not in papers_data:
        return "No papers found."
    
    papers = papers_data['papers']
    count = papers_data.get('count', len(papers))
    
    result = f"Found {count} papers:\n\n"
    
    for i, paper in enumerate(papers, 1):
        title = paper.get('title', 'No title')
        result += f"{i}. {title}\n"
    
    return result.strip()

from typing import Dict, Any, List
from datetime import datetime


def format_author_list(raw_result: Dict[str, Any]) -> str:
    """Format author list - main entry point"""
    authors = raw_result.get("authors", [])
    count = raw_result.get("count", len(authors))
    params = raw_result.get("params", {})
    search_term = params.get("name", "")
    
    if not authors:
        return _format_empty_result(search_term, "author")
    
    if len(authors) == 1:
        return _format_single_author_details(authors[0], search_term)
    else:
        return _format_multiple_authors_list(authors, count, search_term)


def _format_single_author_details(author: Dict[str, Any], search_term: str) -> str:
    """Format single author details"""
    content = f"# 👤 Author Details\n\n"
    content += f"**Search Criteria**: {search_term}\n\n"
    
    content += f"## Basic Information\n"
    content += f"**Name**: {_safe_get_str(author, 'name', 'Unknown')}\n"
    content += f"**Affiliation**: {_safe_get_str(author, 'affiliation', 'N/A')}\n"
    
    email = _safe_get_str(author, 'email')
    if email:
        content += f"**Email**: {email}\n"
    
    content += f"\n## 📊 Academic Metrics\n"
    content += f"**Paper Count**: {_safe_get_int(author, 'paper_count')}\n"
    content += f"**Citation Count**: {_safe_get_int(author, 'citation_count')}\n"
    content += f"**H-index**: {_safe_get_int(author, 'h_index')}\n"
    
    interests = author.get('research_interests')
    if interests:
        content += f"\n## 🔬 Research Interests\n"
        if isinstance(interests, list):
            content += f"{', '.join(interests)}\n"
        else:
            content += f"{interests}\n"
    
    coauthors = author.get('coauthors', [])
    if coauthors:
        content += f"\n## 🤝 Collaboration Network ({len(coauthors)} co-authors)\n\n"
        
        sorted_coauthors = sorted(
            coauthors, 
            key=lambda x: _safe_get_int(x, 'collaboration_count'), 
            reverse=True
        )
        
        for i, coauthor in enumerate(sorted_coauthors[:10], 1):
            collab_count = _safe_get_int(coauthor, 'collaboration_count')
            coauthor_name = _safe_get_str(coauthor, 'name', 'Unknown')
            
            content += f"{i:2d}. **{coauthor_name}** - {collab_count} collaborations\n"
            
            affiliation = _safe_get_str(coauthor, 'affiliation')
            if affiliation:
                content += f"     Affiliation: {affiliation}\n"
            content += "\n"
        
        if len(coauthors) > 10:
            content += f"... and {len(coauthors) - 10} more co-authors\n"
    
    return content


def _format_multiple_authors_list(authors: List[Dict[str, Any]], count: int, search_term: str) -> str:
    """Format multiple authors list information"""
    content = _format_list_header("Author Search Results", count, search_term)
    
    for i, author in enumerate(authors, 1):
        name = _safe_get_str(author, 'name', 'Unknown Author')
        content += f"## {i}. {name}\n\n"
        
        content += _format_author_basic_info(author)
        
        interests = author.get('research_interests')
        if interests:
            if isinstance(interests, list):
                content += f"**Research Interests**: {', '.join(interests)}\n"
            else:
                content += f"**Research Interests**: {interests}\n"
        
        email = _safe_get_str(author, 'email')
        if email:
            content += f"**Email**: {email}\n"
        
        coauthors = author.get('coauthors', [])
        if coauthors:
            content += f"**Co-authors**: {len(coauthors)}"
            top_coauthors = sorted(coauthors, key=lambda x: _safe_get_int(x, 'collaboration_count'), reverse=True)[:3]
            if top_coauthors:
                names = [_safe_get_str(c, 'name') for c in top_coauthors if _safe_get_str(c, 'name')]
                if names:
                    content += f" (Main: {', '.join(names)})"
            content += "\n"
        
        content += "\n---\n\n"
    
    return content


def _format_author_basic_info(author: Dict[str, Any]) -> str:
    """Format basic author information"""
    content = ""
    content += f"**Affiliation**: {_safe_get_str(author, 'affiliation', 'N/A')}\n"
    content += f"**Paper Count**: {_safe_get_int(author, 'paper_count')}\n"
    content += f"**Citation Count**: {_safe_get_int(author, 'citation_count')}\n"
    content += f"**H-index**: {_safe_get_int(author, 'h_index')}\n"
    return content


def _format_list_header(title: str, count: int, search_term: str) -> str:
    """Format list header"""
    content = f"# 📋 {title}\n\n"
    content += f"**Search Criteria**: {search_term}\n"
    content += f"**Total Results**: {count}\n\n"
    return content


def _format_empty_result(search_term: str, result_type: str) -> str:
    """Format empty result"""
    return f"# ❌ No {result_type} found\n\n**Search Criteria**: {search_term}\n\nNo results found matching your search criteria.\n"


def _safe_get_str(data: Dict[str, Any], key: str, default: str = '') -> str:
    """Safely get string value from dictionary"""
    value = data.get(key, default)
    return str(value) if value is not None else default


def _safe_get_int(data: Dict[str, Any], key: str, default: int = 0) -> int:
    """Safely get integer value from dictionary"""
    value = data.get(key, default)
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


class AuthorFormatter:
    """Author data formatter - for backward compatibility"""
    
    def _format_author_papers(self, raw_result: Dict[str, Any], author_id: str, limit: int) -> str:
        """Format author papers"""
        papers = raw_result.get("papers", [])
        count = raw_result.get("count", len(papers))
        
        content = f"# 📄 Author Published Papers\n\n"
        content += f"**Total Papers**: {count}\n"
        content += f"**Displayed**: {len(papers)}\n\n"
        
        if not papers:
            content += "❌ No papers found for this author.\n"
            return content
        
        content += f"## 📋 Paper List\n\n"
        
        for i, paper in enumerate(papers, 1):
            title = self._safe_get_str(paper, 'title', 'Unknown Title')
            content += f"### {i}. {title}\n\n"
            
            published_at = self._safe_get_str(paper, 'published_at')
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%Y-%m-%d')
                    content += f"**Published Date**: {formatted_date}\n"
                except:
                    content += f"**Published Date**: {published_at}\n"
            
            author_order = self._safe_get_int(paper, 'author_order')
            if author_order > 0:
                if author_order == 1:
                    order_text = "First Author"
                elif author_order == 2:
                    order_text = "Second Author"
                elif author_order == 3:
                    order_text = "Third Author"
                else:
                    order_text = f"{author_order}th Author"
                content += f"**Author Order**: {order_text}\n"
            
            is_corresponding = paper.get('is_corresponding')
            if is_corresponding:
                content += f"**Corresponding Author**: ✅ Yes\n"
            else:
                content += f"**Corresponding Author**: ❌ No\n"
            
            content += "\n---\n\n"
        
        if count > len(papers):
            content += f"💡 **Note**: Author has {count} papers in total, showing first {len(papers)}.\n\n"
        
        first_author_count = sum(1 for p in papers if p.get('author_order') == 1)
        corresponding_count = sum(1 for p in papers if p.get('is_corresponding'))
        
        content += f"## 📊 Statistics\n\n"
        content += f"- **First Author Papers**: {first_author_count}\n"
        content += f"- **Corresponding Author Papers**: {corresponding_count}\n"
        
        year_stats = {}
        for paper in papers:
            published_at = paper.get('published_at', '')
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    year = dt.year
                    year_stats[year] = year_stats.get(year, 0) + 1
                except:
                    pass
        
        if year_stats:
            content += f"- **Distribution by Year**:\n"
            for year in sorted(year_stats.keys(), reverse=True):
                content += f"  - {year}: {year_stats[year]} papers\n"
        
        return content

    def _format_authors_result(self, raw_result: Dict[str, Any], search_term: str, search_type: str = "") -> str:
        """Unified author result formatting method - for backward compatibility"""
        return format_author_list(raw_result)

    def _format_single_author_details(self, author: Dict[str, Any], search_term: str) -> str:
        """Format single author details - for backward compatibility"""
        return _format_single_author_details(author, search_term)

    def _format_multiple_authors_list(self, authors: List[Dict[str, Any]], count: int, search_term: str) -> str:
        """Format multiple authors list information - for backward compatibility"""
        return _format_multiple_authors_list(authors, count, search_term)

    def _format_author_basic_info(self, author: Dict[str, Any]) -> str:
        """Format basic author information - for backward compatibility"""
        return _format_author_basic_info(author)

    def _format_list_header(self, title: str, count: int, search_term: str) -> str:
        """Format list header - for backward compatibility"""
        return _format_list_header(title, count, search_term)

    def _format_empty_result(self, search_term: str, result_type: str) -> str:
        """Format empty result - for backward compatibility"""
        return _format_empty_result(search_term, result_type)

    def _safe_get_str(self, data: Dict[str, Any], key: str, default: str = '') -> str:
        """Safely get string value from dictionary - for backward compatibility"""
        return _safe_get_str(data, key, default)

    def _safe_get_int(self, data: Dict[str, Any], key: str, default: int = 0) -> int:
        """Safely get integer value from dictionary - for backward compatibility"""
        return _safe_get_int(data, key, default)

"""
Response Integrator - Integrate execution results and generate final response
"""
from typing import Dict, Any, List
from models.intent import IntentAnalysisResult, IntentType
from services.llm_service import LLMService
from prompts.response_prompts import ResponsePrompts
from utils.logger import get_logger

logger = get_logger(__name__)

class ResponseIntegrator:
    """Response Integrator Class"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.prompts = ResponsePrompts()
    
    async def integrate(self, 
                       query: str,
                       intent_result: IntentAnalysisResult,
                       execution_results: Dict[str, Any],
                       context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Integrate execution results and generate final response"""
        try:
            logger.info("Starting response integration", intent=intent_result.primary_intent.type.value)
            
            # 1. Data preprocessing
            processed_data = self._process_execution_results(execution_results)
            
            # 2. Select response strategy based on intent type
            response_strategy = self._select_response_strategy(intent_result.primary_intent.type)
            
            # 3. Generate structured response
            structured_response = await self._generate_structured_response(
                query, intent_result, processed_data, response_strategy
            )
            
            # 4. Generate natural language response
            natural_response = await self._generate_natural_response(
                query, structured_response, intent_result
            )
            
            # 5. Add metadata and suggestions
            final_response = self._enhance_response(
                natural_response, structured_response, intent_result
            )
            
            logger.info("Response integration completed")
            return final_response
            
        except Exception as e:
            logger.error("Response integration failed", error=str(e))
            return self._create_error_response(str(e))
    
    def _process_execution_results(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process and clean execution results - preserve MCP structure information"""
        processed = {}
        
        for task_id, result in execution_results.items():
            if isinstance(result, dict) and not result.get("error"):
                if "content" in result:
                    content = result["content"]
                    
                    if isinstance(content, list) and content:
                        first_item = content[0]
                        if isinstance(first_item, dict) and first_item.get("type") == "text":
                            # Preserve MCP structure while providing convenient access
                            processed[task_id] = {
                                "mcp_format": True,
                                "content_type": "text",
                                "text_content": first_item.get("text", ""),
                                "raw_mcp_content": content,
                                "full_result": result
                            }
                        else:
                            # Other types of MCP content
                            processed[task_id] = {
                                "mcp_format": True,
                                "content_type": first_item.get("type", "unknown"),
                                "content_data": first_item,
                                "raw_mcp_content": content,
                                "full_result": result
                            }
                    else:
                        # Content is not a list or is empty
                        processed[task_id] = {
                            "mcp_format": True,
                            "content_type": "invalid",
                            "content_data": content,
                            "full_result": result
                        }
                else:
                    # No content field
                    processed[task_id] = {
                        "mcp_format": False,
                        "content_data": result
                    }
            else:
                logger.warning("Task result contains error", 
                            task_id=task_id, 
                            error=result.get("error") if isinstance(result, dict) else "Invalid result format")
        
        return processed
    
    def _select_response_strategy(self, intent_type: IntentType) -> str:
        """Select response strategy based on intent type"""
        strategy_mapping = {
        # Paper related
            IntentType.SEARCH_PAPERS: "paper_list",
            IntentType.GET_PAPER_DETAILS: "paper_detail",
            IntentType.GET_PAPER_CITATIONS: "citation_analysis",
            
            IntentType.SEARCH_AUTHORS: "author_list",
            IntentType.GET_AUTHOR_DETAILS: "author_detail",  # Although the value is "search_authors", the strategy can be different
            IntentType.GET_AUTHOR_PAPERS: "author_papers",

            # Trend analysis
            IntentType.GET_TRENDING_PAPERS: "trending_papers",
            IntentType.GET_TOP_KEYWORDS: "keyword_analysis",

            # IntentType.PAPER_REVIEW: "review_report",
            # IntentType.PAPER_GENERATION: "generation_guide",
            
            # General chat
            IntentType.GENERAL_CHAT: "general_chat",
            
            # Unknown intent
            IntentType.UNKNOWN: "clarification"
        }
        
        return strategy_mapping.get(intent_type, "general")
    
    async def _generate_structured_response(self,
                                          query: str,
                                          intent_result: IntentAnalysisResult,
                                          processed_data: Dict[str, Any],
                                          strategy: str) -> Dict[str, Any]:
        """Generate structured response"""
        structured_response = {
            "strategy": strategy,
            "data": processed_data,
            "summary": {},
            "insights": [],
            "recommendations": []
        }
        
        if strategy == "paper_list":
            structured_response.update(self._structure_paper_list_response(processed_data))
        elif strategy == "paper_detail":
            structured_response.update(self._structure_paper_detail_response(processed_data))
        elif strategy == "author_list":
            structured_response.update(self._structure_author_list_response(processed_data))
        elif strategy == "author_detail":
            structured_response.update(self._structure_author_detail_response(processed_data))
        elif strategy == "network_analysis":
            structured_response.update(self._structure_network_analysis_response(processed_data))
        elif strategy == "trending_papers":
            structured_response.update(self._structure_trend_report_response(processed_data))
        elif strategy == "keyword_analysis":
            structured_response.update(self._structure_keyword_analysis_response(processed_data))
        elif strategy == "landscape_overview":
            structured_response.update(self._structure_landscape_response(processed_data))
        elif strategy == "review_report":
            structured_response.update(self._structure_review_response(processed_data))
        elif strategy == "generation_guide":
            structured_response.update(self._structure_generation_response(processed_data))
        
        return structured_response
    
    def _structure_paper_list_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure paper list response - handle MCP format and JSON string data"""
        papers = []
        total_count = 0
        text_content = ""
        paper_count = 0
        
        for task_result in data.values():
            if isinstance(task_result, dict):
                if task_result.get("mcp_format") and task_result.get("content_type") == "text":
                    # Get JSON string from text_content
                    text_content = task_result.get("text_content", "")
                    
                    if text_content:
                        try:
                            # Try to parse JSON string
                            import json
                            json_data = json.loads(text_content)
                            
                            if isinstance(json_data, dict):
                                # Extract paper data
                                papers.extend(json_data.get("papers", []))
                                total_count = json_data.get("count", len(papers))
                                paper_count = len(papers)
                                
                                logger.info("Successfully parsed JSON from text_content", 
                                        papers_count=len(papers), 
                                        total_count=total_count)
                            else:
                                logger.warning("JSON data is not a dictionary", data_type=type(json_data).__name__)
                                
                        except json.JSONDecodeError as e:
                            logger.warning("Failed to parse JSON from text_content", error=str(e))
                            # Fallback to text parsing
                            parsed_papers = self._parse_paper_text_result(text_content)
                            if parsed_papers.get("papers"):
                                papers = parsed_papers["papers"]
                                total_count = parsed_papers.get("total_count", 0)
                                paper_count = len(papers)
                    
                elif "papers" in task_result:
                    # Standard structured paper data
                    papers.extend(task_result["papers"])
                    total_count = task_result.get("total", len(papers))
                    paper_count = len(papers)
                    
            elif isinstance(task_result, str):
                # Backward compatibility: directly a string
                text_content = task_result
                try:
                    # Try to parse as JSON
                    import json
                    json_data = json.loads(task_result)
                    
                    if isinstance(json_data, dict):
                        papers.extend(json_data.get("papers", []))
                        total_count = json_data.get("count", len(papers))
                        paper_count = len(papers)
                    else:
                        # Not a dictionary, fallback to text parsing
                        raise json.JSONDecodeError("Not a dictionary", task_result, 0)
                        
                except json.JSONDecodeError:
                    # Not JSON, parse as text
                    import re
                    
                    # Extract total count
                    total_match = re.search(r'\*\*Total\*\*:\s*(\d+)', task_result)
                    if total_match:
                        total_count = int(total_match.group(1))
                    
                    # Count papers
                    paper_sections = re.findall(r'###\s*\d+\.', task_result)
                    paper_count = len(paper_sections)
        
        # Extract more detailed statistics
        if papers:
            top_authors = self._extract_top_authors(papers)
            publication_years = self._extract_publication_years(papers)
            avg_citations = sum(paper.get("citations", 0) for paper in papers) / len(papers) if papers else 0
            top_venues = self._extract_top_venues(papers)
        else:
            top_authors = []
            publication_years = []
            avg_citations = 0
            top_venues = []
        
        return {
            "summary": {
                "total_papers": total_count,
                "returned_papers": paper_count,
                "data_format": "json" if papers else ("text" if text_content else "unknown"),
                "has_structured_papers": len(papers) > 0,
                "has_text_content": bool(text_content),
                "top_authors": top_authors[:5],
                "publication_years": publication_years[:5],
                "average_citations": round(avg_citations, 1),
                "top_venues": top_venues[:3]
            },
            "insights": [
                f"Found {total_count} related papers, successfully retrieved detailed information for {len(papers)} papers",
                f"Average citations: {round(avg_citations, 1)} times" if papers else "Retrieved paper search results",
                f"Main authors include: {', '.join(top_authors[:3])}" if top_authors else "Contains work from multiple researchers",
                f"Publication year range: {min(publication_years)}-{max(publication_years)}" if len(publication_years) > 1 else f"Mainly published in {publication_years[0]}" if publication_years else "Year information complete",
                f"Main publication venues: {', '.join(top_venues[:2])}" if top_venues else "Covers multiple academic journals and conferences"
            ],
            "recommendations": [
                "Suggest viewing papers with highest citations to understand core research",
                "Can further analyze author collaboration networks and research teams",
                "Suggest following latest published papers to track frontier progress",
                "Can filter high-quality papers by publication venue"
            ]
        }
 
    def _structure_paper_detail_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure paper detail response - handle actual MCP data format"""
        paper_details = {}
        papers_found = []
        
        for task_result in data.values():
            if isinstance(task_result, dict):
                # Handle MCP format response
                if task_result.get("mcp_format") and task_result.get("content_type") == "text":
                    text_content = task_result.get("text_content", "")
                    try:
                        import json
                        json_data = json.loads(text_content)
                        
                        # Handle new data structure: paper_searches
                        if isinstance(json_data, dict) and "paper_searches" in json_data:
                            paper_searches = json_data["paper_searches"]
                            
                            # Extract all candidate papers
                            for search in paper_searches:
                                if "candidates" in search:
                                    papers_found.extend(search["candidates"])
                            
                            # If papers found, use first one as details
                            if papers_found:
                                paper_details = papers_found[0]
                                break
                                
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse paper details JSON")
                        continue
                        
                # Handle direct paper data format
                elif "paper" in task_result:
                    paper_details = task_result["paper"]
                    break
                elif "papers" in task_result and task_result["papers"]:
                    # If it's a paper list, take the first one
                    paper_details = task_result["papers"][0]
                    break
                elif "candidates" in task_result and task_result["candidates"]:
                    # Directly a candidate list
                    paper_details = task_result["candidates"][0]
                    break
        
        # If no paper details found, return empty structure
        if not paper_details:
            return {
                "summary": {
                    "title": "",
                    "authors": [],
                    "publication_year": "",
                    "citation_count": 0,
                    "venue": "",
                    "doi": "",
                    "abstract": "",
                    "keywords": [],
                    "url": ""
                },
                "insights": ["Paper details not found"],
                "recommendations": [
                    "Please check if paper ID or title is correct",
                    "Try using different search keywords",
                    "Confirm if paper exists in database"
                ]
            }
        
        # Extract paper information - adapt to new data structure
        title = paper_details.get("title", "")
        
        # Handle author information - new format is object array
        authors = []
        authors_data = paper_details.get("authors", [])
        for author in authors_data:
            if isinstance(author, dict):
                author_name = author.get("name", "")
                if author_name:
                    authors.append(author_name)
            elif isinstance(author, str):
                authors.append(author)
        
        # Handle publication year - new format is timestamp
        publication_year = ""
        if "published_at" in paper_details:
            try:
                import datetime
                timestamp = paper_details["published_at"]
                publication_year = datetime.datetime.fromtimestamp(timestamp).year
            except:
                publication_year = "Unknown"
        elif "year" in paper_details:
            publication_year = paper_details["year"]
        
        citation_count = paper_details.get("citations", 0)
        venue = paper_details.get("venue_name", paper_details.get("venue", ""))
        doi = paper_details.get("doi", "")
        abstract = paper_details.get("abstract", "")
        keywords = paper_details.get("keywords", [])
        url = paper_details.get("url", "")
        references_count = paper_details.get("references_count", 0)
        likes_count = paper_details.get("likes_count", 0)
        
        # Analyze paper impact
        impact_level = "Low"
        if citation_count >= 100:
            impact_level = "Very High"
        elif citation_count >= 50:
            impact_level = "High"
        elif citation_count >= 10:
            impact_level = "Medium"
        elif citation_count >= 1:
            impact_level = "Low"
        else:
            impact_level = "Newly Published"
        
        # Analyze research fields
        research_fields = []
        for keyword in keywords:
            if isinstance(keyword, str):
                # Handle common subject classifications
                if keyword.startswith("cs."):
                    field_mapping = {
                        "cs.CR": "Cryptography and Security",
                        "cs.AI": "Artificial Intelligence",
                        "cs.LG": "Machine Learning",
                        "cs.CV": "Computer Vision",
                        "cs.CL": "Computational Linguistics",
                        "cs.DB": "Databases",
                        "cs.DC": "Distributed Computing",
                        "cs.SE": "Software Engineering"
                    }
                    research_fields.append(field_mapping.get(keyword, keyword))
                else:
                    research_fields.append(keyword)
        
        return {
            "summary": {
                "title": title,
                "authors": authors,
                "publication_year": publication_year,
                "citation_count": citation_count,
                "venue": venue,
                "doi": doi,
                "abstract": abstract[:500] + "..." if len(abstract) > 500 else abstract,  # Truncate abstract
                "keywords": keywords,
                "url": url,
                "references_count": references_count,
                "likes_count": likes_count,
                "research_fields": research_fields,
                "impact_level": impact_level
            },
            "insights": [
                f"Paper '{title}' was published in {publication_year}" if title and publication_year else "Paper information retrieved successfully",
                f"Cited {citation_count} times, academic impact is {impact_level}" if citation_count > 0 else "No citation data available",
                f"Authors include: {', '.join(authors[:3])}" + (" et al." if len(authors) > 3 else "") if authors else "Author information complete",
                f"Published in {venue}" if venue else "Journal information available",
                f"Research fields: {', '.join(research_fields[:3])}" if research_fields else "Keywords information complete",
                f"Abstract length: {len(abstract)} characters" if abstract else "Abstract information available",
                f"References: {references_count} papers" if references_count > 0 else "Reference information available",
                f"Received {likes_count} likes" if likes_count > 0 else "Social interaction data available"
            ],
            "recommendations": [
                "View complete abstract and content" if url else "Get paper access link",
                "Analyze paper citation network and impact" if citation_count > 0 else "Follow future citations of this paper",
                f"Learn about author {authors[0]}'s other research work" if authors else "Explore related authors' research",
                f"Explore research in {research_fields[0]} field" if research_fields else "Dive deeper into related research fields",
                "Check paper reference list" if references_count > 0 else "Analyze paper theoretical foundation",
                f"Follow latest research in {venue} journal" if venue else "Learn about journal impact factor",
                "Download and read full paper" if url else "Get detailed paper information"
            ]
        }

    
    def _structure_author_list_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure author list response"""
        authors = []
        
        for task_result in data.values():
            if isinstance(task_result, dict) and "authors" in task_result:
                authors.extend(task_result["authors"])
        
        return {
            "summary": {
                "total_authors": len(authors),
                "top_institutions": self._extract_top_institutions(authors),
                "research_areas": self._extract_research_areas(authors)
            },
            "insights": [
                f"Found {len(authors)} related authors",
                f"Main institutions: {', '.join(self._extract_top_institutions(authors)[:3])}",
                f"Research field distribution: {self._get_area_distribution(authors)}"
            ],
            "recommendations": [
                "Check detailed information of productive authors",
                "Analyze collaboration networks between authors",
                "Focus on research priorities of different institutions"
            ]
        }
    
    def _structure_author_detail_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure author detail response"""
        author_details = {}
        
        for task_result in data.values():
            if isinstance(task_result, dict):
                # Handle MCP format response
                if task_result.get("mcp_format") and task_result.get("content_type") == "text":
                    text_content = task_result.get("text_content", "")
                    try:
                        import json
                        json_data = json.loads(text_content)
                        if isinstance(json_data, dict) and "authors" in json_data:
                            authors = json_data["authors"]
                            if authors and len(authors) > 0:
                                author_details = authors[0]  # Take first author's details
                                break
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse author details JSON")
                        continue
                # Handle direct author data
                elif "authors" in task_result:
                    authors = task_result["authors"]
                    if authors and len(authors) > 0:
                        author_details = authors[0]
                        break
                # Handle single author object
                elif "name" in task_result or "id" in task_result:
                    author_details = task_result
                    break
        
        if not author_details:
            return {
                "summary": {},
                "insights": ["Author details not found"],
                "recommendations": ["Please check if author name is correct", "Try different search keywords"]
            }
        
        # Extract author basic information
        author_name = author_details.get("name", "Unknown Author")
        affiliation = author_details.get("affiliation", "")
        email = author_details.get("email", "")
        h_index = author_details.get("h_index", 0)
        paper_count = author_details.get("paper_count", 0)
        citation_count = author_details.get("citation_count", 0)
        research_interests = author_details.get("research_interests", [])
        
        # Handle coauthor information
        coauthors = author_details.get("coauthors", [])
        coauthor_count = len(coauthors)
        
        # Analyze coauthor institution distribution
        coauthor_institutions = []
        collaboration_strength = {}
        
        for coauthor in coauthors:
            if isinstance(coauthor, dict):
                # Collect coauthor institutions
                coauthor_affiliation = coauthor.get("affiliation", "")
                if coauthor_affiliation and coauthor_affiliation not in coauthor_institutions:
                    coauthor_institutions.append(coauthor_affiliation)
                
                # Analyze collaboration strength
                coauthor_name = coauthor.get("name", "")
                collaboration_count = coauthor.get("collaboration_count", 0)
                if coauthor_name and collaboration_count > 0:
                    collaboration_strength[coauthor_name] = collaboration_count
        
        # Find most frequent collaborators
        top_collaborators = sorted(collaboration_strength.items(), 
                                key=lambda x: x[1], reverse=True)[:5]
        
        # Analyze research activity
        activity_level = "Low"
        if paper_count >= 20:
            activity_level = "High"
        elif paper_count >= 10:
            activity_level = "Medium"
        elif paper_count >= 5:
            activity_level = "Medium-Low"
        
        # Analyze impact
        impact_level = "Low"
        if h_index >= 20:
            impact_level = "Very High"
        elif h_index >= 10:
            impact_level = "High"
        elif h_index >= 5:
            impact_level = "Medium"
        elif h_index >= 2:
            impact_level = "Relatively High"
        
        return {
            "summary": {
                "author_name": author_name,
                "affiliation": affiliation,
                "email": email,
                "h_index": h_index,
                "paper_count": paper_count,
                "citation_count": citation_count,
                "coauthor_count": coauthor_count,
                "research_interests": research_interests if research_interests else [],
                "top_collaborators": [collab[0] for collab in top_collaborators],
                "collaboration_institutions": coauthor_institutions[:5],  # Top 5 institutions
                "activity_level": activity_level,
                "impact_level": impact_level
            },
            "insights": [
                f"Author {author_name} has published {paper_count} papers",
                f"H-index is {h_index}, academic impact is {impact_level}",
                f"Total citations: {citation_count} times" if citation_count > 0 else "Citation information not available",
                f"Has collaborations with {coauthor_count} scholars" if coauthor_count > 0 else "No coauthor information",
                f"Main collaboration institutions: {', '.join(coauthor_institutions[:3])}" if coauthor_institutions else "Institution information incomplete",
                f"Most frequent collaborators: {', '.join([collab[0] for collab in top_collaborators[:3]])}" if top_collaborators else "Collaboration relationship information not available",
                f"Research activity level: {activity_level}"
            ],
            "recommendations": [
                "View author's paper list" if paper_count > 0 else "Search for author's related papers",
                "Analyze author's collaboration network" if coauthor_count > 0 else "Explore potential collaboration relationships",
                "Understand author's research trajectory and trends",
                "View author's contributions in specific research areas",
                "Analyze author's relationships with other notable scholars" if top_collaborators else "Explore author's academic influence",
                f"Follow other researchers at {affiliation}" if affiliation else "Learn about author's academic background"
            ]
        }


    def _structure_network_analysis_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure network analysis response"""
        network_data = {}
        
        for task_result in data.values():
            if isinstance(task_result, dict) and ("nodes" in task_result or "edges" in task_result):
                network_data = task_result
                break
        
        nodes_count = len(network_data.get("nodes", []))
        edges_count = len(network_data.get("edges", []))
        
        return {
            "summary": {
                "nodes_count": nodes_count,
                "edges_count": edges_count,
                "network_density": edges_count / (nodes_count * (nodes_count - 1)) if nodes_count > 1 else 0,
                "key_nodes": self._identify_key_nodes(network_data)
            },
            "insights": [
                f"Network contains {nodes_count} nodes and {edges_count} edges",
                f"Network density is {edges_count / (nodes_count * (nodes_count - 1)):.3f}" if nodes_count > 1 else "Network density cannot be calculated",
                f"Key nodes: {', '.join(self._identify_key_nodes(network_data)[:3])}"
            ],
            "recommendations": [
                "Focus on core nodes in the network",
                "Analyze network community structure",
                "Explore shortest paths between nodes"
            ]
        }
    
    def _structure_trend_report_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure trend report response - Simplified version"""
        trending_papers = []
        total_count = 0
        time_window = ""
        
        # Extract data
        for task_result in data.values():
            if isinstance(task_result, dict):
                if task_result.get("mcp_format") and task_result.get("content_type") == "text":
                    text_content = task_result.get("text_content", "")
                    try:
                        import json
                        json_data = json.loads(text_content)
                        
                        if isinstance(json_data, dict):
                            trending_papers = json_data.get("trending_papers", [])
                            total_count = json_data.get("count", len(trending_papers))
                            time_window = json_data.get("time_window", "")
                            break
                            
                    except json.JSONDecodeError:
                        continue
                        
                elif "trending_papers" in task_result:
                    trending_papers = task_result["trending_papers"]
                    total_count = task_result.get("count", len(trending_papers))
                    time_window = task_result.get("time_window", "")
                    break
        
        if not trending_papers:
            return {
                "summary": {
                    "total_papers": 0,
                    "time_window": time_window or "Unknown"
                },
                "insights": ["No trending papers found"],
                "recommendations": ["Try adjusting search criteria"]
            }
        
        # Simple statistics
        total_citations = sum(paper.get("citations", 0) for paper in trending_papers)
        avg_citations = round(total_citations / len(trending_papers), 1) if trending_papers else 0
        
        # Extract authors (first authors of top 3 papers)
        top_authors = []
        for paper in trending_papers[:3]:
            authors = paper.get("authors", [])
            if authors:
                first_author = authors[0] if isinstance(authors[0], str) else authors[0].get("name", "")
                if first_author:
                    top_authors.append(first_author)
        
        # Extract keywords
        keywords = []
        for paper in trending_papers:
            paper_keywords = paper.get("keywords", [])
            keywords.extend(paper_keywords)
        
        # Deduplicate and take top 3
        unique_keywords = list(dict.fromkeys(keywords))[:3]
        
        # Hottest paper
        hottest_paper = ""
        if trending_papers:
            # Sort by popularity_score, if not available then by citations
            sorted_papers = sorted(trending_papers, 
                                key=lambda x: x.get("popularity_score", x.get("citations", 0)), 
                                reverse=True)
            hottest_paper = sorted_papers[0].get("title", "")
        
        return {
            "summary": {
                "total_papers": total_count,
                "time_window": time_window,
                "average_citations": avg_citations,
                "top_authors": top_authors,
                "keywords": unique_keywords,
                "hottest_paper": hottest_paper
            },
            "insights": [
                f"Found {total_count} trending papers" + (f" (Time window: {time_window})" if time_window else ""),
                f"Average citations: {avg_citations}" if avg_citations > 0 else "Includes recently published papers",
                f"Key authors: {', '.join(top_authors)}" if top_authors else "Covers multiple researchers",
                f"Popular keywords: {', '.join(unique_keywords)}" if unique_keywords else "Covers multiple research areas",
                f"Hottest paper: '{hottest_paper[:50]}...'" if len(hottest_paper) > 50 else f"Hottest paper: '{hottest_paper}'" if hottest_paper else "Complete popularity ranking"
            ],
            "recommendations": [
                "Review papers with highest citations to understand research hotspots",
                "Follow active authors' latest research developments",
                "Explore research areas related to popular keywords",
                "Analyze research methods and innovations in trending papers"
            ]
        }
    
    def _structure_keyword_analysis_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure keyword analysis response - Process MCP format data"""
        keywords = []
        total_count = 0
        text_content = ""
        
        for task_result in data.values():
            if isinstance(task_result, dict):
                if task_result.get("mcp_format") and task_result.get("content_type") == "text":
                    # Get JSON string from text_content
                    text_content = task_result.get("text_content", "")
                    
                    if text_content:
                        try:
                            import json
                            json_data = json.loads(text_content)
                            
                            if isinstance(json_data, dict):
                                keywords = json_data.get("keywords", [])
                                total_count = json_data.get("count", len(keywords))
                                
                                logger.info("Successfully parsed keywords from text_content", 
                                        keywords_count=len(keywords), 
                                        total_count=total_count)
                            else:
                                logger.warning("JSON data is not a dictionary", data_type=type(json_data).__name__)
                                
                        except json.JSONDecodeError as e:
                            logger.warning("Failed to parse JSON from text_content", error=str(e))
                
                elif "keywords" in task_result:
                    # Standard structured keyword data
                    keywords = task_result["keywords"]
                    total_count = task_result.get("count", len(keywords))
        
        # If no keyword data found
        if not keywords:
            return {
                "summary": {
                    "total_keywords": 0,
                    "data_format": "empty"
                },
                "insights": ["No popular keywords found"],
                "recommendations": ["Try specifying a specific research field", "Check if search criteria are correct"]
            }
        
        # Extract statistics
        total_papers = sum(kw.get("paper_count", 0) for kw in keywords)
        avg_papers_per_keyword = round(total_papers / len(keywords), 1) if keywords else 0
        
        # Find the most popular keyword
        top_keyword = max(keywords, key=lambda x: x.get("paper_count", 0)) if keywords else {}
        top_keyword_name = top_keyword.get("keyword", "")
        top_keyword_count = top_keyword.get("paper_count", 0)
        
        # Categorize keywords (simple domain classification)
        cs_keywords = [kw for kw in keywords if kw.get("keyword", "").startswith("cs.")]
        physics_keywords = [kw for kw in keywords if kw.get("keyword", "").startswith("physics.")]
        other_keywords = [kw for kw in keywords if not kw.get("keyword", "").startswith(("cs.", "physics."))]
        
        # Extract top 5 popular keywords
        sorted_keywords = sorted(keywords, key=lambda x: x.get("paper_count", 0), reverse=True)
        top_5_keywords = [(kw.get("keyword", ""), kw.get("paper_count", 0)) for kw in sorted_keywords[:5]]
        
        return {
            "summary": {
                "total_keywords": total_count,
                "returned_keywords": len(keywords),
                "total_papers": total_papers,
                "avg_papers_per_keyword": avg_papers_per_keyword,
                "top_keyword": top_keyword_name,
                "top_keyword_count": top_keyword_count,
                "cs_keywords_count": len(cs_keywords),
                "physics_keywords_count": len(physics_keywords),
                "other_keywords_count": len(other_keywords),
                "top_5_keywords": top_5_keywords
            },
            "insights": [
                f"Found {total_count} popular keywords, covering {total_papers} papers",
                f"Most popular keyword: {top_keyword_name} ({top_keyword_count} papers)" if top_keyword_name else "Even distribution of keyword popularity",
                f"Average {avg_papers_per_keyword} papers per keyword",
                f"Computer Science field: {len(cs_keywords)} keywords" if cs_keywords else "Few Computer Science keywords",
                f"Physics field: {len(physics_keywords)} keywords" if physics_keywords else "Few Physics keywords",
                f"Other fields: {len(other_keywords)} keywords" if other_keywords else "Mainly focused on Computer Science and Physics"
            ],
            "recommendations": [
                f"Deep dive into papers related to popular keyword '{top_keyword_name}'" if top_keyword_name else "Focus on keywords with more papers",
                "Compare keyword trends across different fields",
                "Analyze research opportunities in interdisciplinary keywords",
                "Pay attention to emerging keywords' potential"
            ]
        }

    async def _generate_natural_response(self,
                                    query: str,
                                    structured_response: Dict[str, Any],
                                    intent_result: IntentAnalysisResult) -> str:
        """Generate natural language response"""
        try:
            # Prepare research data
            research_data = {
                "strategy": structured_response.get("strategy"),
                "summary": structured_response.get("summary", {}),
                "insights": structured_response.get("insights", []),
                "recommendations": structured_response.get("recommendations", []),
                "intent_type": intent_result.primary_intent.type.value,
                "confidence": intent_result.primary_intent.confidence
            }
            
            # Call LLM service to generate academic response
            try:
                natural_response = await self.llm_service.generate_academic_response(
                    user_query=query,
                    research_data=research_data,
                    conversation_history=None
                )
                
                if isinstance(natural_response, str) and natural_response.strip():
                    logger.info("LLM generated academic response successfully")
                    return natural_response.strip()
                else:
                    logger.warning("LLM generated empty response")
                    
            except Exception as llm_error:
                logger.warning("LLM academic response generation failed", error=str(llm_error))

            # Fallback: Use basic generate_response method
            try:
                messages = [
                    {
                        "role": "system",
                        "content": "You are a professional academic research assistant. Please generate friendly and professional responses based on user queries and research data."
                    },
                    {
                        "role": "user",
                        "content": f"User query: {query}\n\nResearch data: {research_data}\n\nPlease generate a natural Chinese response:"
                    }
                ]
                
                natural_response = await self.llm_service.generate_response(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                if isinstance(natural_response, str) and natural_response.strip():
                    logger.info("LLM basic response generation successful")
                    return natural_response.strip()
                    
            except Exception as basic_error:
                logger.warning("LLM basic response generation failed", error=str(basic_error))

            # Finally use fallback response
            logger.info("Using fallback response generation")
            return self._create_fallback_response(structured_response)
            
        except Exception as e:
            logger.error("Natural response generation failed", error=str(e))
            return self._create_fallback_response(structured_response)

    
    def _build_response_prompt(self,
                             query: str,
                             structured_response: Dict[str, Any],
                             intent_result: IntentAnalysisResult) -> str:
        """Build response generation prompt"""
        strategy = structured_response.get("strategy", "general")
        base_prompt = self.prompts.get_response_generation_prompt(strategy)
        
        context = f"""
                    User query: {query}
                    Intent type: {intent_result.primary_intent.type.value}
                    Data summary: {structured_response.get('summary', {})}
                    Key insights: {structured_response.get('insights', [])}
                    Recommendations: {structured_response.get('recommendations', [])}
                    """
        
        return f"{base_prompt}\n\n{context}"
    
    def _create_fallback_response(self, structured_response: Dict[str, Any]) -> str:
        """Create fallback response"""
        summary = structured_response.get("summary", {})
        insights = structured_response.get("insights", [])
        
        response_parts = ["Based on your query, I found the following information:"]
        
        if summary:
            response_parts.append(f"Data overview: {summary}")
        
        if insights:
            response_parts.append("Key findings:")
            for insight in insights[:3]:
                response_parts.append(f"• {insight}")
        
        return "\n\n".join(response_parts)
    
    def _enhance_response(self,
                        natural_response: str,
                        structured_response: Dict[str, Any],
                        intent_result: IntentAnalysisResult) -> Dict[str, Any]:
        """Enhance response, add metadata and recommendations"""
        
        # Ensure natural_response is a string
        if not isinstance(natural_response, str):
            natural_response = str(natural_response)
        
        return {
            "content": natural_response,
            "metadata": {
                "intent_type": intent_result.primary_intent.type.value,
                "confidence": intent_result.primary_intent.confidence,
                "strategy": structured_response.get("strategy"),
                "data_sources": list(structured_response.get("data", {}).keys())
            },
            "structured_data": structured_response.get("summary", {}),
            "insights": structured_response.get("insights", []),
            "recommendations": structured_response.get("recommendations", []),
            "follow_up_suggestions": self._generate_follow_up_suggestions(intent_result)
        }
    
    def _generate_follow_up_suggestions(self, intent_result: IntentAnalysisResult) -> List[str]:
        """Generate follow-up suggestions"""
        suggestions = []
        intent_type = intent_result.primary_intent.type
        
        if intent_type == IntentType.SEARCH_PAPERS:
            suggestions = [
                "View detailed information of specific papers",
                "Analyze author's other works",
                "Explore related research trends"
            ]
        elif intent_type == IntentType.SEARCH_AUTHORS:
            suggestions = [
                "View author's detailed profile",
                "Analyze author's collaboration network",
                "Understand author's research trajectory"
            ]
        elif intent_type == IntentType.RESEARCH_TRENDS:
            suggestions = [
                "Deep dive into specific research directions",
                "Compare trends across different time periods",
                "Explore cross-domain research opportunities"
            ]
        elif intent_type == IntentType.GENERAL_CHAT:
            suggestions = [
                "You can ask questions about academic research",
                "Try searching for papers on specific topics",
                "Look up researchers of interest"
            ]
        else:
            suggestions = [
                "Please provide more specific queries",
                "Try using different keywords",
                "Describe the research field you want to learn about"
            ]
        
        return suggestions
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "content": f"Sorry, encountered an issue while processing your request: {error_message}. Please try again later or rephrase your question.",
            "metadata": {
                "error": True,
                "error_message": error_message
            },
            "recommendations": [
                "Please check if your query is clear and specific",
                "Try using different keywords",
                "Contact technical support if the problem persists"
            ]
        }
    
    # Helper methods
    def _extract_top_venues(self, papers: List[Dict]) -> List[str]:
        """Extract popular venues/conferences"""
        venue_counts = {}
        for paper in papers:
            venue = paper.get("venue_name", "")
            if venue:
                venue_counts[venue] = venue_counts.get(venue, 0) + 1
    
        return sorted(venue_counts.keys(), key=lambda x: venue_counts[x], reverse=True)





    def _extract_top_authors(self, papers: List[Dict]) -> List[str]:
        """Extract popular authors - Handle new author data structure"""
        author_counts = {}
        for paper in papers:
            authors = paper.get("authors", [])
            for author in authors:
                if isinstance(author, dict):
                    # New format: {"id": "...", "name": "..."}
                    author_name = author.get("name", "")
                elif isinstance(author, str):
                    # Old format: directly string
                    author_name = author
                else:
                    continue
                    
                if author_name:
                    author_counts[author_name] = author_counts.get(author_name, 0) + 1
    
        return sorted(author_counts.keys(), key=lambda x: author_counts[x], reverse=True)    
    

    def _extract_publication_years(self, papers: List[Dict]) -> List[int]:
        """Extract publication years - Handle timestamp format"""
        years = []
        for paper in papers:
            if "published_at" in paper:
                # Timestamp format
                timestamp = paper["published_at"]
                try:
                    import datetime
                    year = datetime.datetime.fromtimestamp(timestamp).year
                    years.append(year)
                except:
                    continue
            elif "year" in paper:
                # Direct year format
                years.append(paper["year"])
        
        return sorted(set(years), reverse=True)
    
    def _get_year_distribution(self, papers: List[Dict]) -> str:
        """Get year distribution description"""
        years = self._extract_publication_years(papers)
        if not years:
            return "Year information not available"
        
        if len(years) == 1:
            return f"{years[0]} year"
        else:
            return f"{years[-1]}-{years[0]} years"
    
    def _extract_top_institutions(self, authors: List[Dict]) -> List[str]:
        """Extract popular institutions"""
        institutions = []
        for author in authors:
            if "affiliation" in author:
                institutions.append(author["affiliation"])
        
        return list(set(institutions))[:5]  # Return top 5 institutions
    
    def _extract_research_areas(self, authors: List[Dict]) -> List[str]:
        """Extract research areas"""
        areas = []
        for author in authors:
            if "research_areas" in author:
                areas.extend(author["research_areas"])
        
        return list(set(areas))[:5]  # Return top 5 areas
    
    def _get_area_distribution(self, authors: List[Dict]) -> str:
        """Get research area distribution description"""
        areas = self._extract_research_areas(authors)
        if not areas:
            return "Area information not available"
        
        return f"{', '.join(areas[:3])}" + (" etc." if len(areas) > 3 else "")
    
    def _identify_key_nodes(self, network_data: Dict[str, Any]) -> List[str]:
        """Identify key nodes in the network"""
        nodes = network_data.get("nodes", [])
        if not nodes:
            return []
        
        # Simple sorting by degree (if degree information exists)
        if isinstance(nodes[0], dict) and "degree" in nodes[0]:
            sorted_nodes = sorted(nodes, key=lambda x: x.get("degree", 0), reverse=True)
            return [node.get("id", node.get("name", "")) for node in sorted_nodes[:5]]
        
        # Otherwise return first few nodes
        return [node.get("id", node.get("name", "")) for node in nodes[:5]]
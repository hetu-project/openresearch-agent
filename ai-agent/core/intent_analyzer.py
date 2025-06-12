"""
Intent Analyzer - Analyze user query intent
"""
import json
import re
from typing import Dict, Any, List
from models.intent import Intent, IntentType, IntentAnalysisResult
from services.llm_service import LLMService
from prompts import IntentPrompts
from utils.logger import get_logger

logger = get_logger(__name__)

class IntentAnalyzer:
    """Intent Analyzer Class"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.prompts = IntentPrompts()
    
    async def analyze(self, query: str, context: Dict[str, Any] = None) -> IntentAnalysisResult:
        """Analyze user query intent"""
        try:
            logger.info("Starting intent analysis", query=query)
            
            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(query, context)
            
            # Call LLM for intent analysis
            # llm_response = await self.llm_service.analyze_intent(analysis_prompt, context)
            try:
                llm_response = await self.llm_service.analyze_intent(analysis_prompt)
            except Exception as llm_error:
                logger.warning("LLM intent analysis failed, falling back to keyword matching", 
                            error=str(llm_error))
                # Directly use keyword matching as fallback
                llm_response = {"analysis": ""}
            
            # Parse LLM response
            intent_result = self._parse_llm_response(llm_response, query)
            
            logger.info("Intent analysis completed", 
                       intent_type=intent_result.primary_intent.type.value,
                       confidence=intent_result.primary_intent.confidence)
            
            return intent_result
            
        except Exception as e:
            logger.error("Intent analysis failed", error=str(e))
            # Return default unknown intent
            return self._create_fallback_intent(query)
    
    def _build_analysis_prompt(self, query: str, context: Dict[str, Any] = None) -> str:
        """Build intent analysis prompt"""
        base_prompt = self.prompts.get_intent_analysis_prompt()
        
        # Add context information
        context_info = ""
        if context and context.get("recent_intents"):
            context_info = f"\nContext: Recent intents include {context['recent_intents']}"
        
        return f"{base_prompt}\n\nUser Query: {query}{context_info}"
    
    def _parse_llm_response(self, llm_response: Dict[str, Any], original_query: str) -> IntentAnalysisResult:
        """Parse LLM response result"""
        try:
            logger.info("Parsing LLM response", response_keys=list(llm_response.keys()))
            
            # 1. Try to parse structured data returned by LLM first
            if "intent_type" in llm_response:
                # LLM directly returned intent type
                intent_type = llm_response["intent_type"]
                confidence = llm_response.get("confidence", 0.8)
                parameters = llm_response.get("parameters", {})
                entities = llm_response.get("entities", [])
                
                logger.info("Found structured intent in LLM response", 
                           intent_type=intent_type, 
                           confidence=confidence)
                
            elif "analysis" in llm_response:
                # LLM returned analysis text, try to extract structured information
                analysis_text = llm_response["analysis"]
                
                # Try to parse JSON format analysis result
                try:
                    if isinstance(analysis_text, str):
                        # Try to parse entire string as JSON
                        try:
                            analysis_data = json.loads(analysis_text)
                        except json.JSONDecodeError:
                            # If direct parsing fails, try to extract JSON part
                            # Look for possible JSON object (starts with { and ends with })
                            start_idx = analysis_text.find('{')
                            if start_idx != -1:
                                # Find the last matching }
                                brace_count = 0
                                end_idx = -1
                                for i in range(start_idx, len(analysis_text)):
                                    if analysis_text[i] == '{':
                                        brace_count += 1
                                    elif analysis_text[i] == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            end_idx = i
                                            break
                                
                                if end_idx != -1:
                                    json_str = analysis_text[start_idx:end_idx + 1]
                                    analysis_data = json.loads(json_str)
                                else:
                                    raise json.JSONDecodeError("No complete JSON found", analysis_text, 0)
                            else:
                                raise json.JSONDecodeError("No JSON found", analysis_text, 0)
                        
                        intent_type = analysis_data.get("intent_type", "unknown")
                        confidence = analysis_data.get("confidence", 0.7)
                        parameters = analysis_data.get("parameters", {})
                        entities = analysis_data.get("entities", [])
                        
                        logger.info("Parsed JSON from analysis text", 
                                   intent_type=intent_type, 
                                   confidence=confidence)
                    else:
                        # analysis_text itself is a dictionary
                        intent_type = analysis_text.get("intent_type", "unknown")
                        confidence = analysis_text.get("confidence", 0.7)
                        parameters = analysis_text.get("parameters", {})
                        entities = analysis_text.get("entities", [])
                        
                except (json.JSONDecodeError, AttributeError) as e:
                    # JSON parsing failed, fall back to keyword matching
                    logger.warning("Failed to parse JSON from analysis, falling back to keyword matching", 
                                 error=str(e))
                    intent_data = self._extract_intent_from_text(analysis_text, original_query)
                    intent_type = intent_data["intent_type"]
                    confidence = intent_data["confidence"]
                    parameters = intent_data["parameters"]
                    entities = intent_data["entities"]
            else:
                # No expected fields found, fall back to keyword matching
                logger.warning("No expected fields in LLM response, falling back to keyword matching")
                intent_data = self._extract_intent_from_text("", original_query)
                intent_type = intent_data["intent_type"]
                confidence = intent_data["confidence"] * 0.5  # Reduce confidence
                parameters = intent_data["parameters"]
                entities = intent_data["entities"]
            
            # 2. Validate and standardize intent type
            try:
                intent_type_enum = IntentType(intent_type)
                logger.info("Intent Type Enum: ", intent_type=intent_type_enum.value)
            except ValueError:
                logger.warning("Invalid intent type from LLM: ", intent_type=intent_type)
                # Try to map to known intent type
                intent_type_enum = self._map_to_known_intent(intent_type, original_query)
                confidence *= 0.8  # Reduce confidence
            
            # 3. Create primary intent
            primary_intent = Intent(
                type=intent_type_enum,
                confidence=confidence,
                parameters=parameters
            )
            
            # 4. Check if clarification is needed
            needs_clarification = self._should_clarify(intent_type_enum, confidence, parameters)
            clarification_questions = []
            if needs_clarification:
                clarification_questions = self._generate_clarification_questions({
                    "intent_type": intent_type_enum.value,
                    "confidence": confidence,
                    "parameters": parameters
                })
            
            logger.info("Intent parsing completed", 
                       intent_type=intent_type_enum.value,
                       confidence=confidence,
                       needs_clarification=needs_clarification)
            
            return IntentAnalysisResult(
                primary_intent=primary_intent,
                secondary_intents=[],
                needs_clarification=needs_clarification,
                clarification_questions=clarification_questions
            )
            
        except Exception as e:
            logger.error("Failed to parse LLM response", error=str(e))
            return self._create_fallback_intent(original_query)

    def _should_clarify(self, intent_type: IntentType, confidence: float, parameters: Dict[str, Any]) -> bool:
        """Determine if clarification is needed"""
        # Need clarification when confidence is too low
        if confidence < 0.7:
            return True
        
        # Define intent types that require necessary parameters
        intents_requiring_params = {
            # IntentType.SEARCH_PAPERS: ["title","query","search_keywords"],
            IntentType.GET_PAPER_DETAILS: ["search_keywords","keywords","paper_id","paper_title", "title", "query"],  # Need at least one
            IntentType.GET_PAPER_CITATIONS: ["paper_id","paper_title", "title", "query"],
            IntentType.SEARCH_AUTHORS: ["search_keywords","keywords","query", "author_name","name"],
            IntentType.GET_AUTHOR_DETAILS: ["search_keywords","keywords","query", "author_name", "author_id","name"],
            IntentType.GET_AUTHOR_PAPERS: ["author_name", "author_id"],
        }
        
        # Intent types that don't require necessary parameters
        intents_not_requiring_params = {
            IntentType.SEARCH_PAPERS,
            IntentType.SEARCH_AUTHORS,
            IntentType.GENERAL_CHAT,
            IntentType.GET_TRENDING_PAPERS,  # Can return trending papers for all fields
            IntentType.GET_TOP_KEYWORDS,     # Can return keywords for all fields
            IntentType.CITATION_NETWORK,     # Can provide general network analysis
            IntentType.COLLABORATION_NETWORK,
            IntentType.UNKNOWN
        }
        
        # If intent doesn't need parameters, return False
        if intent_type in intents_not_requiring_params:
            return False
        
        # Check if required parameters exist for intents that need them
        if intent_type in intents_requiring_params:
            required_params = intents_requiring_params[intent_type]
            # Check if at least one required parameter exists and is not empty
            has_required_param = any(
                parameters.get(param) and str(parameters.get(param)).strip() 
                for param in required_params
            )
            return not has_required_param
        
        # For other intents, need clarification if no parameters
        return not parameters or not any(v for v in parameters.values() if v)


    def _map_to_known_intent(self, intent_type: str, query: str) -> IntentType:
        """Map unknown intent type to known intent type"""
        intent_mapping = {
            # Paper related
            "paper_search": IntentType.SEARCH_PAPERS,
            "search_paper": IntentType.SEARCH_PAPERS,
            "find_papers": IntentType.SEARCH_PAPERS,
            "paper_details": IntentType.GET_PAPER_DETAILS,
            "get_paper": IntentType.GET_PAPER_DETAILS,
            "paper_info": IntentType.GET_PAPER_DETAILS,

            # Author related
            "author_search": IntentType.SEARCH_AUTHORS,
            "search_author": IntentType.SEARCH_AUTHORS,
            "find_authors": IntentType.SEARCH_AUTHORS,
            "author_details": IntentType.GET_AUTHOR_DETAILS,
            "get_author_details": IntentType.GET_AUTHOR_DETAILS,
            "author_profile": IntentType.GET_AUTHOR_DETAILS,
            "author_info": IntentType.GET_AUTHOR_DETAILS,
            "get_author": IntentType.SEARCH_AUTHORS,
            "author_papers": IntentType.GET_AUTHOR_PAPERS,
            "get_author_papers": IntentType.GET_AUTHOR_PAPERS,

            # Network analysis
            # "citation": IntentType.CITATION_NETWORK,
            # "citations": IntentType.CITATION_NETWORK,
            # "citation_network": IntentType.CITATION_NETWORK,
            # "citation_analysis": IntentType.CITATION_NETWORK,
            # "collaboration": IntentType.COLLABORATION_NETWORK,
            # "collaborations": IntentType.COLLABORATION_NETWORK,
            # "collaboration_network": IntentType.COLLABORATION_NETWORK,

            # Trend analysis
            "trending_papers": IntentType.GET_TRENDING_PAPERS,
            "trending": IntentType.GET_TRENDING_PAPERS,
            "trends": IntentType.GET_TRENDING_PAPERS,
            "trend": IntentType.GET_TRENDING_PAPERS,
            "research_trends": IntentType.GET_TRENDING_PAPERS,
            "research_landscape": IntentType.GET_TRENDING_PAPERS,
            "top_keywords": IntentType.GET_TOP_KEYWORDS,
            "keywords": IntentType.GET_TOP_KEYWORDS,

            # General
            "chat": IntentType.GENERAL_CHAT,
            "general": IntentType.GENERAL_CHAT,

            # Unknown intent
            "unknown": IntentType.UNKNOWN,
            "unclear": IntentType.UNKNOWN,
        }
        
        # Try direct mapping
        mapped_intent = intent_mapping.get(intent_type.lower())
        if mapped_intent:
            return mapped_intent
        
        # Try partial matching
        for key, value in intent_mapping.items():
            if key in intent_type.lower() or intent_type.lower() in key:
                return value
        
        # Fall back to keyword analysis
        intent_data = self._extract_intent_from_text("", query)
        logger.info(f"map_to_known_intent ** Intent Data: {intent_data}")
        
        try:
            return IntentType(intent_data["intent_type"])
        except ValueError:
            return IntentType.UNKNOWN

    def _create_fallback_intent(self, query: str) -> IntentAnalysisResult:
        """Create fallback intent result"""
        fallback_intent = Intent(
            type=IntentType.UNKNOWN,
            confidence=0.1,
            parameters={}
        )
        
        return IntentAnalysisResult(
            primary_intent=fallback_intent,
            needs_clarification=True,
            clarification_questions=["Sorry, I didn't fully understand your request. Could you please be more specific?"]
        )

    def _extract_intent_from_text(self, analysis_text: str, query: str) -> Dict[str, Any]:
        """Extract intent information from text"""
        # Improved keyword mapping - using more flexible matching
        keyword_patterns = [
            # Paper search related
            (["search", "paper"], "search_papers", 0.9),
            (["find", "paper"], "search_papers", 0.9),
            (["paper", "search"], "search_papers", 0.9),
            (["find", "paper"], "search_papers", 0.8),
            (["related papers"], "search_papers", 0.9),
            
            # Paper details
            (["paper", "details"], "get_paper_details", 0.9),
            (["paper", "information"], "get_paper_details", 0.8),

            # Paper citations
            (["paper", "citations"], "get_paper_citations", 0.9),
            (["citation", "relationship"], "get_paper_citations", 0.8),


            # Author search related
            (["search", "author"], "search_authors", 0.9),
            (["find", "author"], "search_authors", 0.9),
            (["author", "information"], "search_authors", 0.9),
            (["author", "search"], "search_authors", 0.9),
            (["author", "details"], "search_authors", 0.9),

            # Author papers
            (["author", "papers"], "get_author_papers", 0.9),
            (["author", "research"], "get_author_papers", 0.9),

            # Trend analysis
            (["trending", "papers"], "get_trending_papers", 0.9),
            (["trend", "papers"], "get_trending_papers", 0.8),
            (["trending", "keywords"], "get_top_keywords", 0.9),
            (["keyword", "analysis"], "get_top_keywords", 0.8),
            (["research", "trends"], "get_trending_papers", 0.7), 

            # General chat
            (["hello"], "general_chat", 0.9),
            (["chat"], "general_chat", 0.8),
            (["conversation"], "general_chat", 0.8),
        ]
        
        # Default values
        intent_type = "unknown"
        confidence = 0.3
        parameters = {}
        
        # Improved matching logic
        query_lower = query.lower()
        
        for keywords, mapped_intent, mapped_confidence in keyword_patterns:
            # Check if all keywords are in the query
            if all(keyword in query_lower for keyword in keywords):
                intent_type = mapped_intent
                confidence = mapped_confidence
                break
        
        # If no exact match, try single keyword matching
        if intent_type == "unknown":
            single_keyword_mapping = {
                "paper": ("search_papers", 0.7),
                "author": ("search_authors", 0.7),
                "search": ("search_papers", 0.6),  # Default search is paper search
                "find": ("search_papers", 0.6),
                "citation": ("get_paper_citations", 0.6),
                "trending": ("get_trending_papers", 0.6),
                "trend": ("get_trending_papers", 0.6),
                "keyword": ("get_top_keywords", 0.6),
                "collaboration": ("collaboration_network", 0.6),
                "network": ("citation_network", 0.5),
                "details": ("get_paper_details", 0.5),
                "information": ("get_paper_details", 0.5),
            }
            
            for keyword, (mapped_intent, mapped_confidence) in single_keyword_mapping.items():
                if keyword in query_lower:
                    intent_type = mapped_intent
                    confidence = mapped_confidence
                    break
        
        # Extract entities and parameters
        entities = self._extract_entities(query)
        parameters = self._extract_parameters(query, intent_type)
        
        logger.info("Intent extraction result", 
            intent_type=intent_type,
            confidence=confidence,
            parameters=parameters)
        
        return {
            "intent_type": intent_type,
            "confidence": confidence,
            "parameters": parameters,
            "entities": entities
        }

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query"""
        entities = []
        
        # Simple entity recognition (can be replaced with NER model later)
        common_entities = [
            "machine learning", "deep learning", "artificial intelligence", "natural language processing",
            "computer vision", "data mining", "neural networks", "reinforcement learning",
            "blockchain", "IoT", "cloud computing", "big data", "algorithms",
            "software engineering", "database", "network security", "distributed systems"
        ]
        
        for entity in common_entities:
            if entity in query:
                entities.append(entity)
        
        return entities
    
    def _extract_parameters(self, query: str, intent_type: str) -> Dict[str, Any]:
        """Extract parameters based on intent type"""
        parameters = {}
        
        if intent_type == "search_papers":
            # Extract search keywords
            query_clean = query.lower()
            
            # Remove common stop words
            stop_words = ["search", "find", "paper", "related", "about", "regarding", "find"]
            for stop_word in stop_words:
                query_clean = query_clean.replace(stop_word, " ")
            
            # Extract remaining keywords
            keywords = [word.strip() for word in query_clean.split() if word.strip()]
            if keywords:
                parameters["query"] = " ".join(keywords)
            else:
                # If no keywords extracted, use original query
                parameters["query"] = query
                
        elif intent_type == "search_authors":
            # Extract author name
            query_clean = query.lower()
            stop_words = ["search", "find", "author", "information", "details"]
            for stop_word in stop_words:
                query_clean = query_clean.replace(stop_word, " ")
            
            author_name = query_clean.strip()
            if author_name:
                # parameters["author_name"] = author_name
                parameters["query"] = author_name  # Also set query parameter
                
        elif intent_type == "get_paper_details":
            # Try to extract paper ID or title
            if "id:" in query.lower():
                paper_id = query.lower().split("id:")[1].strip()
                parameters["paper_id"] = paper_id
            else:
                # If no explicit ID, use entire query as search condition
                parameters["query"] = query
                
        elif intent_type == "get_author_papers":
            # Extract author ID or name
            if "id:" in query.lower():
                author_id = query.lower().split("id:")[1].strip()
                parameters["author_id"] = author_id
            else:
                # Extract author name
                query_clean = query.lower()
                stop_words = ["author", "papers", "get", "view"]
                for stop_word in stop_words:
                    query_clean = query_clean.replace(stop_word, " ")
                
                author_name = query_clean.strip()
                if author_name:
                    parameters["author_name"] = author_name
                    
        elif intent_type == "get_paper_citations":
            # Extract paper ID
            if "id:" in query.lower():
                paper_id = query.lower().split("id:")[1].strip()
                parameters["paper_id"] = paper_id
            else:
                parameters["query"] = query
                
        elif intent_type == "get_trending_papers":
            # Extract research field
            entities = self._extract_entities(query)
            if entities:
                parameters["field"] = entities[0]  # Use first recognized entity
            else:
                # Try to extract field information from query
                query_clean = query.lower()
                stop_words = ["trending", "papers", "trends", "in", "field"]
                for stop_word in stop_words:
                    query_clean = query_clean.replace(stop_word, " ")
                
                field = query_clean.strip()
                if field:
                    parameters["field"] = field
                    
        elif intent_type == "get_top_keywords":
            # Extract research field
            entities = self._extract_entities(query)
            if entities:
                parameters["field"] = entities[0]
            else:
                query_clean = query.lower()
                stop_words = ["trending", "keywords", "in", "field"]
                for stop_word in stop_words:
                    query_clean = query_clean.replace(stop_word, " ")
                
                field = query_clean.strip()
                if field:
                    parameters["field"] = field
        
        # Add common parameters for all intents
        parameters["original_query"] = query
        
        return parameters    

    def _generate_clarification_questions(self, intent_data: Dict[str, Any]) -> List[str]:
        """Generate clarification questions"""
        questions = []
        intent_type = intent_data.get("intent_type", "unknown")
        parameters = intent_data.get("parameters", {})
        
        if intent_type == "search_papers" and not parameters.get("query"):
            questions.append("What topic of papers would you like to search? Please provide more specific keywords.")
            
        elif intent_type == "search_authors" and not parameters.get("author_name") and not parameters.get("query"):
            questions.append("Which author's information would you like to find? Please provide the author's name.")
            
        elif intent_type == "get_paper_details" and not parameters.get("paper_id") and not parameters.get("query"):
            questions.append("Please provide the paper's ID or title to get detailed information.")
            
        elif intent_type == "get_author_papers" and not parameters.get("author_id") and not parameters.get("author_name"):
            questions.append("Please provide the author's ID or name to view their paper list.")
            
        elif intent_type == "get_paper_citations" and not parameters.get("paper_id") and not parameters.get("query"):
            questions.append("Please provide the paper's ID or title to analyze its citation relationships.")
            
        elif intent_type == "get_trending_papers" and not parameters.get("field"):
            questions.append("Which research field's trending papers would you like to see?")
            
        elif intent_type == "get_top_keywords" and not parameters.get("field"):
            questions.append("Which research field's top keywords would you like to see?")
            
        elif intent_type == "unknown":
            questions.append("Sorry, I didn't fully understand your request. Would you like to:")
            questions.append("1. Search for papers?")
            questions.append("2. Find author information?")
            questions.append("3. Analyze citation relationships?")
            questions.append("4. View research trends?")
            questions.append("Please tell me your specific needs.")
        
        return questions
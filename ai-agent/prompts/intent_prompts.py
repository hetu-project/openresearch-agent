"""
Intent analysis prompt template
"""

class IntentPrompts:
    """Intent analysis prompt class"""
    
    def __init__(self):
        self.intent_types = {
            "search_papers": "Search Papers",
            "get_paper_details": "Get Paper Details", 
            "search_authors": "Search Authors",
            "get_author_details": "Get Author Details",
            "citation_analysis": "Citation Analysis",
            "collaboration_analysis": "Collaboration Analysis",
            "trend_analysis": "Research Trend Analysis",
            "get_top_keywords": "Get Hot Topics or Keywords",
            "research_landscape": "Research Landscape Analysis",
            "paper_review": "Paper Review",
            "paper_generation": "Paper Generation",
            "unknown": "Unknown Intent"
        }
    
    def get_intent_analysis_prompt(self) -> str:
        """Get basic prompt for intent analysis"""
        return f"""You are a professional academic research AI assistant who needs to analyze user query intent.

                Supported intent types include:
                {self._format_intent_types()}

                Please analyze the user's query, identify their main intent, and provide the following information:
                1. Intent type (select the most matching type from above)
                2. Confidence (value between 0-1)
                3. Key parameters (such as search keywords, author names, etc.)
                4. Entity information (such as research fields, institution names, etc.)

                Analysis requirements:
                - Accurately identify user's core needs
                - Consider academic research professionalism
                - Extract useful parameters and entities
                - Mark for clarification if intent is unclear

                Please reply in Chinese with clear formatting."""
    
    def get_clarification_prompt(self, intent_type: str) -> str:
        """Get prompt for clarification questions"""
        clarification_templates = {
            "search_papers": "What topic or keywords would you like to search for papers? Please provide more specific research fields or keywords.",
            "search_authors": "Which author's information would you like to find? Please provide the author's name or related information.",
            "citation_analysis": "Which paper or research field's citation relationships would you like to analyze?",
            "collaboration_analysis": "Which authors or institutions' collaboration relationships would you like to analyze?",
            "trend_analysis": "Which research field's development trends would you like to understand? Please specify the research direction.",
            "research_landscape": "Which research field's overall situation would you like to understand?",
            "paper_review": "Which paper would you like to review? Please provide the paper title or related information.",
            "paper_generation": "What topic would you like to generate a paper on? Please provide research direction and specific requirements.",
            "unknown": "Sorry, I didn't fully understand your needs. Could you describe more specifically what you'd like to do?"
        }
        
        return clarification_templates.get(intent_type, clarification_templates["unknown"])
    
    def get_context_prompt(self, recent_intents: list) -> str:
        """Get context-related prompt"""
        if not recent_intents:
            return ""
        
        recent_intent_str = ", ".join([intent.get("type", "unknown") for intent in recent_intents[-3:]])
        return f"""
                Context information:
                User's recent query intents include: {recent_intent_str}
                Please combine this context information to more accurately analyze the current query intent.
                """
    
    def get_entity_extraction_prompt(self) -> str:
        """Get entity extraction prompt"""
        return """Please extract the following types of entities from the user query:
                1. Research field/topic (e.g., machine learning, deep learning, natural language processing, etc.)
                2. Author names
                3. Institution names
                4. Journal/Conference names
                5. Time range
                6. Paper titles or keywords

                Please accurately identify and categorize these entities."""
    
    def get_parameter_extraction_prompt(self, intent_type: str) -> str:
        """Get parameter extraction prompt based on intent type"""
        parameter_templates = {
            "search_papers": "Please extract search-related parameters: query keywords, research field, time range, author restrictions, etc.",
            "search_authors": "Please extract author search-related parameters: author name, institution, research field, etc.",
            "citation_analysis": "Please extract citation analysis-related parameters: target paper, analysis type, time range, etc.",
            "collaboration_analysis": "Please extract collaboration analysis-related parameters: target authors/institutions, analysis dimensions, time range, etc.",
            "trend_analysis": "Please extract trend analysis-related parameters: research field, time range, analysis granularity, etc.",
            "get_top_keywords": "Please extract hot topic analysis-related parameters: target research field, time range, number of keywords, popularity metrics, etc.",
            "research_landscape": "Please extract research landscape-related parameters: research field, analysis dimensions, level of detail, etc."
        }
        
        return parameter_templates.get(intent_type, "Please extract key parameters from the query.")
    
    def _format_intent_types(self) -> str:
        """Format intent type list"""
        formatted_types = []
        for key, description in self.intent_types.items():
            formatted_types.append(f"- {key}: {description}")
        return "\n".join(formatted_types)
    
    def get_confidence_evaluation_prompt(self) -> str:
        """Get confidence evaluation prompt"""
        return """Confidence evaluation criteria:
                - 0.9-1.0: Intent is very clear, key information is complete
                - 0.7-0.9: Intent is relatively clear, but may lack some details
                - 0.5-0.7: Intent is basically clear, but needs further clarification
                - 0.3-0.5: Intent is vague, needs more information from user
                - 0.0-0.3: Intent is unclear, cannot accurately judge user needs
        Please evaluate confidence based on the clarity and completeness of user query."""
    
    def get_multi_intent_prompt(self) -> str:
        """Get multi-intent analysis prompt"""
        return """If user query contains multiple intents, please:
                1. Identify primary intent (most important need)
                2. Identify secondary intents (additional needs)
                3. Analyze relationships between intents
                4. Suggest processing order

                For example: "Search for machine learning papers and analyze their citation trends" contains both paper search and trend analysis intents."""
"""
Response generation prompt templates
"""

class ResponsePrompts:
    """Response Generation Prompt Class"""
    
    def __init__(self):
        self.response_strategies = {
            "paper_list": "Paper List Display",
            "paper_detail": "Paper Detail Display", 
            "author_list": "Author List Display",
            "author_detail": "Author Detail Display",
            "network_analysis": "Network Analysis Results",
            "trend_report": "Trend Analysis Report",
            "landscape_overview": "Research Landscape Overview",
            "review_report": "Paper Review Report",
            "generation_guide": "Paper Generation Guide",
            "clarification": "Clarification Query",
            "general": "General Reply"
        }
    
    def get_response_generation_prompt(self, strategy: str) -> str:
        """Get response generation prompt based on strategy"""
        base_prompt = self._get_base_response_prompt()
        strategy_prompt = self._get_strategy_specific_prompt(strategy)
        
        return f"{base_prompt}\n\n{strategy_prompt}"
    
    def _get_base_response_prompt(self) -> str:
        """Get base response generation prompt"""
        return """You are a professional academic research AI assistant who needs to generate natural and professional responses based on user queries and analysis results.

                Response requirements:
                1. Natural and fluent language that conforms to English expression habits
                2. Professional and accurate content that reflects academic research rigor
                3. Clear structure with highlighted key points
                4. Adjust level of detail according to data volume
                5. Provide valuable insights and suggestions
                6. Maintain a friendly and helpful tone

                Please generate responses based on the provided structured data, ensuring information is accurate and easy to understand."""
    
    def _get_strategy_specific_prompt(self, strategy: str) -> str:
        """Get strategy-specific prompt"""
        strategy_prompts = {
            "paper_list": self._get_paper_list_prompt(),
            "paper_detail": self._get_paper_detail_prompt(),
            "author_list": self._get_author_list_prompt(),
            "author_detail": self._get_author_detail_prompt(),
            "network_analysis": self._get_network_analysis_prompt(),
            "trend_report": self._get_trend_report_prompt(),
            "landscape_overview": self._get_landscape_overview_prompt(),
            "review_report": self._get_review_report_prompt(),
            "generation_guide": self._get_generation_guide_prompt(),
            "clarification": self._get_clarification_prompt(),
            "general": self._get_general_prompt()
        }
        
        return strategy_prompts.get(strategy, strategy_prompts["general"])
    
    def _get_paper_list_prompt(self) -> str:
        """Paper list display prompt"""
        return """For paper search results, please:
                1. Summarize overall search results (total number, main characteristics)
                2. Highlight most relevant or important papers
                3. Analyze paper distribution by time, authors, etc.
                4. Identify research hotspots and trends
                5. Provide suggestions for further exploration

                Format suggestions:
                - Brief summary of search results at the beginning
                - Focus on 3-5 representative papers
                - Analyze overall characteristics and trends
                - Provide follow-up suggestions at the end"""
    
    def _get_paper_detail_prompt(self) -> str:
        """Paper detail display prompt"""
        return """For paper details, please:
                1. Clearly introduce basic paper information (title, authors, publication date, etc.)
                2. Summarize main contributions and innovations
                3. Analyze academic impact (citations, importance)
                4. Introduce author background and research direction
                5. Provide suggestions for exploring related research

                Focus on:
                - Core value and contribution of the paper
                - Status and influence in the field
                - Relationship with other related work"""
    
    def _get_author_list_prompt(self) -> str:
        """Author list display prompt"""
        return """For author search results, please:
                1. Summarize number of authors found and overall characteristics
                2. Highlight most relevant or active authors
                3. Analyze author distribution by institution and research field
                4. Identify core researchers in the field
                5. Provide suggestions for deeper understanding

                Key points:
                - Authors' academic reputation and influence
                - Research directions and expertise
                - Institutional background and collaboration networks"""
    
    def _get_author_detail_prompt(self) -> str:
        """Author detail display prompt"""
        return """For author details, please:
                1. Comprehensively introduce academic background and achievements
                2. Summarize main research directions and contributions
                3. Analyze academic impact and reputation metrics
                4. Introduce important collaborations and networks
                5. Summarize author's position in the field

                Focus on:
                - Representative work and important contributions
                - Academic trajectory and development
                - Influence and status in academia"""
    
    def _get_network_analysis_prompt(self) -> str:
        """Network analysis results prompt"""
        return """For network analysis results, please:
                1. Explain overall network structure and characteristics
                2. Identify key nodes and core groups in the network
                3. Analyze connection patterns and relationship strength
                4. Discover interesting network phenomena and patterns
                5. Provide suggestions for network optimization or utilization

                Analysis focus:
                - Network scale and density
                - Centrality and influence distribution
                - Community structure and clustering characteristics
                - Network evolution and development trends"""
    
    def _get_trend_report_prompt(self) -> str:
        """Trend analysis report prompt"""
        return """For trend analysis results, please:
                1. Summarize overall development trends in research field
                2. Identify hot topics and emerging directions
                3. Analyze technical evolution and methodological changes
                4. Predict possible future development directions
                5. Provide research opportunities and suggestions

                Report structure:
                - Trend overview and main findings
                - Hotspot analysis and case studies
                - Development stages and evolution path
                - Future outlook and research recommendations"""
    
    def _get_landscape_overview_prompt(self) -> str:
        """Research landscape overview prompt"""
        return """For research landscape analysis, please:
                1. Depict overall research landscape of the field
                2. Introduce main research directions and branches
                3. Analyze development status of different directions
                4. Identify research gaps and opportunities
                5. Provide comprehensive research guidance

                Landscape elements:
                - Field boundaries and core issues
                - Main research paradigms and methods
                - Important institutions and research teams
                - Development history and milestones
                - Future challenges and opportunities"""
    
    def _get_review_report_prompt(self) -> str:
        """Paper review report prompt"""
        return """For paper review, please:
                1. Objectively evaluate academic quality
                2. Analyze innovation and contribution
                3. Point out strengths and weaknesses
                4. Provide specific improvement suggestions
                5. Give comprehensive evaluation and recommendations

                Review dimensions:
                - Importance and novelty of research question
                - Scientific validity and rationality of methods
                - Experimental design and results analysis
                - Writing quality and clarity of expression
                - Academic standards and citation completeness"""
    
    def _get_generation_guide_prompt(self) -> str:
        """Paper generation guide prompt"""
        return """For paper generation needs, please:
                1. Analyze research topic feasibility
                2. Provide paper structure and outline suggestions
                3. Recommend relevant literature and references
                4. Guide research methods and technical approach
                5. Provide writing tips and considerations

                Guidance content:
                - Research problem definition and scope
                - Literature review direction and focus
                - Research method selection and application
                - Paper structure and chapter arrangement
                - Writing standards and academic norms"""
    
    def _get_clarification_prompt(self) -> str:
        """Clarification query prompt"""
        return """When clarification of user intent is needed, please:
                1. Friendly explain understanding difficulties
                2. Specifically point out aspects needing clarification
                3. Provide multiple choices or examples
                4. Guide users to provide more information
                5. Maintain patient and helpful attitude

                Clarification strategy:
                - Restate understood content
                - Raise specific clarification questions
                - Provide relevant options or examples
                - Encourage detailed description of needs"""
    
    def _get_general_prompt(self) -> str:
        """General reply prompt"""
        return """For general queries, please:
                1. Provide best response based on available information
                2. Acknowledge information limitations
                3. Provide relevant background knowledge
                4. Suggest ways to obtain more information
                5. Maintain professional and helpful attitude

                Response principles:
                - Based on facts, avoid speculation
                - Acknowledge uncertainties
                - Provide valuable relevant information
                - Guide users to get better help"""
    
    def get_error_response_prompt(self) -> str:
        """Error response prompt"""
        return """When errors occur, please:
                1. Apologize friendly and explain situation
                2. Briefly explain possible causes
                3. Provide problem-solving suggestions
                4. Encourage users to try again
                5. Maintain positive and supportive tone

                Error handling principles:
                - Take responsibility, don't shift to users
                - Provide specific solutions
                - Maintain professional and friendly attitude
                - Encourage continued use of service"""
    
    def get_follow_up_prompt(self, intent_type: str) -> str:
        """Get follow-up suggestion prompt"""
        follow_up_templates = {
            "search_papers": [
                "View detailed information and abstracts of specific papers",
                "Analyze author collaboration networks of these papers",
                "Explore development trends in related research fields",
                "Understand core contributions of highly cited papers"
            ],
            "search_authors": [
                "Deep dive into author's research trajectory and representative works",
                "Analyze collaboration networks between authors",
                "Explore research strength of author's institutions",
                "Follow author's latest research developments"
            ],
            "trend_analysis": [
                "Deep analysis of specific technical direction evolution",
                "Compare research hotspot changes across different time periods",
                "Explore development opportunities in emerging research directions",
                "Analyze impact of technical trends on industry"
            ],
            "citation_analysis": [
                "Analyze citation network evolution patterns",
                "Identify key papers with breakthrough impact",
                "Explore cross-domain citation relationships",
                "Predict future research development directions"
            ]
        }
        
        suggestions = follow_up_templates.get(intent_type, [
            "Further refine your research question",
            "Explore related research fields",
            "Learn about latest research developments",
            "Look for suitable collaboration opportunities"
        ])
        
        return f"Based on current analysis, it is suggested that you can:\n" + "\n".join([f"• {suggestion}" for suggestion in suggestions])

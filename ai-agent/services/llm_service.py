"""
Large Language Model Service - Together.ai Version
"""
import asyncio
import structlog
import aiohttp
import json
from typing import Dict, Any, Optional, List

from configs.llm_config import llm_config
from models.task import Task, TaskResult, TaskStatus

logger = structlog.get_logger()

class LLMService:
    """Large Language Model Service - Together.ai"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._validate_config()
    
    async def initialize(self):
        """Initialize LLM service"""
        try:
            logger.info("Initializing LLM service")
            
            # Validate configuration
            self._validate_config()
            
            # Pre-create HTTP session
            await self._get_session()
            
            # Optional: Perform health check
            # health_status = await self.health_check()
            # if health_status["status"] != "healthy":
            #     raise Exception(f"LLM service health check failed: {health_status.get('error')}")
            
            logger.info("LLM service initialized successfully")
        
        except Exception as e:
            logger.error("Failed to initialize LLM service", error=str(e))
            raise


    def _validate_config(self):
        """Validate configuration"""
        try:
            llm_config.validate_config()
            logger.info("Together.ai LLM service initialized", model=llm_config.together_model)
        except Exception as e:
            logger.error("LLM configuration validation failed", error=str(e))
            raise
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=llm_config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response"""
        try:
            session = await self._get_session()
            
            # Build request parameters
            payload = {
                "model": llm_config.together_model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", llm_config.max_tokens),
                "temperature": kwargs.get("temperature", llm_config.temperature),
                "context_length_exceeded_behavior": llm_config.context_length_exceeded_behavior
            }
            
            # Add optional parameters
            if "top_p" in kwargs:
                payload["top_p"] = kwargs["top_p"]
            if "frequency_penalty" in kwargs:
                payload["frequency_penalty"] = kwargs["frequency_penalty"]
            if "presence_penalty" in kwargs:
                payload["presence_penalty"] = kwargs["presence_penalty"]
            
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Bearer {llm_config.together_api_key}"
            }
            
            logger.debug("Generating LLM response", 
                        model=payload["model"], 
                        messages_count=len(messages),
                        max_tokens=payload["max_tokens"])
            
            # Send request
            async with session.post(
                llm_config.together_base_url,
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error("Together.ai API error", 
                            status=response.status, 
                            error=error_text)
                    raise Exception(f"Together.ai API error {response.status}: {error_text}")
                
                result = await response.json()
                
                # Extract response content
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    
                    # Log usage
                    usage = result.get("usage", {})
                    logger.info(
                        "LLM response generated successfully",
                        model=payload["model"],
                        prompt_tokens=usage.get("prompt_tokens"),
                        completion_tokens=usage.get("completion_tokens"),
                        total_tokens=usage.get("total_tokens")
                    )
                    
                    # Log response content for debugging
                    logger.debug("LLM response content", content_preview=content[:200])
                    
                    return content
                else:
                    logger.error("Invalid response from Together.ai", response=result)
                    raise Exception("No valid response from Together.ai API")
                    
        except aiohttp.ClientError as e:
            logger.error("HTTP client error", error=str(e))
            raise Exception(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error("JSON decode error", error=str(e))
            raise Exception(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            logger.error("Failed to generate LLM response", error=str(e))
            raise

        
    async def analyze_intent(self, user_message: str) -> Dict[str, Any]:
        """Analyze user intent"""
        try:
            # Build intent analysis prompt
            system_prompt = """You are an intent analyzer for an academic research assistant. Please analyze the user's query intent and return the result in JSON format.
                            Possible intent types:
                            - search_papers: Search papers
                            - get_paper_details: Get paper details
                            - search_authors: Search authors
                            - get_author_details: Get author details
                            - citation_network: Citation network analysis
                            - collaboration_network: Collaboration network analysis
                            - research_trends: Research trends analysis
                            - research_landscape: Research landscape analysis
                            - general_chat: General conversation
                            - unknown: Unknown intent

                            Please return in JSON format:
                            {
                                "intent_type": "intent type",
                                "confidence": confidence between 0.0-1.0,
                                "parameters": {extracted parameters},
                                "needs_clarification": true/false,
                                "clarification_question": "clarification question (if needed)"
                            }
                            
                            Important: Only return pure JSON object, do not use markdown format or code blocks."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = await self.generate_response(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=500
            )
            
            # Parse response - handle multiple formats
            result = self._parse_json_response(response)
            
            if result:
                logger.info("Intent analysis completed", intent=result.get("intent_type"))
                return result
            else:
                logger.warning("Failed to parse intent analysis JSON, using fallback")
                return {
                    "intent_type": "unknown",
                    "confidence": 0.3,
                    "parameters": {},
                    "needs_clarification": True,
                    "clarification_question": "Please describe your needs more specifically"
                }
                
        except Exception as e:
            logger.error("Intent analysis failed", error=str(e))
            return {
                "intent_type": "unknown",
                "confidence": 0.0,
                "parameters": {},
                "needs_clarification": True,
                "clarification_question": "Sorry, I cannot understand your request, please rephrase"
            }

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response, support multiple formats"""
        if not response:
            return None
        
        import re
        
        # Method 1: Direct parse (if pure JSON)
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass
        
        # Method 2: Extract JSON from markdown code blocks
        # Match  ...  or  ... 
        patterns = [
            r'\s*\n?(.*?)\n?',
            r'\s*\n?(.*?)\n?',
            r'`(.*?)`'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    json_str = match.strip()
                    result = json.loads(json_str)
                    if isinstance(result, dict):
                        return result
                except json.JSONDecodeError:
                    continue
        
        # Method 3: Find JSON object pattern
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response)
        for match in matches:
            try:
                result = json.loads(match)
                if isinstance(result, dict) and "intent_type" in result:
                    return result
            except json.JSONDecodeError:
                continue
        
        # Method 4: Search line by line
        lines = response.split('\n')
        json_lines = []
        in_json = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('{'):
                in_json = True
                json_lines = [line]
            elif in_json:
                json_lines.append(line)
                if line.endswith('}'):
                    try:
                        json_str = '\n'.join(json_lines)
                        result = json.loads(json_str)
                        if isinstance(result, dict):
                            return result
                    except json.JSONDecodeError:
                        pass
                    in_json = False
                    json_lines = []
        
        logger.warning("Could not extract JSON from response", response_preview=response[:200])
        return None
    
    async def generate_academic_response(self, user_query: str, 
                                       research_data: Dict[str, Any],
                                       conversation_history: List[Dict[str, str]] = None) -> str:
        """Generate academic research related response"""
        try:
            # Build academic assistant system prompt
            system_prompt = """You are a professional academic research assistant, specializing in helping users with paper searches, author queries, citation analysis, and other academic research tasks.
                            Please generate professional, accurate, and helpful responses based on the provided research data. The response should:
                            1. Directly answer the user's question
                            2. Provide specific data and information
                            3. Use professional but understandable language
                            4. Honestly indicate if data is incomplete
                            5. Provide suggestions for further research when appropriate
                            CRITICAL: You MUST respond in English only. Never use Chinese or any other language.
                            Please respond in English, maintaining a professional and friendly tone."""

            # Build user message including query and data
            user_content = f"""User Query: {user_query}
                            Research Data:
                            {json.dumps(research_data, ensure_ascii=False, indent=2)}

                            Please answer the user's query based on the above data."""

            # Build message list
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (recent rounds)
            if conversation_history:
                messages.extend(conversation_history[-6:])  # Only keep the last 3 rounds
            
            messages.append({"role": "user", "content": user_content})
            
            response = await self.generate_response(
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            logger.info("Academic response generated successfully")
            return response
            
        except Exception as e:
            logger.error("Failed to generate academic response", error=str(e))
            return "Sorry, an error occurred while generating the response. Please try again later."
    
    async def execute_task(self, task: Task) -> TaskResult:
        """Execute LLM task"""
        try:
            task.status = TaskStatus.RUNNING
            start_time = asyncio.get_event_loop().time()
            
            logger.info("Executing LLM task", task_id=task.id, task_name=task.name)
            
            # Get task parameters
            prompt = task.parameters.get("prompt", "")
            model_params = task.parameters.get("model_params", {})
            
            if not prompt:
                raise ValueError("Prompt is required for LLM task")
            
            # Build messages
            messages = [{"role": "user", "content": prompt}]
            
            # Generate response
            response = await self.generate_response(messages=messages, **model_params)
            
            # Calculate execution time
            execution_time = asyncio.get_event_loop().time() - start_time
            
            task.status = TaskStatus.COMPLETED
            
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                data={"response": response},
                execution_time=execution_time
            )
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            
            logger.error("LLM task execution failed", task_id=task.id, error=str(e))
            
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        try:
            # Send simple test request
            test_messages = [{"role": "user", "content": "Hello"}]
            await self.generate_response(messages=test_messages, max_tokens=10)
            
            return {
                "status": "healthy",
                "provider": "together.ai",
                "model": llm_config.together_model,
                "base_url": llm_config.together_base_url
            }
        except Exception as e:
            logger.error("LLM health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "provider": "together.ai",
                "error": str(e)
            }
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
                logger.info("LLM service HTTP session closed")
        except Exception as e:
            logger.error("Error during LLM service cleanup", error=str(e))


llm_service = LLMService()

"""
Core Agent Class
"""
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

import asyncio
from typing import Set

from data.models.conversation import Conversation
from models.intent import IntentAnalysisResult
from models.task import TaskPlan, Task, TaskType
from services.llm_service import LLMService
from services import MCPClient
from data.context_manager import ContextManager
from .intent_analyzer import IntentAnalyzer
from .task_orchestrator import TaskOrchestrator
from .response_integrator import ResponseIntegrator
from utils.logger import get_logger

logger = get_logger(__name__)

class AcademicAgent:
    """Academic Research AI Agent Core Class"""
    
    def __init__(self):
        # Initialize core services
        self.llm_service = LLMService()
        self.mcp_client = MCPClient() 
        self.context_manager = ContextManager()
        
        # Initialize core components
        self.intent_analyzer = IntentAnalyzer(self.llm_service)
        self.task_orchestrator = TaskOrchestrator()
        self.response_integrator = ResponseIntegrator(self.llm_service)
        
        # State management
        self.active_conversations: Dict[str, Conversation] = {}
        self.processing_queries: Dict[str, bool] = {}
    
    async def initialize(self):
        """Initialize Agent"""
        try:
            logger.info("Initializing Academic Agent")
            
            # Initialize context manager (including database initialization)
            await self.llm_service.initialize()
            await self.mcp_client.initialize()
            await self.context_manager.initialize()
            
            logger.info("Academic Agent initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Academic Agent", error=str(e))
            raise

    async def _extract_context_for_intent(self, conversation: Conversation) -> Dict[str, Any]:
        """Extract context for intent analysis"""
        context = {}
        
        if hasattr(conversation, 'messages') and conversation.messages:
            # Get recent intent types
            recent_intents = []
            for message in conversation.messages[-5:]:  # Last 5 messages
                if hasattr(message, 'role') and message.role == "assistant" and hasattr(message, 'metadata'):
                    # Ensure metadata is dictionary type
                    metadata = message.metadata
                    if isinstance(metadata, str):
                        try:
                            import json
                            metadata = json.loads(metadata)
                        except (json.JSONDecodeError, TypeError):
                            metadata = {}
                    elif not isinstance(metadata, dict):
                        metadata = {}
                    
                    # Now safely use get method
                    if metadata.get("intent_type"):
                        recent_intents.append(metadata["intent_type"])
            
            context["recent_intents"] = recent_intents
            context["conversation_length"] = len(conversation.messages)
        
        return context

    
    async def _extract_context_for_response(self, conversation: Conversation) -> Dict[str, Any]:
        """Extract context for response generation"""
        context = {}
        
        if hasattr(conversation, 'messages') and conversation.messages:
            context["conversation_length"] = len(conversation.messages)
            context["recent_topics"] = []  # Can add topic extraction logic
            
            # Extract recent query types
            recent_queries = []
            for message in conversation.messages[-10:]:
                if hasattr(message, 'role') and message.role == "user":
                    recent_queries.append(message.content[:50])  # First 50 characters
            context["recent_queries"] = recent_queries
        
        return context

    async def _execute_task_plan(self, task_plan: TaskPlan, query_id: str) -> Dict[str, Any]:
        """Execute task plan - Support dependency management and parallel execution"""
        results = {}
        completed_task_ids = set()
        failed_task_ids = set()
        
        try:
            logger.info("Starting task plan execution", 
                    query_id=query_id,
                    initial_stats=task_plan.get_completion_stats())
            
            # Loop execution until all tasks complete or fail
            max_iterations = len(task_plan.tasks) * 2  # Prevent infinite loop
            iteration = 0
            
            while not task_plan.is_completed() and iteration < max_iterations:
                iteration += 1
                
                # Get executable tasks
                ready_tasks = task_plan.get_ready_tasks(completed_task_ids)
                
                if not ready_tasks:
                    # No executable tasks, check if there's a problem
                    pending_tasks = task_plan.get_pending_tasks()
                    if pending_tasks:
                        logger.warning("No ready tasks found but pending tasks exist", 
                                    pending_task_ids=[t.id for t in pending_tasks],
                                    completed_ids=list(completed_task_ids),
                                    failed_ids=list(failed_task_ids))
                        # Force execute first pending task to avoid deadlock
                        ready_tasks = [pending_tasks[0]]
                    else:
                        break
                
                # Separate parallel and serial tasks
                parallel_tasks = task_plan.get_parallel_tasks(ready_tasks)
                serial_tasks = task_plan.get_serial_tasks(ready_tasks)
                
                logger.info("Executing tasks batch", 
                        iteration=iteration,
                        parallel_count=len(parallel_tasks),
                        serial_count=len(serial_tasks))
                
                # Execute parallel tasks
                if parallel_tasks:
                    parallel_results = await self._execute_parallel_tasks(parallel_tasks, query_id)
                    results.update(parallel_results)
                    
                    # Update task status
                    for task in parallel_tasks:
                        if task.id in parallel_results:
                            result = parallel_results[task.id]
                            # Fix: Ensure result is dictionary type
                            if isinstance(result, dict) and result.get("error"):
                                task.mark_failed(result["error"])
                                failed_task_ids.add(task.id)
                            elif isinstance(result, str) and "error" in result.lower():
                                # If result is error string
                                task.mark_failed(result)
                                failed_task_ids.add(task.id)
                            else:
                                task.mark_completed()
                                completed_task_ids.add(task.id)
                
                # Execute serial tasks
                for task in serial_tasks:
                    try:
                        logger.info("Executing serial task", 
                                task_id=task.id, 
                                task_name=task.name)
                        
                        task.mark_started()
                        
                        # Update task parameters (may depend on previous task results)
                        updated_parameters = self._update_task_parameters(task, results)
                        
                        result = await self._execute_single_task(task, updated_parameters)
                        
                        results[task.id] = result
                        task.mark_completed()
                        completed_task_ids.add(task.id)
                        
                        logger.info("Serial task completed", 
                                task_id=task.id,
                                execution_time=task.execution_time)
                        
                    except Exception as e:
                        error_msg = str(e)
                        logger.error("Serial task failed", 
                                    task_id=task.id, 
                                    error=error_msg)
                        
                        results[task.id] = {"error": error_msg}
                        task.mark_failed(error_msg)
                        failed_task_ids.add(task.id)
            
            final_stats = task_plan.get_completion_stats()
            logger.info("Task plan execution completed", 
                    query_id=query_id,
                    iterations=iteration,
                    final_stats=final_stats)
            
            return results
            
        except Exception as e:
            logger.error("Task plan execution failed", query_id=query_id, error=str(e))
            return {"error": str(e)}


    async def _execute_parallel_tasks(self, tasks: List[Task], query_id: str) -> Dict[str, Any]:
        """Execute parallel tasks"""
        logger.info("Executing parallel tasks", 
                query_id=query_id,
                task_count=len(tasks),
                task_ids=[t.id for t in tasks])
        
        async def execute_single_task_wrapper(task: Task) -> tuple[str, Any]:
            try:
                task.mark_started()
                result = await self._execute_single_task(task, task.parameters)
                return task.id, result
            except Exception as e:
                error_msg = str(e)
                logger.error("Parallel task failed", task_id=task.id, error=error_msg)
                return task.id, {"error": error_msg}
        
        # Use asyncio.gather for parallel execution
        task_coroutines = [execute_single_task_wrapper(task) for task in tasks]
        task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Organize results
        results = {}
        for result in task_results:
            if isinstance(result, Exception):
                logger.error("Parallel task execution exception", error=str(result))
                continue
            
            task_id, task_result = result
            results[task_id] = task_result
        
        return results

    async def _execute_single_task(self, task: Task, parameters: Dict[str, Any]) -> Any:
        """Execute single task"""
        try:
            if task.type == TaskType.MCP_TOOL_CALL:
                # Extract tool name and arguments from parameters
                tool_name = parameters.get("tool_name")
                arguments = parameters.get("arguments", {})
                
                if not tool_name:
                    raise ValueError(f"Missing tool_name in task parameters: {parameters}")
                
                result = await self.mcp_client.call_tool(tool_name, arguments)
                # Ensure return dictionary format
                if isinstance(result, str):
                    return {"content": result, "type": "text"}
                elif isinstance(result, dict):
                    return result
                else:
                    return {"content": str(result), "type": "unknown"}
            
            elif task.type == TaskType.LLM_GENERATION:
                # LLM generation task
                prompt = parameters.get("prompt")
                model_params = parameters.get("model_params", {})
                
                if not prompt:
                    raise ValueError(f"Missing prompt in LLM task parameters: {parameters}")
                
                result = await self.llm_service.generate_text(prompt, **model_params)
                # Ensure return dictionary format
                if isinstance(result, str):
                    return {"content": result, "type": "text"}
                elif isinstance(result, dict):
                    return result
                else:
                    return {"content": str(result), "type": "unknown"}
            
            elif task.type == TaskType.RESPONSE_GENERATION:
                # Response generation task
                content = parameters.get("content")
                format_type = parameters.get("format_type", "text")
                
                if not content:
                    raise ValueError(f"Missing content in response task parameters: {parameters}")
                
                # Can do different formatting based on format_type here
                return {"formatted_content": content, "format": format_type}
            
            else:
                raise ValueError(f"Unknown task type: {task.type}")
                
        except Exception as e:
            logger.error("Task execution failed", task_id=task.id, error=str(e))
            return {"error": str(e)}


    def _update_task_parameters(self, task: Task, previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Update current task parameters based on previous task results"""
        parameters = task.parameters.copy()
        
        # Special handling: If getting paper details task and depends on search task
        if (task.type == TaskType.MCP_TOOL_CALL and 
            parameters.get("tool_name") == "get_paper_details" and 
            task.dependencies):
            
            # Extract paper ID from dependency task results
            for dep_task_id in task.dependencies:
                if dep_task_id in previous_results:
                    dep_result = previous_results[dep_task_id]
                    
                    # Ensure dep_result is dictionary type
                    if not isinstance(dep_result, dict):
                        logger.warning("Dependency result is not a dict", 
                                    task_id=task.id, 
                                    dep_task_id=dep_task_id,
                                    result_type=type(dep_result).__name__)
                        continue
                    
                    # Assume search results contain paper list
                    if "papers" in dep_result:
                        papers = dep_result["papers"]
                        if papers and len(papers) > 0:
                            # Take first paper's ID
                            first_paper = papers[0]
                            if isinstance(first_paper, dict):
                                paper_id = first_paper.get("id") or first_paper.get("paper_id")
                                if paper_id:
                                    # Update parameters
                                    if "arguments" not in parameters:
                                        parameters["arguments"] = {}
                                    parameters["arguments"]["paper_id"] = paper_id
                                    logger.info("Updated task parameters with paper_id", 
                                            task_id=task.id, 
                                            paper_id=paper_id)
                                    break
        
        return parameters


    async def _execute_processing_pipeline(self,
                                        query: str,
                                        conversation_id: Optional[str],
                                        user_id: str,
                                        query_id: str) -> Dict[str, Any]:
        """Execute complete processing pipeline"""
        
        start_time = datetime.now()
        try:
            # 1. Get or create conversation context
            conversation = await self._get_or_create_conversation(
                conversation_id, user_id
            )
            
            # 2. Add user message through context_manager
            await self.context_manager.add_message(
                conversation.id, 
                "user", 
                query, 
                {"query_id": query_id}
            )
            
            # 3. Intent analysis
            logger.info("Starting intent analysis", query_id=query_id)
            intent_result = await self.intent_analyzer.analyze(
                query, 
                await self._extract_context_for_intent(conversation)
            )
            
            # 4. Check if clarification needed
            if intent_result.needs_clarification:
                clarification_response = self._create_clarification_response(intent_result)
                await self.context_manager.add_message(
                    conversation.id,
                    "assistant", 
                    clarification_response["content"]
                )
                await self.context_manager.update_conversation(conversation)
                return clarification_response
            
            # 5. Task orchestration
            logger.info("Creating task plan", query_id=query_id)
            task_plan = await self.task_orchestrator.create_plan(intent_result)
            
            # 6. Execute task plan
            logger.info("Executing task plan", 
                    query_id=query_id,
                    task_stats=task_plan.get_completion_stats())
            execution_results = await self._execute_task_plan(task_plan, query_id)
            
            # 7. Integrate response
            logger.info("Integrating response", query_id=query_id)
            final_response = await self.response_integrator.integrate(
                query,
                intent_result,
                execution_results,
                await self._extract_context_for_response(conversation)
            )
            
            # 8. Ensure final_response is dictionary type
            if not isinstance(final_response, dict):
                logger.warning("Response integrator returned non-dict result", 
                            result_type=type(final_response).__name__)
                final_response = {"content": str(final_response)}
            
            # Ensure content field exists
            if "content" not in final_response:
                final_response["content"] = "Sorry, I cannot generate an appropriate response."
            
            # 9. Add assistant reply through context_manager
            await self.context_manager.add_message(
                conversation.id,
                "assistant", 
                final_response["content"], 
                {
                    "query_id": query_id,
                    "intent_type": intent_result.primary_intent.type.value,
                    "confidence": intent_result.primary_intent.confidence,
                    "task_stats": task_plan.get_completion_stats()
                }
            )
            
            # 10. Save conversation
            await self.context_manager.update_conversation(conversation)
            
            # 11. Calculate processing time - Fix timezone issue
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # 12. Add query metadata
            final_response["query_id"] = query_id
            final_response["conversation_id"] = conversation.id
            final_response["task_execution_stats"] = task_plan.get_completion_stats()
            final_response["processing_time"] = processing_time
            
            logger.info("Query processing completed successfully", 
                    query_id=query_id,
                    processing_time=processing_time,
                    task_stats=final_response["task_execution_stats"])
            
            return final_response
            
        except Exception as e:
            logger.error("Processing pipeline failed", query_id=query_id, error=str(e))
            return self._create_error_response(str(e), query_id)


    def _create_clarification_response(self, intent_result: IntentAnalysisResult) -> Dict[str, Any]:
        """Create clarification response"""
        # Generate different clarification questions based on intent type
        intent_type = intent_result.primary_intent.type.value
        
        clarification_messages = {
            "search_papers": "What topic of papers would you like to search? Please provide more specific keywords.",
            "search_authors": "Which author's information would you like to find? Please provide the author's name.",
            "unknown": "Please provide more information so I can better understand your needs."
        }
        
        content = clarification_messages.get(intent_type, clarification_messages["unknown"])
        
        return {
            "content": content,
            "needs_clarification": True,
            "metadata": {
                "intent_type": intent_type,
                "confidence": intent_result.primary_intent.confidence
            }
        }

    def _create_error_response(self, error_message: str, query_id: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "content": f"Sorry, encountered a problem while processing your request: {error_message}",
            "error": True,
            "query_id": query_id,
            "metadata": {
                "error_message": error_message
            }
        }

    async def process_query(self, 
                          query: str, 
                          conversation_id: Optional[str] = None,
                          user_id: str = "default_user") -> Dict[str, Any]:
        """Main entry method for processing user queries"""
        # Generate query ID for tracking
        query_id = str(uuid.uuid4())
        
        try:
            logger.info("Starting query processing", 
                       query_id=query_id,
                       query=query,
                       conversation_id=conversation_id,
                       user_id=user_id)
            
            # Prevent duplicate processing
            if conversation_id and conversation_id in self.processing_queries:
                return {
                    "content": "Processing your previous request, please wait...",
                    "status": "processing"
                }
            
            if conversation_id:
                self.processing_queries[conversation_id] = True
            
            try:
                # Execute processing pipeline
                result = await self._execute_processing_pipeline(
                    query, conversation_id, user_id, query_id
                )
                
                return result
                
            finally:
                # Clean up processing status
                if conversation_id and conversation_id in self.processing_queries:
                    del self.processing_queries[conversation_id]
            
        except Exception as e:
            logger.error("Query processing failed", 
                        query_id=query_id,
                        error=str(e))
            return self._create_error_response(str(e), query_id)
    
    async def _get_or_create_conversation(self,
                                        conversation_id: Optional[str],
                                        user_id: str) -> Conversation:
        """Get or create conversation"""
        if conversation_id and conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]
        
        if conversation_id:
            # Try to load from database
            conversation = await self.context_manager.get_conversation(conversation_id)
            if conversation:
                self.active_conversations[conversation_id] = conversation
                return conversation
        
        # Create new conversation
        conversation = await self.context_manager.create_conversation(
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        self.active_conversations[conversation.id] = conversation
        return conversation

    async def get_task_plan_debug_info(self, query: str, user_id: str = "debug_user") -> Dict[str, Any]:
        """Get task plan debug information (for development and testing)"""
        try:
            # Create temporary conversation
            conversation = await self._get_or_create_conversation(None, user_id)
            
            # Intent analysis
            intent_result = await self.intent_analyzer.analyze(
                query, 
                await self._extract_context_for_intent(conversation)
            )
            
            # Create task plan
            task_plan = await self.task_orchestrator.create_plan(intent_result)
            
            # Return debug information
            debug_info = {
                "query": query,
                "intent_analysis": {
                    "primary_intent": {
                        "type": intent_result.primary_intent.type.value,
                        "confidence": intent_result.primary_intent.confidence,
                        "parameters": intent_result.primary_intent.parameters
                    },
                    "needs_clarification": intent_result.needs_clarification,
                    "clarification_questions": getattr(intent_result, 'clarification_questions', [])
                },
                "task_plan": task_plan.to_dict(),
                "execution_flow": self._analyze_execution_flow(task_plan)
            }
            
            return debug_info
            
        except Exception as e:
            logger.error("Failed to get task plan debug info", error=str(e))
            return {"error": str(e)}

    def _analyze_execution_flow(self, task_plan: TaskPlan) -> Dict[str, Any]:
        """Analyze task execution flow"""
        flow_info = {
            "total_tasks": len(task_plan.tasks),
            "parallel_tasks": [],
            "serial_tasks": [],
            "dependency_chains": [],
            "execution_phases": []
        }
        
        # Analyze parallel and serial tasks
        for task in task_plan.tasks:
            task_info = {
                "id": task.id,
                "name": task.name,
                "type": task.type.value,
                "dependencies": task.dependencies
            }
            
            if task.can_parallel:
                flow_info["parallel_tasks"].append(task_info)
            else:
                flow_info["serial_tasks"].append(task_info)
        
        # Analyze dependency chains
        dependency_chains = self._find_dependency_chains(task_plan.tasks)
        flow_info["dependency_chains"] = dependency_chains
        
        # Simulate execution phases
        execution_phases = self._simulate_execution_phases(task_plan)
        flow_info["execution_phases"] = execution_phases
        
        return flow_info

    def _find_dependency_chains(self, tasks: List[Task]) -> List[List[str]]:
        """Find dependency chains"""
        chains = []
        visited = set()
        
        for task in tasks:
            if task.id not in visited and not task.dependencies:
                # Build chain starting from tasks with no dependencies
                chain = self._build_chain(task, tasks, visited)
                if len(chain) > 1:
                    chains.append(chain)
        
        return chains

    def _build_chain(self, start_task: Task, all_tasks: List[Task], visited: set) -> List[str]:
        """Build dependency chain starting from specified task"""
        chain = [start_task.id]
        visited.add(start_task.id)
        
        # Find next task that depends on current task
        for task in all_tasks:
            if start_task.id in task.dependencies and task.id not in visited:
                chain.extend(self._build_chain(task, all_tasks, visited))
                break
        
        return chain

    def _simulate_execution_phases(self, task_plan: TaskPlan) -> List[Dict[str, Any]]:
        """Simulate execution phases"""
        phases = []
        completed_ids = set()
        phase_num = 1
        
        while len(completed_ids) < len(task_plan.tasks):
            ready_tasks = task_plan.get_ready_tasks(completed_ids)
            
            if not ready_tasks:
                break
            
            parallel_tasks = task_plan.get_parallel_tasks(ready_tasks)
            serial_tasks = task_plan.get_serial_tasks(ready_tasks)
            
            phase_info = {
                "phase": phase_num,
                "parallel_tasks": [{"id": t.id, "name": t.name} for t in parallel_tasks],
                "serial_tasks": [{"id": t.id, "name": t.name} for t in serial_tasks],
                "total_tasks_in_phase": len(ready_tasks)
            }
            
            phases.append(phase_info)
            
            # Simulate completing these tasks
            for task in ready_tasks:
                completed_ids.add(task.id)
            
            phase_num += 1
            
            # Prevent infinite loop
            if phase_num > 10:
                break
        
        return phases
    
    async def get_conversation_history(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation history"""
        try:
            conversation = await self.context_manager.get_conversation(conversation_id)
            if not conversation:
                return None
            
            return {
                "conversation_id": conversation.id,
                "user_id": conversation.user_id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "message_count": len(conversation.messages) if hasattr(conversation, 'messages') else 0,
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat(),
                        "metadata": msg.metadata
                    }
                    for msg in (conversation.messages if hasattr(conversation, 'messages') else [])
                ]
            }
            
        except Exception as e:
            logger.error("Failed to get conversation history", 
                        conversation_id=conversation_id,
                        error=str(e))
            return None
    
    async def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's conversation list"""
        try:
            conversations = await self.context_manager.get_user_conversations(user_id)
            
            return [
                {
                    "conversation_id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": len(conv.messages) if hasattr(conv, 'messages') else 0,
                    "last_message": conv.messages[-1].content if hasattr(conv, 'messages') and conv.messages else None
                }
                for conv in conversations
            ]
            
        except Exception as e:
            logger.error("Failed to get user conversations", user_id=user_id, error=str(e))
            return []
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Starting agent cleanup")
            
            # Save all active conversations
            for conversation in self.active_conversations.values():
                await self.context_manager.update_conversation(conversation)
            
            # Clean up context manager
            await self.context_manager.cleanup()
            
            # Clean up status
            self.active_conversations.clear()
            self.processing_queries.clear()
            
            logger.info("Agent cleanup completed")
            
        except Exception as e:
            logger.error("Error during agent cleanup", error=str(e))
            raise
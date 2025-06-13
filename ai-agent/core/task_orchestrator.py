"""
Task Orchestrator
"""
import uuid
from typing import List, Dict, Any
from models.intent import IntentAnalysisResult, IntentType
from models.task import Task, TaskPlan, TaskType, TaskStatus
from utils.logger import get_logger

logger = get_logger(__name__)

class TaskOrchestrator:
    """Task Orchestrator Class"""
    
    def __init__(self):
        self.intent_to_tools = self._build_intent_tool_mapping()
    
    async def create_plan(self, intent_result: IntentAnalysisResult) -> TaskPlan:
        """Create task execution plan based on intent analysis results"""
        try:
            logger.info("Creating task plan", intent=intent_result.primary_intent.type.value)
            
            # Create tasks based on primary intent
            primary_tasks = self._create_tasks_for_intent(intent_result.primary_intent)
            
            # Handle secondary intents (if any)
            # secondary_tasks = []
            # for secondary_intent in intent_result.secondary_intents:
            #     secondary_tasks.extend(self._create_tasks_for_intent(secondary_intent))
            
            # all_tasks = primary_tasks + secondary_tasks
            all_tasks = primary_tasks

            # Create simplified task plan
            task_plan = TaskPlan(tasks=all_tasks)
            
            logger.info("Task plan created", 
                       task_count=len(all_tasks),
                       stats=task_plan.get_completion_stats())
            
            return task_plan
            
        except Exception as e:
            logger.error("Failed to create task plan", error=str(e))
            raise
    
    def _build_intent_tool_mapping(self) -> Dict[IntentType, List[str]]:
        """Build intent to tool mapping relationship"""
        return {
            # Paper related
            IntentType.SEARCH_PAPERS: ["search_papers"],
            IntentType.GET_PAPER_DETAILS: ["get_paper_details"],
            IntentType.GET_PAPER_CITATIONS: ["get_paper_citations"],
            
            # Author related
            IntentType.SEARCH_AUTHORS: ["search_authors"],
            IntentType.GET_AUTHOR_DETAILS: ["search_authors"],
            IntentType.GET_AUTHOR_PAPERS: ["get_author_papers"],
            
            # Network analysis
            IntentType.CITATION_NETWORK: ["get_paper_citations"],
            IntentType.COLLABORATION_NETWORK: ["search_authors"],  # Use search authors as alternative
            
            # Trend analysis
            IntentType.GET_TRENDING_PAPERS: ["get_trending_papers"],
            IntentType.GET_TOP_KEYWORDS: ["get_top_keywords"],
            IntentType.RESEARCH_TRENDS: ["get_trending_papers"],
            IntentType.RESEARCH_LANDSCAPE: ["get_trending_papers"],

            # General chat - no tool calls needed
            IntentType.GENERAL_CHAT: [],
            
            # Unknown intent - no tool calls needed
            IntentType.UNKNOWN: [],
        }

    
    def _create_tasks_for_intent(self, intent) -> List[Task]:
        """Create task list for specific intent"""
        tasks = []
        
        # Special handling for compound intents
        # if intent.type == IntentType.PAPER_REVIEW:
        #     tasks = self._create_paper_review_tasks(intent)
        # elif intent.type == IntentType.PAPER_GENERATION:
        #     tasks = self._create_paper_generation_tasks(intent)
        # else:
            # Simple intent: direct mapping to tools
        tools = self.intent_to_tools.get(intent.type, [])
        for tool_name in tools:
            task = Task(
                id=str(uuid.uuid4()),
                type=TaskType.MCP_TOOL_CALL,
                name=f"Call {tool_name}",
                parameters=self._prepare_tool_parameters(tool_name, intent.parameters),
                dependencies=[],  # No dependencies for simple tasks
                can_parallel=True  # Simple tasks can be parallel
            )
            tasks.append(task)
        
        return tasks
    
    def _create_paper_review_tasks(self, intent) -> List[Task]:
        """Create paper review task sequence - with dependencies"""
        tasks = []
        
        # 1. Search related papers
        search_task = Task(
            id=str(uuid.uuid4()),
            type=TaskType.MCP_TOOL_CALL,
            name="Search papers for review",
            parameters=self._prepare_tool_parameters("search_papers", intent.parameters),
            dependencies=[],  # No dependencies
            can_parallel=True
        )
        tasks.append(search_task)
        
        # 2. Get paper details (depends on search results)
        details_task = Task(
            id=str(uuid.uuid4()),
            type=TaskType.MCP_TOOL_CALL,
            name="Get paper details for review",
            parameters={
                "tool_name": "get_paper_details",
                "arguments": {}  # Parameters will be obtained from search results at runtime
            },
            dependencies=[search_task.id],  # Depends on search task
            can_parallel=False  # Has dependencies, cannot be parallel
        )
        tasks.append(details_task)
        
        return tasks
    
    def _create_paper_generation_tasks(self, intent) -> List[Task]:
        """Create paper generation task sequence - can be parallel"""
        tasks = []
        
        # 1. Analyze research trends
        trend_task = Task(
            id=str(uuid.uuid4()),
            type=TaskType.MCP_TOOL_CALL,
            name="Analyze research trends",
            parameters=self._prepare_tool_parameters("get_research_trends", intent.parameters),
            dependencies=[],
            can_parallel=True  # Can be parallel with search task
        )
        tasks.append(trend_task)
        
        # 2. Search related papers
        search_task = Task(
            id=str(uuid.uuid4()),
            type=TaskType.MCP_TOOL_CALL,
            name="Search papers for generation",
            parameters=self._prepare_tool_parameters("search_papers", intent.parameters),
            dependencies=[],
            can_parallel=True  # Can be parallel with trend analysis
        )
        tasks.append(search_task)
        
        return tasks
    
    def _prepare_tool_parameters(self, tool_name: str, intent_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for tool calls"""
        # Return standardized parameter format, including tool name and parameters
        tool_arguments = {}
        
        if tool_name == "search_papers":
            tool_arguments = {
                "query": intent_parameters.get("query", ""),
                "limit": intent_parameters.get("limit", 6),
                "format": "json",
                "fields": intent_parameters.get("fields", ["title", "abstract", "authors"])
            }
        elif tool_name == "get_paper_details":
            tool_arguments = {
                "title": intent_parameters.get("paper_title", ""),
                "include_citations": intent_parameters.get("include_citations", True)
            }
        elif tool_name == "search_authors":
            tool_arguments = {
                "query": intent_parameters.get("author_name", ""),
                "limit": intent_parameters.get("limit", 6)
            }
        # elif tool_name == "get_author_details":
        #     tool_arguments = {
        #         "query": intent_parameters.get("author_name", intent_parameters.get("query", "")),
        #         "limit": intent_parameters.get("limit", 10),
        #         "include_coauthors": intent_parameters.get("include_coauthors", True)
        #     }
        elif tool_name == "get_citation_network":
            tool_arguments = {
                "title": intent_parameters.get("paper_title", ""),
                "depth": intent_parameters.get("depth", 2)
            }
        elif tool_name == "get_collaboration_network":
            tool_arguments = {
                "author_id": intent_parameters.get("author_id", ""),
                "depth": intent_parameters.get("depth", 2)
            }
        elif tool_name == "get_research_trends":
            tool_arguments = {
                "field": intent_parameters.get("field", ""),
                "time_range": intent_parameters.get("time_range", "5years")
            }
        elif tool_name == "analyze_research_landscape":
            tool_arguments = {
                "domain": intent_parameters.get("domain", ""),
                "analysis_type": intent_parameters.get("analysis_type", "overview")
            }
        
        # Return standardized format
        return {
            "tool_name": tool_name,
            "arguments": tool_arguments
        }
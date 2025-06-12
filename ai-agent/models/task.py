"""
Task execution related models - Simplified version (Plan 1)
"""
from enum import Enum
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from pydantic import BaseModel, Field
from dataclasses import dataclass, field

class TaskType(Enum):
    """Task type enumeration"""
    # MCP tool call task
    MCP_TOOL_CALL = "mcp_tool_call"
    
    # LLM processing task
    LLM_GENERATION = "llm_generation"
    
    # Response generation task
    RESPONSE_GENERATION = "response_generation"

class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    """Single task - Including dependency and parallel information"""
    id: str
    type: TaskType
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    timeout: int = 30  # Timeout (seconds)
    
    # New: Dependency and parallel control
    dependencies: List[str] = field(default_factory=list)  # List of dependent task IDs
    can_parallel: bool = True  # Whether can be executed in parallel
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "parameters": self.parameters,
            "status": self.status.value,
            "timeout": self.timeout,
            "dependencies": self.dependencies,
            "can_parallel": self.can_parallel,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message
        }
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get execution time (seconds)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def is_ready(self, completed_task_ids: Set[str]) -> bool:
        """Check if task can be executed (dependencies satisfied)"""
        if self.status != TaskStatus.PENDING:
            return False
        return all(dep_id in completed_task_ids for dep_id in self.dependencies)
    
    def mark_started(self):
        """Mark task as started"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
    
    def mark_completed(self):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def mark_failed(self, error_message: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message

class TaskResult(BaseModel):
    """Task execution result"""
    task_id: str
    status: TaskStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        """Check if task is successful"""
        return self.status == TaskStatus.COMPLETED and self.error is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "is_success": self.is_success
        }

class TaskPlan:
    """Simplified task plan - Only contains task list"""
    
    def __init__(self, tasks: List[Task]):
        self.tasks = tasks
        self.created_at = datetime.now()
    
    def get_ready_tasks(self, completed_task_ids: Set[str]) -> List[Task]:
        """Get executable tasks (dependencies satisfied)"""
        ready_tasks = []
        for task in self.tasks:
            if task.is_ready(completed_task_ids):
                ready_tasks.append(task)
        return ready_tasks
    
    def get_parallel_tasks(self, ready_tasks: List[Task]) -> List[Task]:
        """Filter tasks that can be executed in parallel from ready tasks"""
        return [task for task in ready_tasks if task.can_parallel]
    
    def get_serial_tasks(self, ready_tasks: List[Task]) -> List[Task]:
        """Filter tasks that must be executed serially from ready tasks"""
        return [task for task in ready_tasks if not task.can_parallel]
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        return [task for task in self.tasks if task.status == TaskStatus.PENDING]
    
    def get_completed_tasks(self) -> List[Task]:
        """Get all completed tasks"""
        return [task for task in self.tasks if task.status == TaskStatus.COMPLETED]
    
    def get_failed_tasks(self) -> List[Task]:
        """Get all failed tasks"""
        return [task for task in self.tasks if task.status == TaskStatus.FAILED]
    
    def is_completed(self) -> bool:
        """Check if all tasks are completed (success or failure)"""
        return all(task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] for task in self.tasks)
    
    def get_completion_stats(self) -> Dict[str, int]:
        """Get completion statistics"""
        stats = {
            "total": len(self.tasks),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0
        }
        
        for task in self.tasks:
            stats[task.status.value] += 1
        
        return stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "created_at": self.created_at.isoformat(),
            "task_count": len(self.tasks),
            "tasks": [task.to_dict() for task in self.tasks],
            "completion_stats": self.get_completion_stats()
        }

# Task builder class - Updated to support dependency and parallel control
class TaskBuilder:
    """Task builder"""
    
    @staticmethod
    def mcp_tool_call(tool_name: str, arguments: Dict[str, Any], 
                     task_id: str = None, dependencies: List[str] = None,
                     can_parallel: bool = True) -> Task:
        """Create MCP tool call task"""
        return Task(
            id=task_id or f"mcp_{tool_name}_{datetime.now().strftime('%H%M%S')}",
            type=TaskType.MCP_TOOL_CALL,
            name=f"Call MCP tool: {tool_name}",
            parameters={
                "tool_name": tool_name,
                "arguments": arguments
            },
            dependencies=dependencies or [],
            can_parallel=can_parallel
        )
    
    @staticmethod
    def llm_generation(prompt: str, model_params: Dict[str, Any] = None,
                      task_id: str = None, dependencies: List[str] = None,
                      can_parallel: bool = True) -> Task:
        """Create LLM generation task"""
        return Task(
            id=task_id or f"llm_gen_{datetime.now().strftime('%H%M%S')}",
            type=TaskType.LLM_GENERATION,
            name="LLM text generation",
            parameters={
                "prompt": prompt,
                "model_params": model_params or {}
            },
            dependencies=dependencies or [],
            can_parallel=can_parallel
        )
    
    @staticmethod
    def response_generation(content: str, format_type: str = "text",
                           task_id: str = None, dependencies: List[str] = None,
                           can_parallel: bool = False) -> Task:
        """Create response generation task"""
        return Task(
            id=task_id or f"resp_gen_{datetime.now().strftime('%H%M%S')}",
            type=TaskType.RESPONSE_GENERATION,
            name="Generate response",
            parameters={
                "content": content,
                "format_type": format_type
            },
            dependencies=dependencies or [],
            can_parallel=can_parallel  # Response generation usually needs to wait for all data to be collected
        )
    
    @staticmethod
    def create_dependent_chain(tasks_config: List[Dict[str, Any]]) -> List[Task]:
        """Create dependent chain tasks"""
        tasks = []
        previous_task_id = None
        
        for i, config in enumerate(tasks_config):
            dependencies = [previous_task_id] if previous_task_id else []
            
            task = Task(
                id=config.get("id", f"task_{i}_{datetime.now().strftime('%H%M%S')}"),
                type=TaskType(config["type"]),
                name=config["name"],
                parameters=config.get("parameters", {}),
                dependencies=dependencies,
                can_parallel=config.get("can_parallel", False)  # Chain tasks cannot be parallel by default
            )
            
            tasks.append(task)
            previous_task_id = task.id
        
        return tasks
    
    @staticmethod
    def create_parallel_group(tasks_config: List[Dict[str, Any]], 
                             shared_dependencies: List[str] = None) -> List[Task]:
        """Create parallel task group"""
        tasks = []
        
        for i, config in enumerate(tasks_config):
            task = Task(
                id=config.get("id", f"parallel_{i}_{datetime.now().strftime('%H%M%S')}"),
                type=TaskType(config["type"]),
                name=config["name"],
                parameters=config.get("parameters", {}),
                dependencies=shared_dependencies or [],
                can_parallel=True  # Tasks in parallel group can be executed in parallel
            )
            
            tasks.append(task)
        
        return tasks

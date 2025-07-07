"""TASK tool for task decomposition and orchestration."""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from ..core.base import Tool, ToolResult, ExecutionContext


@dataclass
class TaskStep:
    """A single step in a task plan."""
    id: str
    title: str
    description: str
    tool_name: str
    tool_params: Dict[str, Any]
    status: str  # 'pending', 'in_progress', 'completed', 'failed', 'skipped'
    dependencies: List[str]  # List of step IDs that must complete first
    estimated_duration: Optional[int] = None  # minutes
    actual_duration: Optional[int] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


@dataclass
class TaskPlan:
    """A complete task execution plan."""
    id: str
    title: str
    description: str
    status: str  # 'draft', 'ready', 'in_progress', 'completed', 'failed', 'paused'
    steps: List[TaskStep]
    created_at: str
    updated_at: str
    estimated_total_duration: Optional[int] = None
    actual_total_duration: Optional[int] = None
    success_criteria: List[str] = None
    failure_conditions: List[str] = None
    
    def __post_init__(self):
        if self.success_criteria is None:
            self.success_criteria = []
        if self.failure_conditions is None:
            self.failure_conditions = []


class TaskTool(Tool):
    """Tool for task decomposition and orchestration."""
    
    def __init__(self):
        super().__init__(
            name="task",
            description="Decompose complex tasks and create execution plans"
        )
        self.plans_file = "agent_task_plans.json"
        self.templates_file = "agent_task_templates.json"
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        action = kwargs.get("action")
        
        if not action or action not in [
            "decompose_task", "create_plan", "execute_plan", "get_plan",
            "list_plans", "update_step", "add_step", "remove_step",
            "save_template", "load_template", "get_next_steps", "validate_plan"
        ]:
            return False
        
        # Action-specific validation
        if action == "decompose_task":
            return "description" in kwargs
        
        if action == "create_plan":
            return "title" in kwargs
        
        if action in ["execute_plan", "get_plan", "update_step", "add_step"]:
            return "plan_id" in kwargs
        
        if action == "update_step":
            return "step_id" in kwargs
        
        if action in ["save_template", "load_template"]:
            return "template_name" in kwargs
        
        return True
    
    def execute(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Execute the task tool."""
        if not self.validate_input(**kwargs):
            return ToolResult(
                success=False,
                data=None,
                error="Invalid input parameters"
            )
        
        action = kwargs["action"]
        
        try:
            if action == "decompose_task":
                return self._decompose_task(context, **kwargs)
            elif action == "create_plan":
                return self._create_plan(context, **kwargs)
            elif action == "execute_plan":
                return self._execute_plan(context, **kwargs)
            elif action == "get_plan":
                return self._get_plan(context, **kwargs)
            elif action == "list_plans":
                return self._list_plans(context, **kwargs)
            elif action == "update_step":
                return self._update_step(context, **kwargs)
            elif action == "add_step":
                return self._add_step(context, **kwargs)
            elif action == "remove_step":
                return self._remove_step(context, **kwargs)
            elif action == "save_template":
                return self._save_template(context, **kwargs)
            elif action == "load_template":
                return self._load_template(context, **kwargs)
            elif action == "get_next_steps":
                return self._get_next_steps(context, **kwargs)
            elif action == "validate_plan":
                return self._validate_plan(context, **kwargs)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error executing task tool: {str(e)}"
            )
    
    def _get_plans_file_path(self, context: ExecutionContext) -> Path:
        """Get the path to the plans file."""
        return Path(context.working_directory) / self.plans_file
    
    def _get_templates_file_path(self, context: ExecutionContext) -> Path:
        """Get the path to the templates file."""
        return Path(context.working_directory) / self.templates_file
    
    def _load_plans(self, context: ExecutionContext) -> Dict[str, TaskPlan]:
        """Load task plans from file."""
        plans_path = self._get_plans_file_path(context)
        
        if not plans_path.exists():
            return {}
        
        try:
            with open(plans_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            plans = {}
            for plan_id, plan_data in data.items():
                # Convert steps
                steps = []
                for step_data in plan_data.get("steps", []):
                    steps.append(TaskStep(**step_data))
                
                plan_data["steps"] = steps
                plans[plan_id] = TaskPlan(**plan_data)
            
            return plans
        except Exception:
            return {}
    
    def _save_plans(self, context: ExecutionContext, plans: Dict[str, TaskPlan]) -> bool:
        """Save task plans to file."""
        plans_path = self._get_plans_file_path(context)
        
        try:
            data = {}
            for plan_id, plan in plans.items():
                plan_dict = asdict(plan)
                # Convert steps to dicts
                plan_dict["steps"] = [asdict(step) for step in plan.steps]
                data[plan_id] = plan_dict
            
            with open(plans_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def _decompose_task(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Decompose a complex task into steps."""
        description = kwargs["description"]
        context_info = kwargs.get("context", "")
        task_type = kwargs.get("task_type", "general")
        
        try:
            # Task decomposition logic based on common patterns
            steps = self._analyze_and_decompose(description, context_info, task_type)
            
            # Create a draft plan
            plan_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            plan = TaskPlan(
                id=plan_id,
                title=f"Task: {description[:50]}...",
                description=description,
                status="draft",
                steps=steps,
                created_at=now,
                updated_at=now
            )
            
            # Save the plan
            plans = self._load_plans(context)
            plans[plan_id] = plan
            
            if not self._save_plans(context, plans):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to save decomposed task plan"
                )
            
            return ToolResult(
                success=True,
                data={
                    "plan_id": plan_id,
                    "plan": asdict(plan),
                    "step_count": len(steps)
                },
                metadata={
                    "task_type": task_type,
                    "decomposition_method": "pattern_based"
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error decomposing task: {str(e)}"
            )
    
    def _analyze_and_decompose(self, description: str, context: str, task_type: str) -> List[TaskStep]:
        """Analyze task and decompose into steps."""
        steps = []
        step_counter = 1
        
        # Common task patterns and their decomposition
        desc_lower = description.lower()
        
        if "implement" in desc_lower or "create" in desc_lower or "build" in desc_lower:
            # Development task pattern
            steps.extend(self._decompose_development_task(description, step_counter))
        elif "analyze" in desc_lower or "research" in desc_lower or "investigate" in desc_lower:
            # Analysis task pattern
            steps.extend(self._decompose_analysis_task(description, step_counter))
        elif "fix" in desc_lower or "debug" in desc_lower or "resolve" in desc_lower:
            # Bug fix task pattern
            steps.extend(self._decompose_bugfix_task(description, step_counter))
        elif "refactor" in desc_lower or "improve" in desc_lower or "optimize" in desc_lower:
            # Refactoring task pattern
            steps.extend(self._decompose_refactor_task(description, step_counter))
        else:
            # Generic task pattern
            steps.extend(self._decompose_generic_task(description, step_counter))
        
        return steps
    
    def _decompose_development_task(self, description: str, start_counter: int) -> List[TaskStep]:
        """Decompose a development task."""
        steps = []
        counter = start_counter
        
        # Research and planning
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Research and understand requirements",
            description="Research existing codebase and understand requirements",
            tool_name="find",
            tool_params={"action": "search_content", "query": "related functionality"},
            status="pending",
            dependencies=[],
            estimated_duration=30
        ))
        counter += 1
        
        # Design
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Create design plan",
            description="Design the implementation approach",
            tool_name="todo",
            tool_params={"action": "create_todo", "title": "Design implementation"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=20
        ))
        counter += 1
        
        # Implementation
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Implement core functionality",
            description="Write the main implementation code",
            tool_name="write",
            tool_params={"action": "write_file", "path": "implementation.py"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=120
        ))
        counter += 1
        
        # Testing
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Test implementation",
            description="Run tests and verify functionality",
            tool_name="execute",
            tool_params={"command": "python -m pytest tests/"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=30
        ))
        
        return steps
    
    def _decompose_analysis_task(self, description: str, start_counter: int) -> List[TaskStep]:
        """Decompose an analysis task."""
        steps = []
        counter = start_counter
        
        # Gather information
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Gather relevant files",
            description="Find and collect relevant files for analysis",
            tool_name="find",
            tool_params={"action": "find_files", "pattern": "*"},
            status="pending",
            dependencies=[],
            estimated_duration=15
        ))
        counter += 1
        
        # Analyze content
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Analyze code content",
            description="Read and analyze the content of relevant files",
            tool_name="read",
            tool_params={"action": "read_file"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=45
        ))
        counter += 1
        
        # Document findings
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Document analysis results",
            description="Create documentation of analysis findings",
            tool_name="write",
            tool_params={"action": "write_file", "path": "analysis_results.md"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=30
        ))
        
        return steps
    
    def _decompose_bugfix_task(self, description: str, start_counter: int) -> List[TaskStep]:
        """Decompose a bug fix task."""
        steps = []
        counter = start_counter
        
        # Reproduce bug
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Reproduce the bug",
            description="Identify and reproduce the reported bug",
            tool_name="execute",
            tool_params={"command": "python reproduce_bug.py"},
            status="pending",
            dependencies=[],
            estimated_duration=20
        ))
        counter += 1
        
        # Locate bug source
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Locate bug source",
            description="Find the source code causing the bug",
            tool_name="find",
            tool_params={"action": "search_content", "query": "error pattern"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=30
        ))
        counter += 1
        
        # Fix the bug
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Implement bug fix",
            description="Fix the identified bug in the code",
            tool_name="update",
            tool_params={"action": "replace_pattern"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=45
        ))
        counter += 1
        
        # Verify fix
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Verify bug fix",
            description="Test that the bug is fixed and no regressions",
            tool_name="execute",
            tool_params={"command": "python -m pytest"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=20
        ))
        
        return steps
    
    def _decompose_refactor_task(self, description: str, start_counter: int) -> List[TaskStep]:
        """Decompose a refactoring task."""
        steps = []
        counter = start_counter
        
        # Analyze current code
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Analyze current implementation",
            description="Understand the current code structure",
            tool_name="read",
            tool_params={"action": "read_file"},
            status="pending",
            dependencies=[],
            estimated_duration=30
        ))
        counter += 1
        
        # Plan refactoring
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Plan refactoring approach",
            description="Design the refactoring strategy",
            tool_name="todo",
            tool_params={"action": "create_todo", "title": "Refactoring plan"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=20
        ))
        counter += 1
        
        # Implement refactoring
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Implement refactoring",
            description="Apply the refactoring changes",
            tool_name="update",
            tool_params={"action": "replace_function"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=90
        ))
        counter += 1
        
        # Test refactored code
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Test refactored code",
            description="Ensure refactoring didn't break functionality",
            tool_name="execute",
            tool_params={"command": "python -m pytest"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=25
        ))
        
        return steps
    
    def _decompose_generic_task(self, description: str, start_counter: int) -> List[TaskStep]:
        """Decompose a generic task."""
        steps = []
        counter = start_counter
        
        # Understanding phase
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Understand task requirements",
            description="Analyze and understand what needs to be done",
            tool_name="read",
            tool_params={"action": "list_directory", "path": "."},
            status="pending",
            dependencies=[],
            estimated_duration=15
        ))
        counter += 1
        
        # Planning phase
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Create execution plan",
            description="Plan how to accomplish the task",
            tool_name="todo",
            tool_params={"action": "create_todo", "title": f"Execute: {description}"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=10
        ))
        counter += 1
        
        # Execution phase
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Execute main task",
            description="Perform the main task execution",
            tool_name="execute",
            tool_params={"command": "echo 'Task execution placeholder'"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=60
        ))
        counter += 1
        
        # Verification phase
        steps.append(TaskStep(
            id=f"step_{counter}",
            title="Verify task completion",
            description="Verify that the task was completed successfully",
            tool_name="read",
            tool_params={"action": "file_exists", "path": "result.txt"},
            status="pending",
            dependencies=[f"step_{counter-1}"],
            estimated_duration=10
        ))
        
        return steps
    
    def _create_plan(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Create a new task plan manually."""
        title = kwargs["title"]
        description = kwargs.get("description", "")
        steps_data = kwargs.get("steps", [])
        
        try:
            plan_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Convert steps data to TaskStep objects
            steps = []
            for i, step_data in enumerate(steps_data):
                step_id = step_data.get("id", f"step_{i+1}")
                steps.append(TaskStep(
                    id=step_id,
                    title=step_data.get("title", f"Step {i+1}"),
                    description=step_data.get("description", ""),
                    tool_name=step_data.get("tool_name", "execute"),
                    tool_params=step_data.get("tool_params", {}),
                    status="pending",
                    dependencies=step_data.get("dependencies", []),
                    estimated_duration=step_data.get("estimated_duration")
                ))
            
            plan = TaskPlan(
                id=plan_id,
                title=title,
                description=description,
                status="ready",
                steps=steps,
                created_at=now,
                updated_at=now
            )
            
            plans = self._load_plans(context)
            plans[plan_id] = plan
            
            if not self._save_plans(context, plans):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to save task plan"
                )
            
            return ToolResult(
                success=True,
                data=asdict(plan),
                metadata={"plan_id": plan_id}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error creating plan: {str(e)}"
            )
    
    def _get_next_steps(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Get the next executable steps from a plan."""
        plan_id = kwargs["plan_id"]
        
        try:
            plans = self._load_plans(context)
            
            if plan_id not in plans:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Plan not found: {plan_id}"
                )
            
            plan = plans[plan_id]
            next_steps = []
            
            for step in plan.steps:
                if step.status == "pending":
                    # Check if all dependencies are completed
                    dependencies_met = True
                    for dep_id in step.dependencies:
                        dep_step = next((s for s in plan.steps if s.id == dep_id), None)
                        if not dep_step or dep_step.status != "completed":
                            dependencies_met = False
                            break
                    
                    if dependencies_met:
                        next_steps.append(asdict(step))
            
            return ToolResult(
                success=True,
                data=next_steps,
                metadata={
                    "plan_id": plan_id,
                    "available_steps": len(next_steps)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error getting next steps: {str(e)}"
            )
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["decompose_task", "create_plan", "execute_plan", "get_plan", "list_plans", "update_step", "add_step", "remove_step", "save_template", "load_template", "get_next_steps", "validate_plan"],
                    "description": "Action to perform"
                },
                "description": {
                    "type": "string",
                    "description": "Task description to decompose"
                },
                "title": {
                    "type": "string",
                    "description": "Plan title"
                },
                "plan_id": {
                    "type": "string",
                    "description": "Plan ID"
                },
                "step_id": {
                    "type": "string",
                    "description": "Step ID"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context for task decomposition"
                },
                "task_type": {
                    "type": "string",
                    "description": "Type of task (development, analysis, bugfix, refactor, generic)",
                    "default": "generic"
                },
                "steps": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of step definitions"
                },
                "template_name": {
                    "type": "string",
                    "description": "Template name"
                }
            },
            "required": ["action"]
        }
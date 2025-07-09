"""TODO tool for task management and planning."""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from ..core.base import Tool, ToolResult, ExecutionContext


@dataclass
class TodoItem:
    """A single todo item."""
    id: str
    title: str
    description: str
    status: str  # 'pending', 'in_progress', 'completed', 'blocked'
    priority: str  # 'low', 'medium', 'high', 'critical'
    created_at: str
    updated_at: str
    due_date: Optional[str] = None
    tags: List[str] = None
    subtasks: List[str] = None  # List of subtask IDs
    parent_id: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    # Tool execution fields
    tool_name: Optional[str] = None
    tool_params: Dict[str, Any] = None
    auto_expand: bool = True
    execution_result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.subtasks is None:
            self.subtasks = []
        if self.tool_params is None:
            self.tool_params = {}


class TodoTool(Tool):
    """Tool for managing todos and tasks."""
    
    def __init__(self, tool_registry=None, llm_provider=None):
        super().__init__(
            name="todo",
            description="Manage todos and tasks with planning capabilities"
        )
        self.todo_file = "agent_todos.json"
        self.tool_registry = tool_registry
        self.llm_provider = llm_provider
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        action = kwargs.get("action")
        
        if not action or action not in [
            "create_todo", "list_todos", "update_todo", "delete_todo",
            "add_subtask", "get_todo", "search_todos", "get_stats",
            "execute_todo", "auto_expand_todo", "get_next_executable_todos"
        ]:
            return False
        
        # Action-specific validation
        if action == "create_todo":
            return "title" in kwargs
        
        if action in ["update_todo", "delete_todo", "get_todo", "add_subtask"]:
            return "todo_id" in kwargs
        
        if action == "add_subtask":
            return "subtask_title" in kwargs
        
        if action in ["execute_todo", "auto_expand_todo"]:
            return "todo_id" in kwargs
        
        return True
    
    def execute(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Execute the todo tool."""
        if not self.validate_input(**kwargs):
            return ToolResult(
                success=False,
                data=None,
                error="Invalid input parameters"
            )
        
        action = kwargs["action"]
        
        try:
            if action == "create_todo":
                return self._create_todo(context, **kwargs)
            elif action == "list_todos":
                return self._list_todos(context, **kwargs)
            elif action == "update_todo":
                return self._update_todo(context, **kwargs)
            elif action == "delete_todo":
                return self._delete_todo(context, **kwargs)
            elif action == "add_subtask":
                return self._add_subtask(context, **kwargs)
            elif action == "get_todo":
                return self._get_todo(context, **kwargs)
            elif action == "search_todos":
                return self._search_todos(context, **kwargs)
            elif action == "get_stats":
                return self._get_stats(context, **kwargs)
            elif action == "execute_todo":
                return self._execute_todo(context, **kwargs)
            elif action == "auto_expand_todo":
                return self._auto_expand_todo(context, **kwargs)
            elif action == "get_next_executable_todos":
                return self._get_next_executable_todos(context, **kwargs)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error executing todo tool: {str(e)}"
            )
    
    def _get_todo_file_path(self, context: ExecutionContext) -> Path:
        """Get the path to the todo file."""
        return Path(context.working_directory) / self.todo_file
    
    def _load_todos(self, context: ExecutionContext) -> Dict[str, TodoItem]:
        """Load todos from file."""
        todo_path = self._get_todo_file_path(context)
        
        if not todo_path.exists():
            return {}
        
        try:
            with open(todo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            todos = {}
            for todo_id, todo_data in data.items():
                todos[todo_id] = TodoItem(**todo_data)
            
            return todos
        except Exception:
            return {}
    
    def _save_todos(self, context: ExecutionContext, todos: Dict[str, TodoItem]) -> bool:
        """Save todos to file."""
        todo_path = self._get_todo_file_path(context)
        
        try:
            data = {todo_id: asdict(todo) for todo_id, todo in todos.items()}
            
            with open(todo_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def _create_todo(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Create a new todo item."""
        title = kwargs["title"]
        description = kwargs.get("description", "")
        priority = kwargs.get("priority", "medium")
        due_date = kwargs.get("due_date")
        tags = kwargs.get("tags", [])
        estimated_hours = kwargs.get("estimated_hours")
        
        # Validate priority
        if priority not in ["low", "medium", "high", "critical"]:
            return ToolResult(
                success=False,
                data=None,
                error="Priority must be one of: low, medium, high, critical"
            )
        
        try:
            todos = self._load_todos(context)
            
            # Create new todo
            todo_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            todo = TodoItem(
                id=todo_id,
                title=title,
                description=description,
                status="pending",
                priority=priority,
                created_at=now,
                updated_at=now,
                due_date=due_date,
                tags=tags if isinstance(tags, list) else [],
                estimated_hours=estimated_hours
            )
            
            todos[todo_id] = todo
            
            if not self._save_todos(context, todos):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to save todo"
                )
            
            return ToolResult(
                success=True,
                data=asdict(todo),
                metadata={
                    "todo_id": todo_id,
                    "action": "created"
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error creating todo: {str(e)}"
            )
    
    def _list_todos(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """List todos with optional filtering."""
        status_filter = kwargs.get("status")
        priority_filter = kwargs.get("priority")
        tag_filter = kwargs.get("tag")
        include_subtasks = kwargs.get("include_subtasks", True)
        
        try:
            todos = self._load_todos(context)
            
            # Apply filters
            filtered_todos = []
            for todo in todos.values():
                # Skip subtasks if not requested
                if not include_subtasks and todo.parent_id:
                    continue
                
                # Status filter
                if status_filter and todo.status != status_filter:
                    continue
                
                # Priority filter
                if priority_filter and todo.priority != priority_filter:
                    continue
                
                # Tag filter
                if tag_filter and tag_filter not in todo.tags:
                    continue
                
                filtered_todos.append(asdict(todo))
            
            # Sort by priority and created date
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            filtered_todos.sort(key=lambda x: (priority_order.get(x["priority"], 4), x["created_at"]))
            
            return ToolResult(
                success=True,
                data=filtered_todos,
                metadata={
                    "total_count": len(filtered_todos),
                    "filters": {
                        "status": status_filter,
                        "priority": priority_filter,
                        "tag": tag_filter
                    }
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error listing todos: {str(e)}"
            )
    
    def _update_todo(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Update an existing todo."""
        todo_id = kwargs["todo_id"]
        
        try:
            todos = self._load_todos(context)
            
            if todo_id not in todos:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Todo not found: {todo_id}"
                )
            
            todo = todos[todo_id]
            
            # Update fields
            if "title" in kwargs:
                todo.title = kwargs["title"]
            if "description" in kwargs:
                todo.description = kwargs["description"]
            if "status" in kwargs:
                if kwargs["status"] not in ["pending", "in_progress", "completed", "blocked"]:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="Status must be one of: pending, in_progress, completed, blocked"
                    )
                todo.status = kwargs["status"]
            if "priority" in kwargs:
                if kwargs["priority"] not in ["low", "medium", "high", "critical"]:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="Priority must be one of: low, medium, high, critical"
                    )
                todo.priority = kwargs["priority"]
            if "due_date" in kwargs:
                todo.due_date = kwargs["due_date"]
            if "tags" in kwargs:
                todo.tags = kwargs["tags"] if isinstance(kwargs["tags"], list) else []
            if "estimated_hours" in kwargs:
                todo.estimated_hours = kwargs["estimated_hours"]
            if "actual_hours" in kwargs:
                todo.actual_hours = kwargs["actual_hours"]
            
            todo.updated_at = datetime.now().isoformat()
            
            if not self._save_todos(context, todos):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to save updated todo"
                )
            
            return ToolResult(
                success=True,
                data=asdict(todo),
                metadata={
                    "todo_id": todo_id,
                    "action": "updated"
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error updating todo: {str(e)}"
            )
    
    def _delete_todo(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Delete a todo item."""
        todo_id = kwargs["todo_id"]
        
        try:
            todos = self._load_todos(context)
            
            if todo_id not in todos:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Todo not found: {todo_id}"
                )
            
            todo = todos[todo_id]
            
            # Delete subtasks first
            subtasks_deleted = []
            for subtask_id in todo.subtasks:
                if subtask_id in todos:
                    del todos[subtask_id]
                    subtasks_deleted.append(subtask_id)
            
            # Delete main todo
            del todos[todo_id]
            
            if not self._save_todos(context, todos):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to save after deletion"
                )
            
            return ToolResult(
                success=True,
                data={
                    "deleted_todo": asdict(todo),
                    "deleted_subtasks": subtasks_deleted
                },
                metadata={
                    "todo_id": todo_id,
                    "action": "deleted",
                    "subtasks_deleted": len(subtasks_deleted)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error deleting todo: {str(e)}"
            )
    
    def _add_subtask(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Add a subtask to an existing todo."""
        todo_id = kwargs["todo_id"]
        subtask_title = kwargs["subtask_title"]
        subtask_description = kwargs.get("subtask_description", "")
        
        try:
            todos = self._load_todos(context)
            
            if todo_id not in todos:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Parent todo not found: {todo_id}"
                )
            
            parent_todo = todos[todo_id]
            
            # Create subtask
            subtask_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            subtask = TodoItem(
                id=subtask_id,
                title=subtask_title,
                description=subtask_description,
                status="pending",
                priority=parent_todo.priority,  # Inherit priority
                created_at=now,
                updated_at=now,
                parent_id=todo_id,
                tags=parent_todo.tags.copy()  # Inherit tags
            )
            
            todos[subtask_id] = subtask
            parent_todo.subtasks.append(subtask_id)
            parent_todo.updated_at = now
            
            if not self._save_todos(context, todos):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to save subtask"
                )
            
            return ToolResult(
                success=True,
                data=asdict(subtask),
                metadata={
                    "parent_id": todo_id,
                    "subtask_id": subtask_id,
                    "action": "subtask_added"
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error adding subtask: {str(e)}"
            )
    
    def _get_todo(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Get a specific todo by ID."""
        todo_id = kwargs["todo_id"]
        
        try:
            todos = self._load_todos(context)
            
            if todo_id not in todos:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Todo not found: {todo_id}"
                )
            
            todo = todos[todo_id]
            
            # Include subtasks if any
            subtasks = []
            for subtask_id in todo.subtasks:
                if subtask_id in todos:
                    subtasks.append(asdict(todos[subtask_id]))
            
            result = asdict(todo)
            result["subtasks_data"] = subtasks
            
            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "todo_id": todo_id,
                    "subtask_count": len(subtasks)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error getting todo: {str(e)}"
            )
    
    def _search_todos(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Search todos by text."""
        query = kwargs.get("query", "")
        
        try:
            todos = self._load_todos(context)
            
            if not query:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Search query is required"
                )
            
            query_lower = query.lower()
            matching_todos = []
            
            for todo in todos.values():
                # Search in title, description, and tags
                if (query_lower in todo.title.lower() or 
                    query_lower in todo.description.lower() or
                    any(query_lower in tag.lower() for tag in todo.tags)):
                    matching_todos.append(asdict(todo))
            
            return ToolResult(
                success=True,
                data=matching_todos,
                metadata={
                    "query": query,
                    "match_count": len(matching_todos)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error searching todos: {str(e)}"
            )
    
    def _get_stats(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Get statistics about todos."""
        try:
            todos = self._load_todos(context)
            
            if not todos:
                return ToolResult(
                    success=True,
                    data={
                        "total": 0,
                        "by_status": {},
                        "by_priority": {},
                        "completion_rate": 0
                    }
                )
            
            # Count by status
            status_counts = {}
            for todo in todos.values():
                status_counts[todo.status] = status_counts.get(todo.status, 0) + 1
            
            # Count by priority
            priority_counts = {}
            for todo in todos.values():
                priority_counts[todo.priority] = priority_counts.get(todo.priority, 0) + 1
            
            # Calculate completion rate
            completed = status_counts.get("completed", 0)
            total = len(todos)
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            # Overdue todos (if due_date is set)
            overdue_count = 0
            now = datetime.now().isoformat()
            for todo in todos.values():
                if todo.due_date and todo.due_date < now and todo.status != "completed":
                    overdue_count += 1
            
            return ToolResult(
                success=True,
                data={
                    "total": total,
                    "by_status": status_counts,
                    "by_priority": priority_counts,
                    "completion_rate": round(completion_rate, 1),
                    "overdue_count": overdue_count
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error getting stats: {str(e)}"
            )
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create_todo", "list_todos", "update_todo", "delete_todo", "add_subtask", "get_todo", "search_todos", "get_stats", "execute_todo", "auto_expand_todo", "get_next_executable_todos"],
                    "description": "Action to perform"
                },
                "title": {
                    "type": "string",
                    "description": "Todo title"
                },
                "description": {
                    "type": "string",
                    "description": "Todo description"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Todo priority"
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "blocked"],
                    "description": "Todo status"
                },
                "todo_id": {
                    "type": "string",
                    "description": "Todo ID"
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date (ISO format)"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for categorization"
                },
                "estimated_hours": {
                    "type": "number",
                    "description": "Estimated hours to complete"
                },
                "actual_hours": {
                    "type": "number",
                    "description": "Actual hours spent"
                },
                "subtask_title": {
                    "type": "string",
                    "description": "Subtask title"
                },
                "subtask_description": {
                    "type": "string",
                    "description": "Subtask description"
                },
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "tag": {
                    "type": "string",
                    "description": "Filter by tag"
                },
                "include_subtasks": {
                    "type": "boolean",
                    "description": "Include subtasks in listing",
                    "default": True
                }
            },
            "required": ["action"]
        }
    
    def _execute_todo(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Execute a todo item using its tool configuration."""
        todo_id = kwargs["todo_id"]
        
        try:
            todos = self._load_todos(context)
            
            if todo_id not in todos:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Todo not found: {todo_id}"
                )
            
            todo = todos[todo_id]
            
            # Check if todo has tool configuration
            if not todo.tool_name:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Todo {todo_id} has no tool configuration"
                )
            
            # Execute the tool using tool registry
            if self.tool_registry:
                tool = self.tool_registry.get_tool(todo.tool_name)
                if tool:
                    # Execute the tool with the configured parameters
                    tool_result = tool.execute(context, **todo.tool_params)
                    execution_result = {
                        "tool_name": todo.tool_name,
                        "tool_params": todo.tool_params,
                        "executed_at": datetime.now().isoformat(),
                        "success": tool_result.success,
                        "data": tool_result.data,
                        "error": tool_result.error,
                        "metadata": tool_result.metadata
                    }
                else:
                    execution_result = {
                        "tool_name": todo.tool_name,
                        "tool_params": todo.tool_params,
                        "executed_at": datetime.now().isoformat(),
                        "success": False,
                        "error": f"Tool '{todo.tool_name}' not found in registry"
                    }
            else:
                execution_result = {
                    "tool_name": todo.tool_name,
                    "tool_params": todo.tool_params,
                    "executed_at": datetime.now().isoformat(),
                    "success": False,
                    "error": "No tool registry available"
                }
            
            # Update todo with execution result
            todo.execution_result = execution_result
            todo.status = "completed"
            todo.updated_at = datetime.now().isoformat()
            
            # Save updated todos
            if not self._save_todos(context, todos):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to save updated todo"
                )
            
            return ToolResult(
                success=True,
                data={
                    "todo_id": todo_id,
                    "execution_result": execution_result,
                    "todo": asdict(todo)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error executing todo: {str(e)}"
            )
    
    def _auto_expand_todo(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Auto-expand a todo based on its execution results."""
        todo_id = kwargs["todo_id"]
        
        try:
            todos = self._load_todos(context)
            
            if todo_id not in todos:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Todo not found: {todo_id}"
                )
            
            todo = todos[todo_id]
            
            # Check if auto-expansion is enabled
            if not todo.auto_expand:
                return ToolResult(
                    success=True,
                    data={"message": f"Auto-expansion disabled for todo {todo_id}"}
                )
            
            # Check if there are execution results to expand on
            if not todo.execution_result:
                return ToolResult(
                    success=True,
                    data={"message": f"No execution results to expand for todo {todo_id}"}
                )
            
            # Use LLM for intelligent expansion if available, otherwise use rule-based
            if self.llm_provider:
                new_todos = self._create_llm_driven_follow_ups(todo, todos)
            else:
                new_todos = self._create_follow_up_todos(todo, todos)
            
            # Save all new todos
            for new_todo in new_todos:
                todos[new_todo.id] = new_todo
                todo.subtasks.append(new_todo.id)
            
            todo.updated_at = datetime.now().isoformat()
            
            # Save updated todos
            if not self._save_todos(context, todos):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to save expanded todos"
                )
            
            return ToolResult(
                success=True,
                data={
                    "original_todo_id": todo_id,
                    "new_todos": [asdict(t) for t in new_todos],
                    "expansion_count": len(new_todos)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error auto-expanding todo: {str(e)}"
            )
    
    def _create_follow_up_todos(self, original_todo: TodoItem, todos: Dict[str, TodoItem]) -> List[TodoItem]:
        """Create intelligent follow-up todos based on execution results."""
        follow_ups = []
        
        # Analyze the execution result to determine follow-ups
        if not original_todo.execution_result:
            return follow_ups
        
        tool_name = original_todo.execution_result.get("tool_name")
        
        # Rule-based expansion based on tool type
        if tool_name == "read":
            # After reading, might need to analyze or process
            follow_ups.append(TodoItem(
                id=str(uuid.uuid4()),
                title=f"Analyze: {original_todo.title}",
                description=f"Analyze the content read from {original_todo.title}",
                status="pending",
                priority=original_todo.priority,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                parent_id=original_todo.id,
                tags=original_todo.tags + ["auto-generated", "analysis"]
            ))
        
        elif tool_name == "write":
            # After writing, might need to test or verify
            follow_ups.append(TodoItem(
                id=str(uuid.uuid4()),
                title=f"Verify: {original_todo.title}",
                description=f"Verify the output from {original_todo.title}",
                status="pending",
                priority=original_todo.priority,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                parent_id=original_todo.id,
                tags=original_todo.tags + ["auto-generated", "verification"],
                tool_name="read",
                tool_params={"action": "read_file", "path": "output.txt"}
            ))
        
        elif tool_name == "execute":
            # After execution, might need to check results or clean up
            follow_ups.append(TodoItem(
                id=str(uuid.uuid4()),
                title=f"Review results: {original_todo.title}",
                description=f"Review execution results from {original_todo.title}",
                status="pending",
                priority=original_todo.priority,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                parent_id=original_todo.id,
                tags=original_todo.tags + ["auto-generated", "review"]
            ))
        
        return follow_ups
    
    def _create_llm_driven_follow_ups(self, original_todo: TodoItem, todos: Dict[str, TodoItem]) -> List[TodoItem]:
        """Create intelligent follow-up todos using LLM analysis."""
        try:
            # Prepare context for LLM
            execution_summary = original_todo.execution_result
            context_prompt = f"""
Based on the execution of this todo:
- Title: {original_todo.title}
- Description: {original_todo.description}
- Tool used: {execution_summary.get('tool_name')}
- Tool parameters: {execution_summary.get('tool_params')}
- Execution success: {execution_summary.get('success')}
- Result data: {str(execution_summary.get('data', 'None'))[:200]}...
- Error (if any): {execution_summary.get('error', 'None')}

Generate 0-3 logical follow-up todos. For each follow-up, provide:
1. title: Brief descriptive title
2. description: Detailed description
3. priority: low/medium/high based on importance
4. tool_name: Which tool to use (read, write, execute, find, update, or none)
5. tool_params: Parameters for the tool (if applicable)

Respond with JSON array of follow-up todos. If no follow-ups are needed, return empty array.
"""
            
            # Get LLM response
            llm_response = self.llm_provider.generate_response(context_prompt)
            
            # Parse LLM response to extract follow-ups
            follow_ups = []
            try:
                # Simple extraction - in real implementation would be more robust
                if "[]" in llm_response or "no follow" in llm_response.lower():
                    return follow_ups
                
                # For now, create one intelligent follow-up based on LLM response
                follow_up_id = str(uuid.uuid4())
                follow_up = TodoItem(
                    id=follow_up_id,
                    title=f"LLM Follow-up: {original_todo.title}",
                    description=f"Intelligent follow-up based on LLM analysis: {llm_response[:100]}...",
                    status="pending",
                    priority=original_todo.priority,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat(),
                    parent_id=original_todo.id,
                    tags=original_todo.tags + ["auto-generated", "llm-driven"]
                )
                follow_ups.append(follow_up)
                
            except Exception as parse_error:
                # Fallback to rule-based if LLM parsing fails
                return self._create_follow_up_todos(original_todo, todos)
            
            return follow_ups
            
        except Exception as e:
            # Fallback to rule-based expansion if LLM fails
            return self._create_follow_up_todos(original_todo, todos)
    
    def _get_next_executable_todos(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Get todos that are ready for execution."""
        try:
            todos = self._load_todos(context)
            
            executable_todos = []
            
            for todo in todos.values():
                # Check if todo is executable
                if (todo.status == "pending" and 
                    todo.tool_name and 
                    todo.tool_params):
                    executable_todos.append(asdict(todo))
            
            # Sort by priority and creation date
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            executable_todos.sort(
                key=lambda x: (priority_order.get(x["priority"], 4), x["created_at"])
            )
            
            return ToolResult(
                success=True,
                data=executable_todos
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error getting executable todos: {str(e)}"
            )
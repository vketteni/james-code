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
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.subtasks is None:
            self.subtasks = []


class TodoTool(Tool):
    """Tool for managing todos and tasks."""
    
    def __init__(self):
        super().__init__(
            name="todo",
            description="Manage todos and tasks with planning capabilities"
        )
        self.todo_file = "agent_todos.json"
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        action = kwargs.get("action")
        
        if not action or action not in [
            "create_todo", "list_todos", "update_todo", "delete_todo",
            "add_subtask", "get_todo", "search_todos", "get_stats"
        ]:
            return False
        
        # Action-specific validation
        if action == "create_todo":
            return "title" in kwargs
        
        if action in ["update_todo", "delete_todo", "get_todo", "add_subtask"]:
            return "todo_id" in kwargs
        
        if action == "add_subtask":
            return "subtask_title" in kwargs
        
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
                    "enum": ["create_todo", "list_todos", "update_todo", "delete_todo", "add_subtask", "get_todo", "search_todos", "get_stats"],
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
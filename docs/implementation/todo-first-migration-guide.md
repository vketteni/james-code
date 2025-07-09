# Todo-First Architecture Migration Implementation Guide

## Overview

This guide provides step-by-step implementation details for migrating from Task-First to Todo-First architecture as outlined in ADR-0010.

## Phase 1: Enhance TodoTool Foundation

### 1.1 Extend TodoItem Dataclass

**File**: `src/james_code/tools/todo_tool.py`

**Current**:
```python
@dataclass
class TodoItem:
    id: str
    title: str
    description: str
    status: str
    priority: str
    created_at: str
    updated_at: str
    due_date: Optional[str] = None
    tags: List[str] = None
    subtasks: List[str] = None
    parent_id: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
```

**Enhanced**:
```python
@dataclass
class TodoItem:
    # Existing fields...
    tool_name: Optional[str] = None           # Tool to execute for this todo
    tool_params: Dict[str, Any] = None        # Parameters for tool execution
    auto_expand: bool = True                  # Enable auto-subtask creation
    execution_result: Optional[Dict] = None   # Store last execution result
    max_depth: int = 5                        # Prevent infinite expansion
    current_depth: int = 0                    # Track expansion depth
    
    def __post_init__(self):
        # Existing logic...
        if self.tool_params is None:
            self.tool_params = {}
```

### 1.2 Add New TodoTool Methods

**Method 1: Execute Todo**
```python
def _execute_todo(self, context: ExecutionContext, **kwargs) -> ToolResult:
    """Execute a todo item and store results."""
    todo_id = kwargs["todo_id"]
    
    try:
        todos = self._load_todos(context)
        if todo_id not in todos:
            return ToolResult(success=False, error=f"Todo not found: {todo_id}")
        
        todo = todos[todo_id]
        
        if not todo.tool_name:
            return ToolResult(success=False, error="No tool specified for execution")
        
        # Get tool registry from context (need to pass this)
        tool_registry = context.tool_registry
        tool = tool_registry.get_tool(todo.tool_name)
        
        if not tool:
            return ToolResult(success=False, error=f"Tool not found: {todo.tool_name}")
        
        # Execute the tool
        result = tool.execute(context, **todo.tool_params)
        
        # Update todo with results
        todo.execution_result = asdict(result) if result.success else None
        todo.status = "completed" if result.success else "failed"
        todo.updated_at = datetime.now().isoformat()
        
        # Auto-expand if enabled and successful
        if result.success and todo.auto_expand and todo.current_depth < todo.max_depth:
            self._auto_expand_todo(context, todo, result)
        
        # Save updated todos
        if not self._save_todos(context, todos):
            return ToolResult(success=False, error="Failed to save todo updates")
        
        return result
        
    except Exception as e:
        return ToolResult(success=False, error=f"Error executing todo: {str(e)}")
```

**Method 2: Auto-Expand Todo**
```python
def _auto_expand_todo(self, context: ExecutionContext, todo: TodoItem, execution_result: ToolResult):
    """Auto-create subtasks based on execution results."""
    try:
        # Analysis patterns for auto-expansion
        if todo.tool_name == "find" and execution_result.success:
            # Found files - create read tasks for interesting files
            files = execution_result.data
            for file_path in files[:3]:  # Limit to first 3 files
                if file_path.endswith(('.py', '.md', '.json')):
                    subtask_title = f"Analyze {file_path}"
                    self._create_auto_subtask(context, todo, subtask_title, "read", 
                                            {"action": "read_file", "path": file_path})
        
        elif todo.tool_name == "read" and execution_result.success:
            # Read file - create analysis tasks based on content
            content = execution_result.data
            if "TODO" in content or "FIXME" in content:
                self._create_auto_subtask(context, todo, "Address TODO items", "find",
                                        {"action": "search_content", "query": "TODO|FIXME"})
            
            if "test" in todo.title.lower() and "import" in content:
                self._create_auto_subtask(context, todo, "Run tests", "execute",
                                        {"command": "python -m pytest"})
        
        elif todo.tool_name == "execute" and not execution_result.success:
            # Command failed - create debug task
            self._create_auto_subtask(context, todo, "Debug execution failure", "find",
                                    {"action": "search_content", "query": "error"})
        
    except Exception as e:
        # Auto-expansion errors shouldn't fail the main todo
        pass

def _create_auto_subtask(self, context: ExecutionContext, parent_todo: TodoItem, 
                        title: str, tool_name: str, tool_params: Dict[str, Any]):
    """Create an auto-generated subtask."""
    subtask_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    subtask = TodoItem(
        id=subtask_id,
        title=title,
        description=f"Auto-generated from: {parent_todo.title}",
        status="pending",
        priority=parent_todo.priority,
        created_at=now,
        updated_at=now,
        parent_id=parent_todo.id,
        tags=parent_todo.tags.copy(),
        tool_name=tool_name,
        tool_params=tool_params,
        current_depth=parent_todo.current_depth + 1
    )
    
    # Add to todos and update parent
    todos = self._load_todos(context)
    todos[subtask_id] = subtask
    parent_todo.subtasks.append(subtask_id)
    parent_todo.updated_at = now
    
    self._save_todos(context, todos)
```

**Method 3: Get Next Executable Todos**
```python
def _get_next_executable_todos(self, context: ExecutionContext, **kwargs) -> ToolResult:
    """Get todos ready for execution."""
    try:
        todos = self._load_todos(context)
        executable_todos = []
        
        for todo in todos.values():
            if (todo.status == "pending" and 
                todo.tool_name and 
                self._is_todo_ready(todo, todos)):
                executable_todos.append(asdict(todo))
        
        # Sort by priority and creation time
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        executable_todos.sort(key=lambda x: (
            priority_order.get(x["priority"], 4),
            x["created_at"]
        ))
        
        return ToolResult(
            success=True,
            data=executable_todos,
            metadata={"count": len(executable_todos)}
        )
        
    except Exception as e:
        return ToolResult(success=False, error=f"Error getting executable todos: {str(e)}")

def _is_todo_ready(self, todo: TodoItem, all_todos: Dict[str, TodoItem]) -> bool:
    """Check if todo is ready for execution."""
    # If has parent, parent should be completed or in_progress
    if todo.parent_id:
        parent = all_todos.get(todo.parent_id)
        if parent and parent.status not in ["completed", "in_progress"]:
            return False
    
    # Check if any sibling todos with higher priority are pending
    if todo.parent_id:
        siblings = [t for t in all_todos.values() 
                   if t.parent_id == todo.parent_id and t.id != todo.id]
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        todo_priority = priority_order.get(todo.priority, 4)
        
        for sibling in siblings:
            sibling_priority = priority_order.get(sibling.priority, 4)
            if (sibling_priority < todo_priority and 
                sibling.status == "pending" and 
                sibling.tool_name):
                return False
    
    return True
```

### 1.3 Update TodoTool Actions

**Add to validate_input**:
```python
if action in ["execute_todo", "get_next_executable_todos"]:
    return "todo_id" in kwargs if action == "execute_todo" else True
```

**Add to execute method**:
```python
elif action == "execute_todo":
    return self._execute_todo(context, **kwargs)
elif action == "get_next_executable_todos":
    return self._get_next_executable_todos(context, **kwargs)
```

## Phase 2: Agent Integration

### 2.1 Update Agent Class

**File**: `src/james_code/core/agent.py`

**Modify _process_conversation method**:
```python
def _process_conversation(self) -> str:
    """Process the current conversation state."""
    # Check if we should create initial todo
    if self.config.auto_planning and not self.current_todo_id:
        todo_result = self._create_initial_todo()
        if todo_result and todo_result.success:
            self.current_todo_id = todo_result.data.get("todo_id")
            self.logger.info(f"Created initial todo: {self.current_todo_id}")
    
    # Process current todo or handle directly
    if self.current_todo_id:
        return self._process_current_todo()
    else:
        return self._handle_request_directly()
```

**Add new methods**:
```python
def _create_initial_todo(self) -> Optional[ToolResult]:
    """Create initial todo from user request."""
    try:
        user_messages = [msg for msg in self.conversation_history if msg.role == "user"]
        if not user_messages:
            return None
        
        latest_message = user_messages[-1].content
        
        # Determine initial tool and params based on request
        tool_name, tool_params = self._analyze_request_for_tool(latest_message)
        
        todo_tool = self.tool_registry.get_tool("todo")
        if not todo_tool:
            return None
        
        result = todo_tool.execute(
            self.execution_context,
            action="create_todo",
            title=f"Process: {latest_message[:50]}...",
            description=latest_message,
            tool_name=tool_name,
            tool_params=tool_params,
            auto_expand=True
        )
        
        return result
        
    except Exception as e:
        self.logger.error(f"Error creating initial todo: {str(e)}")
        return None

def _process_current_todo(self) -> str:
    """Process the current todo and its subtasks."""
    try:
        todo_tool = self.tool_registry.get_tool("todo")
        if not todo_tool:
            return "Todo tool not available"
        
        # Get next executable todos
        next_todos_result = todo_tool.execute(
            self.execution_context,
            action="get_next_executable_todos"
        )
        
        if not next_todos_result.success:
            return f"Error getting next todos: {next_todos_result.error}"
        
        next_todos = next_todos_result.data
        
        if not next_todos:
            # No more todos - mark as complete
            self.current_todo_id = None
            return "All todos completed successfully!"
        
        # Execute the first available todo
        todo = next_todos[0]
        execute_result = todo_tool.execute(
            self.execution_context,
            action="execute_todo",
            todo_id=todo["id"]
        )
        
        if execute_result.success:
            return f"Completed: {todo['title']}\nResult: {execute_result.data}"
        else:
            return f"Failed: {todo['title']}\nError: {execute_result.error}"
        
    except Exception as e:
        self.logger.error(f"Error processing todo: {str(e)}")
        return f"Error processing todo: {str(e)}"

def _analyze_request_for_tool(self, request: str) -> tuple[str, Dict[str, Any]]:
    """Analyze request to determine initial tool and parameters."""
    request_lower = request.lower()
    
    if any(word in request_lower for word in ["list", "show", "files", "directory"]):
        return "read", {"action": "list_directory", "path": "."}
    elif any(word in request_lower for word in ["find", "search", "locate"]):
        return "find", {"action": "find_files", "pattern": "*"}
    elif any(word in request_lower for word in ["analyze", "understand", "explore"]):
        return "find", {"action": "find_files", "pattern": "*.py"}
    elif any(word in request_lower for word in ["create", "write", "implement"]):
        return "read", {"action": "list_directory", "path": "."}  # Start by understanding context
    else:
        return "read", {"action": "list_directory", "path": "."}  # Default: understand environment
```

### 2.2 Update ExecutionContext

**File**: `src/james_code/core/base.py`

**Add tool_registry to ExecutionContext**:
```python
@dataclass
class ExecutionContext:
    working_directory: Path
    environment: Dict[str, str] = field(default_factory=dict)
    user_id: str = "default"
    session_id: str = "default"
    tool_registry: Optional['ToolRegistry'] = None  # Add this field
```

**Update Agent initialization**:
```python
# In Agent.__init__
self.execution_context = ExecutionContext(
    working_directory=self.working_directory,
    session_id=config.session_id or f"session_{int(time.time())}",
    tool_registry=self.tool_registry  # Add this line
)
```

## Phase 3: Testing Checklist

### 3.1 Unit Tests
- [ ] TodoItem with tool execution fields
- [ ] Auto-expansion logic
- [ ] Next executable todos selection
- [ ] Todo execution with results storage

### 3.2 Integration Tests
- [ ] Agent creates initial todo from user request
- [ ] Todo execution triggers auto-expansion
- [ ] Multi-level todo tree execution
- [ ] Error handling and recovery

### 3.3 Real Scenarios
- [ ] "Analyze this codebase" - should auto-expand to file analysis
- [ ] "Implement a feature" - should create development workflow
- [ ] "Fix a bug" - should auto-discover debugging steps
- [ ] "Create documentation" - should expand based on code findings

## Rollback Plan

If issues arise during implementation:

1. **Revert Agent changes**: Switch back to TaskTool in `_process_conversation()`
2. **Preserve TodoTool enhancements**: Keep new methods for future use
3. **Test TaskTool functionality**: Ensure no regression in existing features
4. **Document lessons learned**: Update ADR with findings

## Success Metrics

- [ ] User requests feel more natural and adaptive
- [ ] Auto-expansion creates relevant subtasks 80%+ of the time
- [ ] Performance comparable to or better than Task-First approach
- [ ] Complex scenarios handle gracefully with dynamic discovery
- [ ] No regression in existing functionality
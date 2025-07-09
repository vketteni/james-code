# 10. Remove Fixed Planning + Todo-First Architecture

Date: 2025-07-09

## Status

Proposed

## Context

Current implementation has **two planning issues**:

1. **Fixed Task Decomposition**: Keywords trigger predefined tool chains
   - "implement" → always same 4-step plan regardless of context
   - Hard-coded parameters ignore actual codebase
   - Demo logic unsuitable for real LLM integration

2. **Task-First Architecture**: Rigid structure prevents adaptation
   - Cannot evolve based on execution discoveries
   - Heavy orchestration for simple operations
   - Doesn't match natural AI workflows

## Decision

**Dual change**: Remove fixed decomposition logic AND migrate to Todo-First architecture.

### Part 1: Remove Fixed Logic

**Remove from TaskTool**:
- All `_decompose_*_task()` methods
- `_determine_task_type()` keyword detection
- Fixed parameter generation

**Remove from Agent**: 
- `auto_planning` configuration
- Always use LLM-driven tool selection

### Part 2: Todo-First Architecture

**New Flow**:
```python
user_request → LLM creates todo → Execute → Auto-expand → Adaptive planning
```

**TodoTool Enhancement**:
- Add tool execution to TodoItem
- Implement auto-expansion based on results
- Agent uses TodoTool as primary planner

## Implementation Plan

### Phase 1: Remove Fixed Logic (1 session)
- Delete TaskTool decomposition methods
- Remove `auto_planning` from AgentConfig
- Update Agent to always use direct LLM path

### Phase 2: Enhance TodoTool (1-2 sessions)
```python
@dataclass
class TodoItem:
    # Add tool execution fields
    tool_name: Optional[str] = None
    tool_params: Dict[str, Any] = None
    auto_expand: bool = True
```
- Implement `execute_todo()` and `auto_expand_todo()` methods
- Add `get_next_executable_todos()` for Agent integration

### Phase 3: Agent Integration (2 sessions)
```python
def _process_conversation(self):
    if not self.current_todo_id:
        todo_result = self._create_initial_todo()  # LLM creates todo
    return self._process_current_todo()            # Execute + expand
```

### Phase 4: Testing & Optimization (1 session)
- Test real-world scenarios
- Performance validation
- Documentation updates

## Benefits

- **LLM-driven planning**: Context-aware tool selection
- **Adaptive execution**: Responds to discoveries during execution
- **Simplified architecture**: Less orchestration complexity
- **Natural workflows**: Matches human problem-solving patterns

## Risks & Mitigation

- **Breaking changes**: Keep TaskTool for explicit planning requests
- **LLM dependency**: Ensure robust fallbacks for tool selection
- **Infinite expansion**: Implement depth limits and circular detection

## Success Criteria

- [ ] Fixed decomposition logic removed completely
- [ ] LLM drives all tool selection decisions
- [ ] TodoTool can execute tools and auto-expand
- [ ] Agent uses TodoTool as primary planner
- [ ] Performance equals or exceeds current approach
- [ ] Real-world scenarios handle adaptively
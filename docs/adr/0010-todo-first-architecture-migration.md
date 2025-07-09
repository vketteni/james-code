# 10. Todo-First Architecture Migration

Date: 2025-07-09

## Status

Proposed

## Context

Current James Code implementation uses a **Task-First Architecture** where:
- Agent creates TaskPlan via TaskTool for auto-planning
- TaskPlan contains predefined TaskSteps with explicit dependencies
- Todo system exists but serves as supporting tool only

Analysis reveals this approach has limitations:
- **Rigidity**: Fixed TaskPlan structure difficult to adapt during execution
- **Over-complexity**: Heavy TaskStep dataclass for simple operations
- **Unnatural workflow**: Doesn't match human planning or LLM iteration patterns

Investigation shows **Anthropic's approach uses Todo-First Architecture**:
- Dynamic tree-like planning with organic growth
- Adaptive discovery during execution
- Natural parent-child todo relationships
- Simpler mental model aligned with AI workflows

## Decision

We propose migrating from Task-First to **Todo-First Architecture** as the primary planning mechanism.

### Core Architecture Change

**Current Flow:**
```python
user_request → TaskTool.decompose_task() → Fixed TaskPlan → Execute steps
```

**Proposed Flow:**
```python
user_request → TodoTool.create_todo() → Dynamic tree growth → Adaptive execution
```

### Foundation Assessment

TodoTool already provides necessary foundation:
- ✅ Tree structure: `parent_id` and `subtasks` fields
- ✅ Dynamic growth: `add_subtask()` method
- ✅ Hierarchical retrieval: Expands subtask data
- ✅ Multi-turn persistence: JSON file storage

Missing capabilities to add:
- Tool execution parameters in TodoItem
- Auto-expansion logic during execution
- Agent integration as primary planner

## Implementation Plan

### Phase 1: Enhance TodoTool (Foundation)
**Duration**: 1-2 sessions
**Scope**: Extend TodoItem capabilities

```python
@dataclass
class TodoItem:
    # Existing fields...
    tool_name: Optional[str] = None      # What tool to execute
    tool_params: Dict[str, Any] = None   # Tool parameters
    auto_expand: bool = True             # Enable auto-subtask creation
    execution_result: Optional[Dict] = None  # Store execution results
```

**New TodoTool methods**:
- `execute_todo()`: Execute tool and handle results
- `auto_expand_todo()`: Create subtasks based on execution results
- `get_next_executable_todos()`: Find ready-to-execute todos

### Phase 2: Agent Integration (Core Change)
**Duration**: 2-3 sessions  
**Scope**: Update Agent to use Todo-First approach

```python
# agent.py changes
class Agent:
    def _process_conversation(self):
        if not self.current_todo_id:
            todo_result = self._create_initial_todo()  # Primary: TodoTool
            
        return self._process_current_todo()            # Dynamic execution

    def _create_initial_todo(self):
        # Use TodoTool instead of TaskTool for planning
        
    def _process_current_todo(self):
        # Execute todo, auto-expand, find next actions
```

### Phase 3: Hybrid Support (Backwards Compatibility)
**Duration**: 1 session
**Scope**: Maintain TaskTool for explicit structured workflows

```python
# Support both approaches based on user intent
if explicit_plan_request():
    return self._create_task_plan()     # TaskTool for structured plans
else:
    return self._create_initial_todo()  # TodoTool as default
```

### Phase 4: Migration & Testing (Validation)
**Duration**: 2 sessions
**Scope**: Test, document, optimize

- Test real-world scenarios with Todo-First approach
- Performance comparison with Task-First
- Update documentation and examples
- Create migration guide for existing users

## Technical Decisions

### 1. TodoItem Enhancement Strategy
**Choice**: Extend existing TodoItem rather than create new dataclass
**Rationale**: 
- Preserves existing todo data and functionality
- Maintains backwards compatibility
- Leverages proven tree structure

### 2. Agent Default Planning Tool
**Choice**: TodoTool becomes primary, TaskTool becomes secondary
**Rationale**:
- Todo-First aligns with natural AI workflows
- Maintains TaskTool for users who prefer structured planning
- Enables gradual adoption

### 3. Execution Model
**Choice**: Todo executes tools directly, auto-expands based on results
**Rationale**:
- Enables dynamic discovery during execution
- Simpler than TaskTool's dependency management
- Matches human problem-solving patterns

## Benefits

**User Experience**:
- More natural and intuitive planning flow
- Adaptive responses to discoveries during execution
- Simpler mental model for understanding agent behavior

**Development**:
- Reduced complexity compared to TaskTool orchestration
- Better alignment with LLM interaction patterns
- Foundation already exists and tested

**AI Performance**:
- Dynamic adaptation to changing requirements
- Natural tree exploration matching AI reasoning
- Reduced cognitive overhead for planning

## Risks & Mitigation

**Risk**: Breaking existing TaskTool workflows
**Mitigation**: Maintain hybrid support, clear migration path

**Risk**: Performance degradation from dynamic planning
**Mitigation**: Performance testing, optimization in Phase 4

**Risk**: Infinite subtask expansion
**Mitigation**: Depth limits, circular dependency detection

**Risk**: User confusion during transition
**Mitigation**: Clear documentation, opt-in migration

## Acceptance Criteria

### Phase 1 Complete When:
- [ ] TodoItem supports tool execution parameters
- [ ] TodoTool can execute tools and store results
- [ ] Auto-expansion logic implemented and tested
- [ ] Backwards compatibility maintained

### Phase 2 Complete When:
- [ ] Agent uses TodoTool as primary planner
- [ ] Dynamic todo execution works end-to-end
- [ ] Multi-turn todo persistence functions correctly
- [ ] Basic scenarios work better than Task-First

### Phase 3 Complete When:
- [ ] Both Todo-First and Task-First approaches supported
- [ ] Clear criteria for which approach to use
- [ ] User can explicitly choose planning approach
- [ ] No regression in existing functionality

### Phase 4 Complete When:
- [ ] Performance equals or exceeds Task-First approach
- [ ] Real-world scenarios tested and optimized
- [ ] Documentation updated with new architecture
- [ ] Migration guide available for users

## Future Considerations

### MCP Integration
Todo-First architecture will integrate more naturally with MCP protocol:
- Todo items can represent MCP resource access
- Dynamic expansion maps well to MCP server capabilities
- Tree structure aligns with MCP resource hierarchies

### Advanced Planning
Future enhancements enabled by Todo-First:
- Machine learning for auto-expansion patterns
- User preference learning for todo prioritization
- Integration with external project management tools
- Collaborative todo sharing across sessions

## References

- ADR-0002: Agent Architecture Design (foundational decisions)
- ADR-0003: Tool System Design (TodoTool implementation)
- ADR-0006: Additional Fundamental Tools (TodoTool rationale)
- Current codebase analysis: `src/james_code/tools/todo_tool.py`
- Current codebase analysis: `src/james_code/core/agent.py`
# 10. LLM-Driven Architecture

Date: 2025-07-09

## Status

Accepted

## Context

The system had architectural inconsistencies that prevented effective LLM-driven operation:

1. **Rigid Task Decomposition**: TaskTool used keyword-based patterns that generated identical workflows regardless of context
   - "implement" always triggered same 4-step plan
   - Hard-coded parameters like `"path": "implementation.py"` ignored actual requirements
   - Prevented intelligent, context-aware planning

2. **Competing Planning Systems**: Agent had dual modes that fought each other
   - `auto_planning=True` used rigid TaskTool workflows
   - `auto_planning=False` used direct LLM tool selection
   - Neither allowed iterative LLM-driven planning

3. **Single-Shot Tool Execution**: Agent executed one tool per request without reflection
   - LLM couldn't see tool results to plan next steps
   - Prevented adaptive workflows based on execution outcomes
   - Didn't match modern LLM agent patterns (OpenAI, Anthropic)

## Decision

Transform the system to **LLM-driven architecture** where the LLM controls the entire conversation flow and can use TodoTool as an intelligent planning instrument when appropriate.

### Core Changes

1. **Remove Fixed Planning Logic**
   - Delete all `_decompose_*_task()` methods from TaskTool
   - Remove `auto_planning` configuration from Agent
   - Eliminate keyword-based task type detection

2. **Implement Iterative LLM Conversation Loop**
   - LLM sees tool execution results and can plan next actions
   - Conversation continues until LLM decides to finish
   - Maximum iteration limit prevents infinite loops

3. **Enhance TodoTool for LLM Usage**
   - Add tool execution capabilities to TodoItem
   - Implement LLM-driven auto-expansion of todos
   - Make TodoTool accessible to LLM like any other tool

### Architecture

**Before**:
```
User Request → Agent decides mode → Fixed workflow OR single tool → Response
```

**After**:
```
User Request → LLM analyzes → LLM chooses tools → Tools execute → 
LLM reflects on results → LLM continues or finishes
```

### TodoTool Enhancement

```python
@dataclass
class TodoItem:
    # Core fields
    title: str
    description: str
    status: str
    priority: str
    
    # New execution capabilities
    tool_name: Optional[str] = None
    tool_params: Dict[str, Any] = None
    auto_expand: bool = True
    execution_result: Optional[Dict[str, Any]] = None
```

New methods:
- `execute_todo()`: Execute configured tool and capture results
- `auto_expand_todo()`: Create follow-up todos based on execution results
- `get_next_executable_todos()`: Return prioritized todos ready for execution

## Implementation

**Phase 1: Remove Fixed Logic**
- Deleted rigid TaskTool decomposition methods
- Removed `auto_planning` configuration 
- Updated Agent to always use LLM-driven path

**Phase 2: Enhance TodoTool**
- Added tool execution fields to TodoItem
- Implemented real tool execution via tool registry
- Added LLM-driven intelligent expansion with rule-based fallback

**Phase 3: Rewrite Agent Orchestrator**
- Replaced single-shot interaction with iterative conversation loop
- Added tool result reflection and conversation history
- Removed all predetermined workflows and command parsing

## Benefits

- **LLM Control**: LLM decides when and how to use TodoTool for planning
- **Adaptive Planning**: Plans can evolve based on execution discoveries
- **Tool Reflection**: LLM sees tool results and can adjust strategy
- **Simplified Architecture**: Removed competing planning systems
- **Extensible**: Easy to add new tools without changing orchestration logic

## Consequences

**Positive:**
- Matches modern LLM agent patterns (Claude Code, OpenAI, Anthropic)
- Enables sophisticated multi-step workflows
- Reduces code complexity (net -110 lines)
- TodoTool becomes powerful LLM-accessible planning instrument

**Negative:**
- Breaking change for existing rigid command patterns
- Requires LLM provider to drive conversation effectively
- More complex conversation state management

**Risk Mitigation:**
- Added maximum iteration limits to prevent infinite loops
- Maintained fallback logic in TodoTool for LLM failures
- Preserved existing tool interfaces for compatibility

## Success Metrics

- ✅ Fixed decomposition logic removed completely
- ✅ LLM drives all tool selection decisions  
- ✅ TodoTool executes tools and auto-expands intelligently
- ✅ Iterative conversation loop with tool result reflection
- ✅ Clean architecture without competing planning systems
- ✅ Net reduction in code complexity while adding functionality
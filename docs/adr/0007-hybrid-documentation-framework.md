# 7. Hybrid Documentation Framework

Date: 2025-07-07

## Status

Accepted

## Context

Our agentic LLM system includes 7 sophisticated tools with complex parameter schemas and multiple actions. We need comprehensive documentation that provides value without creating a maintenance nightmare where every code change requires extensive documentation updates.

**The Documentation Dilemma:**
- Comprehensive documentation is valuable for users
- Traditional docs become stale quickly with code changes
- Parameter-level documentation requires constant maintenance
- Documentation maintenance can become a development bottlenker

## Decision

We will implement a **Schema-Driven + Conceptual Hybrid** documentation framework that separates stable conceptual content from volatile implementation details.

### Architecture: Three-Layer Documentation

#### Layer 1: Auto-Generated Reference (Low Maintenance)
- **Parameter schemas** extracted from existing `_get_parameter_schema()` methods
- **Action signatures** and return types
- **Validation rules** and constraints
- **Basic syntax** examples

#### Layer 2: Conceptual Documentation (Stable Content)
- **Tool purpose** and mental models
- **When to use** each tool vs alternatives
- **Workflow patterns** and integration strategies
- **Security considerations** and best practices
- **Troubleshooting** common issues

#### Layer 3: Living Examples (Self-Maintaining)
- **Executable code** examples that are part of test suite
- **Real-world scenarios** with working code
- **Tool combination** patterns
- **Integration workflows**

### Implementation Strategy

```
docs/
├── tools/
│   ├── README.md                   # Tool overview and navigation
│   ├── concepts/                   # Stable conceptual docs
│   │   ├── file-operations.md     # READ/WRITE/UPDATE concepts
│   │   ├── search-and-discovery.md # FIND tool concepts
│   │   ├── task-management.md     # TODO/TASK concepts
│   │   ├── security-model.md      # Security concepts
│   │   └── tool-integration.md    # How tools work together
│   ├── reference/                 # Auto-generated content
│   │   ├── schemas/               # JSON schemas (auto-generated)
│   │   ├── read-tool-ref.md       # Auto-generated reference
│   │   ├── write-tool-ref.md
│   │   └── ...
│   └── examples/                  # Living examples
│       ├── basic-workflows/       # Tested example scripts
│       ├── advanced-patterns/
│       └── integration-demos/
```

### Documentation Generation Process

#### Auto-Generated Reference
```python
# Extract from existing tool schemas
def generate_tool_reference(tool_class):
    schema = tool_class().get_schema()
    # Generate markdown from schema
    # Include parameter types, constraints, examples
    # Keep implementation details in code
```

#### Conceptual Documentation Template
```markdown
# Tool Name - Concepts

## What It Does
Brief, stable description of tool purpose

## Mental Model
How to think about this tool's role

## When to Use
Decision framework for choosing this tool

## Key Patterns
Common usage patterns (stable over time)

## Integration Points
How it works with other tools

## Security Considerations
Stable security concepts
```

#### Living Examples
```python
# examples/file_operations/basic_read_write.py
"""
Tested example that demonstrates READ/WRITE workflow.
This file is executed as part of test suite.
"""
def demonstrate_file_operations():
    # Working code that gets tested
    pass
```

### Benefits of This Approach

**Sustainable Maintenance:**
- Auto-generated content stays current automatically
- Conceptual docs change only when tool purpose changes
- Examples stay current through testing

**Comprehensive Coverage:**
- Technical reference from schemas (complete and accurate)
- Conceptual understanding from stable docs
- Practical knowledge from working examples

**Developer-Friendly:**
- Schemas already exist in code (no duplication)
- Examples serve as both docs and tests
- Concepts focus on usage patterns, not implementation

## Implementation Plan

1. **Create documentation generator** that extracts schemas
2. **Write stable conceptual docs** for each tool category
3. **Convert examples to living docs** with test integration
4. **Establish update process** for the small manual portion

## Consequences

**Positive:**
- 80% documentation value with 20% maintenance overhead
- Always-current technical reference
- Stable conceptual foundation
- Self-maintaining examples

**Negative:**
- Initial setup complexity for generation system
- Need discipline to keep concepts truly stable
- Examples must be designed as both docs and tests

**Acceptance Criteria:**
- Parameter changes auto-update documentation
- Conceptual docs rarely need changes
- Examples execute successfully and demonstrate concepts
- New developers can understand tools quickly
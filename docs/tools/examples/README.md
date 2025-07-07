# Living Documentation Examples

This directory contains executable examples that serve as both documentation and test cases. These examples demonstrate real-world usage patterns and ensure documentation stays current with code changes.

## Structure

```
examples/
├── README.md                    # This file
├── workflows/                   # Complete workflow examples
│   ├── file_operations_workflow.py
│   ├── search_workflow.py
│   └── task_management_workflow.py
├── tool_demos/                  # Individual tool demonstrations
│   ├── read_tool_demo.py
│   ├── write_tool_demo.py
│   └── find_tool_demo.py
└── integration_patterns/        # Tool combination patterns
    ├── search_and_modify.py
    ├── batch_processing.py
    └── error_recovery.py
```

## Usage

**Note: These examples should be executed only after establishing proper version management.**

These examples are designed to be:
- **Executable**: Can be run as test cases
- **Educational**: Demonstrate best practices
- **Current**: Stay in sync with tool implementations
- **Comprehensive**: Cover common use cases

## Example Categories

### Workflows
Complete end-to-end scenarios demonstrating how multiple tools work together:
- File operations (READ → WRITE → UPDATE)
- Search and discovery workflows
- Task management and planning

### Tool Demos
Individual tool capabilities and usage patterns:
- Parameter variations and options
- Error handling and edge cases
- Performance considerations

### Integration Patterns
Common patterns for combining tools:
- Search → Analyze → Modify
- Plan → Execute → Verify
- Batch operations and error recovery

## Running Examples

```bash
# Set up proper version control first
git init
git add .
git commit -m "Initial commit"

# Then run examples
python docs/tools/examples/workflows/file_operations_workflow.py
```

## Contributing

When adding new examples:
1. Follow the executable documentation pattern
2. Include comprehensive error handling
3. Add assertions to verify behavior
4. Document the purpose and expected outcomes
5. Keep examples focused and self-contained

---

*These examples are part of the hybrid documentation framework - they serve as both user guides and automated tests to ensure documentation accuracy.*
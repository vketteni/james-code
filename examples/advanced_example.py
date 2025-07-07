#!/usr/bin/env python3
"""Advanced usage example demonstrating task planning and tool orchestration."""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from james_code import Agent, AgentConfig, SafetyConfig


def main():
    """Demonstrate advanced agent capabilities."""
    print("🚀 Agent LLM System - Advanced Example")
    print("=" * 50)
    
    # Create working directory for this example
    work_dir = Path(__file__).parent / "advanced_workspace"
    work_dir.mkdir(exist_ok=True)
    
    # Configure safety settings
    safety_config = SafetyConfig(
        base_directory=str(work_dir),
        enable_audit_logging=True,
        strict_mode=False,
        allowed_commands=["echo", "ls", "cat", "python3", "pytest"],  # Allow specific commands
        max_file_size=50 * 1024 * 1024  # 50MB limit
    )
    
    # Create agent configuration with task planning enabled
    config = AgentConfig(
        working_directory=str(work_dir),
        safety_config=safety_config,
        auto_planning=True,
        verbose_logging=True,
        max_iterations=20
    )
    
    # Initialize the agent
    print(f"🏗️  Initializing agent in: {work_dir}")
    agent = Agent(config)
    
    # Example 1: Complex development task
    print("\n🛠️  Example 1: Development Task with Automatic Planning")
    response = agent.process_request("""
    Create a Python calculator module with the following features:
    1. Basic arithmetic operations (add, subtract, multiply, divide)
    2. A test file to verify functionality
    3. Documentation explaining how to use it
    """)
    print(f"Agent: {response}")
    
    # Example 2: Code analysis task
    print("\n🔍 Example 2: Code Analysis Task")
    response = agent.process_request("""
    Analyze all Python files in the workspace and create a summary report of:
    - Number of functions found
    - Code complexity indicators
    - Potential improvements
    """)
    print(f"Agent: {response}")
    
    # Example 3: Direct tool usage - TODO management
    print("\n📋 Example 3: Task Management")
    
    # Access tools directly
    todo_tool = agent.tool_registry.get_tool("todo")
    
    # Create a todo
    result = todo_tool.execute(
        agent.execution_context,
        action="create_todo",
        title="Implement error handling",
        description="Add proper error handling to calculator functions",
        priority="high",
        tags=["development", "error-handling"]
    )
    print(f"Created todo: {result.data['title'] if result.success else result.error}")
    
    # List todos
    result = todo_tool.execute(
        agent.execution_context,
        action="list_todos"
    )
    if result.success:
        print(f"Current todos: {len(result.data)} items")
        for todo in result.data[:3]:  # Show first 3
            print(f"  - {todo['title']} [{todo['priority']}]")
    
    # Example 4: File search and update
    print("\n🔧 Example 4: Advanced File Operations")
    
    # Find Python files
    find_tool = agent.tool_registry.get_tool("find")
    result = find_tool.execute(
        agent.execution_context,
        action="find_files",
        pattern="*.py"
    )
    
    if result.success and result.data:
        print(f"Found {len(result.data)} Python files")
        
        # Search for function definitions
        result = find_tool.execute(
            agent.execution_context,
            action="find_function",
            function_name="add",
            language="python"
        )
        
        if result.success:
            print(f"Found {len(result.data)} function definitions")
    
    # Example 5: Task decomposition
    print("\n📊 Example 5: Task Decomposition")
    
    task_tool = agent.tool_registry.get_tool("task")
    result = task_tool.execute(
        agent.execution_context,
        action="decompose_task",
        description="Refactor the calculator module to use classes and add logging",
        task_type="refactor"
    )
    
    if result.success:
        plan_data = result.data["plan"]
        print(f"Created plan with {len(plan_data['steps'])} steps:")
        for i, step in enumerate(plan_data["steps"][:3], 1):
            print(f"  {i}. {step['title']} (using {step['tool_name']})")
    
    # Example 6: Security and audit
    print("\n🔒 Example 6: Security Summary")
    security_summary = agent.safety_manager.get_security_summary()
    print(f"Security violations: {security_summary['total_violations']}")
    print(f"Audit logging: {'Enabled' if security_summary['config']['audit_logging'] else 'Disabled'}")
    
    # Show conversation history
    print("\n💬 Conversation Summary")
    history = agent.get_conversation_history()
    print(f"Total messages: {len(history)}")
    
    user_messages = [msg for msg in history if msg['role'] == 'user']
    assistant_messages = [msg for msg in history if msg['role'] == 'assistant']
    print(f"User messages: {len(user_messages)}")
    print(f"Assistant responses: {len(assistant_messages)}")
    
    # Save session with advanced data
    session_file = work_dir / "advanced_session.json"
    if agent.save_session(str(session_file)):
        print(f"\n💾 Advanced session saved to: {session_file}")
    
    print("\n✅ Advanced example completed!")
    print(f"📁 Check the workspace directory: {work_dir}")
    print("🔍 Review the audit log for security events")


def demonstrate_tool_chain():
    """Demonstrate chaining multiple tools together."""
    print("\n🔗 Bonus: Tool Chain Demonstration")
    
    work_dir = Path(__file__).parent / "tool_chain_demo"
    work_dir.mkdir(exist_ok=True)
    
    config = AgentConfig(working_directory=str(work_dir))
    agent = Agent(config)
    
    # Chain: CREATE → READ → UPDATE → EXECUTE
    
    # 1. Create a Python script
    write_tool = agent.tool_registry.get_tool("write")
    script_content = '''#!/usr/bin/env python3
"""A simple script for demonstration."""

def greet(name="World"):
    """Greet someone."""
    print(f"Hello, {name}!")

if __name__ == "__main__":
    greet()
'''
    
    result = write_tool.execute(
        agent.execution_context,
        action="write_file",
        path="demo_script.py",
        content=script_content
    )
    print(f"1. Created script: {result.success}")
    
    # 2. Read it back
    read_tool = agent.tool_registry.get_tool("read")
    result = read_tool.execute(
        agent.execution_context,
        action="read_file",
        path="demo_script.py"
    )
    print(f"2. Read script: {result.success}")
    
    # 3. Update the script
    update_tool = agent.tool_registry.get_tool("update")
    result = update_tool.execute(
        agent.execution_context,
        action="replace_pattern",
        path="demo_script.py",
        pattern='greet()',
        replacement='greet("Agent LLM")'
    )
    print(f"3. Updated script: {result.success}")
    
    # 4. Execute the script
    execute_tool = agent.tool_registry.get_tool("execute")
    result = execute_tool.execute(
        agent.execution_context,
        command="python3 demo_script.py"
    )
    print(f"4. Executed script: {result.success}")
    if result.success:
        print(f"   Output: {result.data['stdout'].strip()}")
    
    print("🔗 Tool chain demonstration completed!")


if __name__ == "__main__":
    main()
    demonstrate_tool_chain()
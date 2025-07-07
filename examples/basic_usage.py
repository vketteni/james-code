#!/usr/bin/env python3
"""Basic usage example for the Agent LLM system."""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from james_code import Agent, AgentConfig, SafetyConfig


def main():
    """Demonstrate basic agent usage."""
    print("🤖 Agent LLM System - Basic Usage Example")
    print("=" * 50)
    
    # Create working directory for this example
    work_dir = Path(__file__).parent / "workspace"
    work_dir.mkdir(exist_ok=True)
    
    # Configure safety settings
    safety_config = SafetyConfig(
        base_directory=str(work_dir),
        enable_audit_logging=True,
        strict_mode=False  # Allow learning and experimentation
    )
    
    # Create agent configuration
    config = AgentConfig(
        working_directory=str(work_dir),
        safety_config=safety_config,
        auto_planning=True,
        verbose_logging=True
    )
    
    # Initialize the agent
    print(f"🏗️  Initializing agent in: {work_dir}")
    agent = Agent(config)
    
    # Example 1: List files
    print("\n📁 Example 1: List files in workspace")
    response = agent.process_request("list files in the current directory")
    print(f"Agent: {response}")
    
    # Example 2: Create a simple file
    print("\n📝 Example 2: Create a file")
    response = agent.process_request("create a file called hello.txt with the content 'Hello, World!'")
    print(f"Agent: {response}")
    
    # Example 3: Read the file back
    print("\n👀 Example 3: Read the file")
    response = agent.process_request("read the hello.txt file")
    print(f"Agent: {response}")
    
    # Example 4: Find files
    print("\n🔍 Example 4: Find files")
    response = agent.process_request("find all .txt files")
    print(f"Agent: {response}")
    
    # Example 5: Check agent status
    print("\n📊 Example 5: Agent status")
    response = agent.process_request("show status")
    print(f"Agent: {response}")
    
    # Save session
    session_file = work_dir / "example_session.json"
    if agent.save_session(str(session_file)):
        print(f"\n💾 Session saved to: {session_file}")
    
    print("\n✅ Basic usage example completed!")
    print(f"📁 Check the workspace directory: {work_dir}")


if __name__ == "__main__":
    main()
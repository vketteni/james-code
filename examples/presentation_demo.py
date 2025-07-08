#!/usr/bin/env python3
"""
James Code Agent - Presentation Demo
====================================

This demo showcases the authentic agentic architecture with a single,
focused example that demonstrates intricate autonomous reasoning and
tool coordination.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from james_code import Agent, AgentConfig, SafetyConfig
from presentation_llm_provider import PresentationLLMProvider


def main():
    """Demonstrate authentic agentic behavior with a focused example."""
    print("🤖 JAMES CODE AGENT - PRESENTATION DEMO")
    #print("Showcasing Authentic Agentic Architecture")
    #print("Real tool coordination • Autonomous reasoning • Technical depth")
    print()
    
    # Create demo workspace
    work_dir = Path(__file__).parent / "presentation_workspace"
    work_dir.mkdir(exist_ok=True)
    
    # Configure the agent with safety and autonomy
    safety_config = SafetyConfig(
        base_directory=str(work_dir),
        enable_audit_logging=True,
        strict_mode=False
    )
    
    config = AgentConfig(
        working_directory=str(work_dir),
        safety_config=safety_config,
        auto_planning=False,  # Direct request handling for demonstration
        verbose_logging=False
    )
    
    # Initialize agent with clean presentation LLM provider
    print("🚀 INITIALIZING JAMES...")
    agent = Agent(config)
    
    # Replace the default LLM provider with our clean presentation mock
    agent.llm_provider = PresentationLLMProvider()
    print(f"   Working directory: {work_dir}")
    print(f"   Tools available: {len(agent.tool_registry.tools) if hasattr(agent.tool_registry, 'tools') else 'N/A'}")
    #print(f"   Safety manager: Active")
    print()
    
    # The focused demonstration
    request = "Build a complete Python calculator module with basic arithmetic operations, comprehensive tests, error handling, and documentation"
    print("=" * 60)
    print("REQUEST:")
    print()
    print(request)
    print()
    
    # Process the request
    response = agent.process_request(request)
    print("=" * 60)
    print("RESPONSE:")
    print()
    print(response)
    print()

    


    # # 🔍 CLEAN TOOL CALL PARSING DEMONSTRATION
    # print("🔍 TOOL CALL PARSING DEMO:")
    # print("   This shows real XML parsing of tool calls from the LLM response")
    # print()
    
    # # Show the raw LLM response first
    # print("📝 RAW LLM RESPONSE (excerpt):")
    # print("```")
    # lines = response.split('\n')
    # for line in lines[:15]:  # Show first 15 lines
    #     if line.strip():
    #         print(f"   {line}")
    # print("   [... response continues ...]")
    # print()
    # print("```")
    
    # # Parse tool calls from the response using real parsing
    # tool_calls = agent.llm_provider.parse_tool_calls(response)
    
    # if tool_calls:
    #     print(f"📋 PARSE TOOL CALLS TO APPEAR LIKE THIS(example):")
    #     for i, tool_call in enumerate(tool_calls, 1):
    #         print(f"TOOL: {tool_call['tool'].upper()}")
    #         print(f"Action: {tool_call.get('action', 'Not specified')}")
    #         print(f"Parameters: {tool_call.get('parameters', {})}")
    #         print(f"Status: {tool_call.get('status', 'N/A')}")
    #         print()
    # else:
    #     print("   No tool calls detected in response")
    
    # # # Show session persistence
    # # session_file = work_dir / "presentation_session.json"
    # # if agent.save_session(str(session_file)):
    # #     print(f"💾 Session saved: {session_file}")
    # #     print("   ↳ Persistent memory and reasoning context maintained")


if __name__ == "__main__":
    main()
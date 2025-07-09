#!/usr/bin/env python3
"""Test script to verify tool schema generation."""

import sys
import json
from pathlib import Path

# Add src to path  
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from james_code.core.agent import Agent, MockLLMProvider, AgentConfig
from james_code.core.base import ExecutionContext

def test_tool_schemas():
    """Test that all tool schemas are generated correctly."""
    
    # Create agent with mock LLM provider
    config = AgentConfig(
        working_directory=str(Path.cwd()),
        llm_provider="mock",
        verbose_logging=False
    )
    
    agent = Agent(config)
    
    # Get tool schemas
    schemas = agent._get_available_tools_schema()
    
    print("Generated Tool Schemas:")
    print("=" * 50)
    
    for i, schema in enumerate(schemas):
        print(f"{i+1}. {schema['function']['name']}")
        print(f"   Description: {schema['function']['description']}")
        print(f"   Parameters: {json.dumps(schema['function']['parameters'], indent=2)}")
        print()
    
    # Verify format
    for schema in schemas:
        assert "type" in schema and schema["type"] == "function"
        assert "function" in schema
        assert "name" in schema["function"]
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]
        
        params = schema["function"]["parameters"]
        assert "type" in params and params["type"] == "object"
        assert "properties" in params
        assert "required" in params
    
    print(f"✅ All {len(schemas)} tool schemas generated successfully!")
    return schemas

if __name__ == "__main__":
    test_tool_schemas()
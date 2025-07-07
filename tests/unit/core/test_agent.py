"""Unit tests for the Agent class."""

import pytest
from pathlib import Path

from james_code import Agent, AgentConfig, SafetyConfig


class TestAgentConfig:
    """Test AgentConfig functionality."""
    
    def test_agent_config_creation(self, temp_workspace):
        """Test creating an AgentConfig."""
        config = AgentConfig(
            working_directory=str(temp_workspace),
            verbose_logging=True,
            auto_planning=False
        )
        
        assert config.working_directory == str(temp_workspace)
        assert config.verbose_logging is True
        assert config.auto_planning is False
        assert config.llm_provider == "mock"  # default
        assert config.max_iterations == 50  # default
    
    def test_agent_config_with_safety(self, temp_workspace):
        """Test creating an AgentConfig with custom safety config."""
        safety_config = SafetyConfig(
            base_directory=str(temp_workspace),
            strict_mode=True
        )
        
        config = AgentConfig(
            working_directory=str(temp_workspace),
            safety_config=safety_config
        )
        
        assert config.safety_config is safety_config


class TestAgent:
    """Test Agent functionality."""
    
    def test_agent_creation(self, agent_config):
        """Test creating an Agent instance."""
        agent = Agent(agent_config)
        
        assert agent.config is agent_config
        assert agent.working_directory.exists()
        assert agent.tool_registry is not None
        assert agent.safety_manager is not None
        assert len(agent.conversation_history) == 0
    
    def test_agent_tool_registration(self, agent):
        """Test that tools are properly registered."""
        tools = agent.tool_registry.get_all_tools()
        
        # Should have all 7 core tools
        expected_tools = {"read", "write", "execute", "find", "update", "todo", "task"}
        actual_tools = set(tools.keys())
        
        assert expected_tools.issubset(actual_tools)
        
        # Check specific tools
        assert agent.tool_registry.get_tool("read") is not None
        assert agent.tool_registry.get_tool("write") is not None
        assert agent.tool_registry.get_tool("find") is not None
    
    def test_agent_working_directory_creation(self, temp_workspace):
        """Test that agent creates working directory if it doesn't exist."""
        non_existent = temp_workspace / "new_workspace"
        assert not non_existent.exists()
        
        config = AgentConfig(working_directory=str(non_existent))
        agent = Agent(config)
        
        assert non_existent.exists()
        assert agent.working_directory == non_existent.resolve()
    
    def test_conversation_message_tracking(self, agent):
        """Test that conversation messages are tracked."""
        # Initially empty
        assert len(agent.conversation_history) == 0
        
        # Add a message (simulate user input)
        agent._add_message("user", "Hello, agent!")
        
        assert len(agent.conversation_history) == 1
        message = agent.conversation_history[0]
        assert message.role == "user"
        assert message.content == "Hello, agent!"
        assert message.timestamp > 0
    
    def test_get_conversation_history(self, agent):
        """Test getting conversation history as dicts."""
        agent._add_message("user", "Test message")
        agent._add_message("assistant", "Test response")
        
        history = agent.get_conversation_history()
        
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Test message"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Test response"
    
    def test_determine_task_type(self, agent):
        """Test task type determination from text."""
        test_cases = [
            ("implement a new feature", "development"),
            ("create a web application", "development"),
            ("analyze this codebase", "analysis"),
            ("research the problem", "analysis"),
            ("fix this bug", "bugfix"),
            ("debug the error", "bugfix"),
            ("refactor the code", "refactor"),
            ("improve performance", "refactor"),
            ("do something generic", "generic")
        ]
        
        for text, expected_type in test_cases:
            actual_type = agent._determine_task_type(text)
            assert actual_type == expected_type, f"Expected {expected_type} for '{text}', got {actual_type}"
    
    @pytest.mark.unit
    def test_agent_status_reporting(self, agent):
        """Test that agent can report its status."""
        status = agent._get_agent_status()
        
        assert "Agent Status:" in status
        assert str(agent.working_directory) in status
        assert "Available Tools:" in status
        assert "Conversation Messages:" in status
    
    def test_conversation_history_truncation(self, agent):
        """Test that conversation history is truncated when it gets too long."""
        # Add many messages
        for i in range(105):  # More than the 100 limit
            agent._add_message("user", f"Message {i}")
        
        # Should be truncated to 50 most recent
        assert len(agent.conversation_history) == 50
        
        # Should have the most recent messages
        last_message = agent.conversation_history[-1]
        assert "Message 104" in last_message.content
"""Command-line interface for Agent LLM system."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .core.agent import Agent, AgentConfig
from .safety.safety_manager import SafetyConfig


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="agent-llm",
        description="Agentic LLM system with READ, WRITE, and EXECUTE tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agent-llm --workspace ./project "analyze this codebase"
  agent-llm --interactive
  agent-llm --version
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    parser.add_argument(
        "--workspace", "-w",
        type=str,
        default="./workspace",
        help="Working directory for agent operations (default: ./workspace)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict security mode"
    )
    
    parser.add_argument(
        "--allowed-commands",
        type=str,
        nargs="*",
        default=["python3", "pytest", "git", "ls", "cat"],
        help="Commands allowed for execution (default: python3, pytest, git, ls, cat)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive mode"
    )
    
    parser.add_argument(
        "request",
        nargs="?",
        help="Request to process (if not in interactive mode)"
    )
    
    return parser


def setup_agent(args: argparse.Namespace) -> Agent:
    """Set up the agent with configuration from command-line arguments."""
    # Ensure workspace directory exists
    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Create safety configuration
    safety_config = SafetyConfig(
        base_directory=str(workspace),
        enable_audit_logging=args.verbose,
        strict_mode=args.strict,
        allowed_commands=args.allowed_commands
    )
    
    # Create agent configuration
    agent_config = AgentConfig(
        working_directory=str(workspace),
        safety_config=safety_config,
        verbose_logging=args.verbose,
        auto_planning=True
    )
    
    return Agent(agent_config)


def interactive_mode(agent: Agent) -> None:
    """Run the agent in interactive mode."""
    print("🤖 Agent LLM Interactive Mode")
    print("=" * 40)
    print(f"📁 Working directory: {agent.working_directory}")
    print("💡 Type 'help' for commands, 'quit' to exit")
    print()
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == "help":
                print_help()
                continue
            
            if user_input.lower() == "status":
                print_status(agent)
                continue
            
            if user_input.lower().startswith("save"):
                save_session(agent, user_input)
                continue
            
            # Process the request
            print("🤖 Agent: ", end="", flush=True)
            response = agent.process_request(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


def print_help() -> None:
    """Print help information for interactive mode."""
    help_text = """
🤖 Agent LLM Commands:

Basic Commands:
  help              - Show this help message
  status            - Show agent status and statistics
  quit/exit/q       - Exit interactive mode
  save [filename]   - Save current session

Example Requests:
  "list files in the current directory"
  "create a Python script that prints hello world"
  "find all Python files and show their structure"
  "analyze the codebase and create a summary"
  "implement a calculator with tests"

The agent will automatically plan and execute complex multi-step tasks.
    """
    print(help_text)


def print_status(agent: Agent) -> None:
    """Print agent status information."""
    print("\n📊 Agent Status:")
    print(f"  📁 Working Directory: {agent.working_directory}")
    print(f"  🔧 Available Tools: {len(agent.tool_registry.get_all_tools())}")
    print(f"  💬 Conversation Messages: {len(agent.conversation_history)}")
    print(f"  📋 Current Plan: {agent.current_plan_id or 'None'}")
    
    # Security summary
    security_summary = agent.safety_manager.get_security_summary()
    print(f"  🛡️  Security Violations: {security_summary['total_violations']}")
    print()


def save_session(agent: Agent, command: str) -> None:
    """Save the current session."""
    parts = command.split()
    filename = parts[1] if len(parts) > 1 else None
    
    if agent.save_session(filename):
        print(f"💾 Session saved successfully")
    else:
        print(f"❌ Failed to save session")


def single_request_mode(agent: Agent, request: str) -> None:
    """Process a single request and exit."""
    print(f"🤖 Processing: {request}")
    print("=" * 40)
    
    response = agent.process_request(request)
    print(response)


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle version check
    if hasattr(args, 'version'):
        return
    
    # Validate arguments
    if not args.interactive and not args.request:
        parser.error("Must provide either --interactive or a request")
    
    try:
        # Set up the agent
        agent = setup_agent(args)
        
        if args.interactive:
            interactive_mode(agent)
        else:
            single_request_mode(agent, args.request)
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
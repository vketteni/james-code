"""READ tool for file system operations."""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..core.base import Tool, ToolResult, ExecutionContext


class ReadTool(Tool):
    """Tool for reading files and directories."""
    
    def __init__(self):
        super().__init__(
            name="read",
            description="Read files and navigate directories"
        )
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        action = kwargs.get("action")
        path = kwargs.get("path")
        
        if not action or action not in ["read_file", "list_directory", "file_exists", "get_file_info"]:
            return False
        
        if not path:
            return False
        
        return True
    
    def execute(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Execute the read tool."""
        if not self.validate_input(**kwargs):
            return ToolResult(
                success=False,
                data=None,
                error="Invalid input parameters"
            )
        
        action = kwargs["action"]
        path = kwargs["path"]
        
        try:
            # Convert to absolute path relative to working directory
            target_path = Path(context.working_directory) / path
            target_path = target_path.resolve()
            
            # Security check: ensure path is within working directory
            if not str(target_path).startswith(str(context.working_directory.resolve())):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Path outside working directory not allowed"
                )
            
            if action == "read_file":
                return self._read_file(target_path)
            elif action == "list_directory":
                return self._list_directory(target_path)
            elif action == "file_exists":
                return self._file_exists(target_path)
            elif action == "get_file_info":
                return self._get_file_info(target_path)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error executing read tool: {str(e)}"
            )
    
    def _read_file(self, path: Path) -> ToolResult:
        """Read contents of a file."""
        try:
            if not path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File does not exist: {path}"
                )
            
            if not path.is_file():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path is not a file: {path}"
                )
            
            # Check file size (limit to 10MB)
            if path.stat().st_size > 10 * 1024 * 1024:
                return ToolResult(
                    success=False,
                    data=None,
                    error="File too large (>10MB)"
                )
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return ToolResult(
                success=True,
                data=content,
                metadata={"file_size": path.stat().st_size}
            )
            
        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                data=None,
                error="File contains binary data or invalid encoding"
            )
    
    def _list_directory(self, path: Path) -> ToolResult:
        """List contents of a directory."""
        try:
            if not path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Directory does not exist: {path}"
                )
            
            if not path.is_dir():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path is not a directory: {path}"
                )
            
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime
                })
            
            return ToolResult(
                success=True,
                data=items,
                metadata={"item_count": len(items)}
            )
            
        except PermissionError:
            return ToolResult(
                success=False,
                data=None,
                error="Permission denied"
            )
    
    def _file_exists(self, path: Path) -> ToolResult:
        """Check if a file exists."""
        return ToolResult(
            success=True,
            data=path.exists(),
            metadata={"path": str(path)}
        )
    
    def _get_file_info(self, path: Path) -> ToolResult:
        """Get file information."""
        try:
            if not path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path does not exist: {path}"
                )
            
            stat = path.stat()
            info = {
                "name": path.name,
                "path": str(path),
                "type": "directory" if path.is_dir() else "file",
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "permissions": oct(stat.st_mode)[-3:]
            }
            
            return ToolResult(
                success=True,
                data=info
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error getting file info: {str(e)}"
            )
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read_file", "list_directory", "file_exists", "get_file_info"],
                    "description": "Action to perform"
                },
                "path": {
                    "type": "string",
                    "description": "Path to file or directory"
                }
            },
            "required": ["action", "path"]
        }
    
    def _get_examples(self) -> List[Dict[str, Any]]:
        """Get usage examples for this tool."""
        return [
            {
                "description": "Read a Python source file",
                "parameters": {
                    "action": "read_file",
                    "path": "src/main.py"
                }
            },
            {
                "description": "List files in current directory",
                "parameters": {
                    "action": "list_directory",
                    "path": "."
                }
            },
            {
                "description": "Check if a configuration file exists",
                "parameters": {
                    "action": "file_exists",
                    "path": "config.json"
                }
            },
            {
                "description": "Get detailed information about a file",
                "parameters": {
                    "action": "get_file_info",
                    "path": "README.md"
                }
            },
            {
                "description": "Explore a subdirectory",
                "parameters": {
                    "action": "list_directory",
                    "path": "tests"
                }
            }
        ]
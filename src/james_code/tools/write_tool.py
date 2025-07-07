"""WRITE tool for file system modifications."""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.base import Tool, ToolResult, ExecutionContext


class WriteTool(Tool):
    """Tool for writing files and creating directories."""
    
    def __init__(self):
        super().__init__(
            name="write",
            description="Write files and create directories"
        )
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        action = kwargs.get("action")
        path = kwargs.get("path")
        
        if not action or action not in ["write_file", "append_file", "create_directory", "delete_file", "delete_directory"]:
            return False
        
        if not path:
            return False
        
        # Content required for write/append operations
        if action in ["write_file", "append_file"] and "content" not in kwargs:
            return False
        
        return True
    
    def execute(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Execute the write tool."""
        if not self.validate_input(**kwargs):
            return ToolResult(
                success=False,
                data=None,
                error="Invalid input parameters"
            )
        
        action = kwargs["action"]
        path = kwargs["path"]
        content = kwargs.get("content", "")
        
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
            
            if action == "write_file":
                return self._write_file(target_path, content)
            elif action == "append_file":
                return self._append_file(target_path, content)
            elif action == "create_directory":
                return self._create_directory(target_path)
            elif action == "delete_file":
                return self._delete_file(target_path)
            elif action == "delete_directory":
                return self._delete_directory(target_path)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error executing write tool: {str(e)}"
            )
    
    def _write_file(self, path: Path, content: str) -> ToolResult:
        """Write content to a file."""
        try:
            # Check content size (limit to 10MB)
            if len(content.encode('utf-8')) > 10 * 1024 * 1024:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Content too large (>10MB)"
                )
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                data=f"File written: {path}",
                metadata={
                    "file_size": path.stat().st_size,
                    "created": not path.existed_before_write if hasattr(path, 'existed_before_write') else None
                }
            )
            
        except PermissionError:
            return ToolResult(
                success=False,
                data=None,
                error="Permission denied"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error writing file: {str(e)}"
            )
    
    def _append_file(self, path: Path, content: str) -> ToolResult:
        """Append content to a file."""
        try:
            # Check if file exists
            if not path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File does not exist: {path}"
                )
            
            # Check total size after append
            existing_size = path.stat().st_size
            new_content_size = len(content.encode('utf-8'))
            
            if existing_size + new_content_size > 10 * 1024 * 1024:
                return ToolResult(
                    success=False,
                    data=None,
                    error="File would exceed size limit (10MB) after append"
                )
            
            # Append content to file
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                data=f"Content appended to: {path}",
                metadata={
                    "file_size": path.stat().st_size,
                    "appended_bytes": new_content_size
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error appending to file: {str(e)}"
            )
    
    def _create_directory(self, path: Path) -> ToolResult:
        """Create a directory."""
        try:
            if path.exists():
                if path.is_dir():
                    return ToolResult(
                        success=True,
                        data=f"Directory already exists: {path}",
                        metadata={"already_existed": True}
                    )
                else:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Path exists but is not a directory: {path}"
                    )
            
            # Create directory with parents
            path.mkdir(parents=True, exist_ok=True)
            
            return ToolResult(
                success=True,
                data=f"Directory created: {path}",
                metadata={"created": True}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error creating directory: {str(e)}"
            )
    
    def _delete_file(self, path: Path) -> ToolResult:
        """Delete a file."""
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
            
            # Store file info before deletion
            file_size = path.stat().st_size
            
            # Delete the file
            path.unlink()
            
            return ToolResult(
                success=True,
                data=f"File deleted: {path}",
                metadata={"deleted_size": file_size}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error deleting file: {str(e)}"
            )
    
    def _delete_directory(self, path: Path) -> ToolResult:
        """Delete a directory."""
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
            
            # Check if directory is empty
            if any(path.iterdir()):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Directory is not empty: {path}"
                )
            
            # Delete the directory
            path.rmdir()
            
            return ToolResult(
                success=True,
                data=f"Directory deleted: {path}",
                metadata={"deleted": True}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error deleting directory: {str(e)}"
            )
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["write_file", "append_file", "create_directory", "delete_file", "delete_directory"],
                    "description": "Action to perform"
                },
                "path": {
                    "type": "string",
                    "description": "Path to file or directory"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (required for write_file and append_file)"
                }
            },
            "required": ["action", "path"]
        }
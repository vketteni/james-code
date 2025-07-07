"""UPDATE tool for surgical file modifications."""

import re
import difflib
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from ..core.base import Tool, ToolResult, ExecutionContext


class UpdateTool(Tool):
    """Tool for surgical file modifications and updates."""
    
    def __init__(self):
        super().__init__(
            name="update",
            description="Perform surgical file modifications and updates"
        )
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        action = kwargs.get("action")
        path = kwargs.get("path")
        
        if not action or action not in [
            "update_lines", "replace_pattern", "insert_at_line", 
            "delete_lines", "apply_patch", "replace_function"
        ]:
            return False
        
        if not path:
            return False
        
        # Action-specific validation
        if action == "update_lines":
            return all(k in kwargs for k in ["start_line", "end_line", "new_content"])
        
        if action == "replace_pattern":
            return all(k in kwargs for k in ["pattern", "replacement"])
        
        if action == "insert_at_line":
            return all(k in kwargs for k in ["line_number", "content"])
        
        if action == "delete_lines":
            return all(k in kwargs for k in ["start_line", "end_line"])
        
        if action == "apply_patch":
            return "patch_content" in kwargs
        
        if action == "replace_function":
            return all(k in kwargs for k in ["function_name", "new_content"])
        
        return True
    
    def execute(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Execute the update tool."""
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
            
            if not target_path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File does not exist: {target_path}"
                )
            
            if not target_path.is_file():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path is not a file: {target_path}"
                )
            
            # Create backup before modification
            backup_content = self._read_file(target_path)
            if backup_content is None:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Could not read file for backup"
                )
            
            # Execute the specific action
            if action == "update_lines":
                result = self._update_lines(target_path, backup_content, **kwargs)
            elif action == "replace_pattern":
                result = self._replace_pattern(target_path, backup_content, **kwargs)
            elif action == "insert_at_line":
                result = self._insert_at_line(target_path, backup_content, **kwargs)
            elif action == "delete_lines":
                result = self._delete_lines(target_path, backup_content, **kwargs)
            elif action == "apply_patch":
                result = self._apply_patch(target_path, backup_content, **kwargs)
            elif action == "replace_function":
                result = self._replace_function(target_path, backup_content, **kwargs)
            
            # Add backup content to result for rollback capability
            if result.success:
                result.metadata["backup_content"] = backup_content
                result.metadata["file_path"] = str(target_path)
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error executing update tool: {str(e)}"
            )
    
    def _read_file(self, path: Path) -> Optional[str]:
        """Read file content safely."""
        try:
            # Check file size (limit to 10MB)
            if path.stat().st_size > 10 * 1024 * 1024:
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except (UnicodeDecodeError, PermissionError):
            return None
    
    def _write_file(self, path: Path, content: str) -> bool:
        """Write file content safely."""
        try:
            # Check content size
            if len(content.encode('utf-8')) > 10 * 1024 * 1024:
                return False
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    def _update_lines(self, path: Path, original_content: str, **kwargs) -> ToolResult:
        """Update specific lines in a file."""
        start_line = kwargs["start_line"]
        end_line = kwargs["end_line"]
        new_content = kwargs["new_content"]
        
        try:
            lines = original_content.split('\n')
            
            # Validate line numbers (1-based)
            if start_line < 1 or end_line < 1:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Line numbers must be >= 1"
                )
            
            if start_line > len(lines) or end_line > len(lines):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Line numbers exceed file length ({len(lines)})"
                )
            
            if start_line > end_line:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Start line must be <= end line"
                )
            
            # Replace lines (convert to 0-based indexing)
            new_lines = new_content.split('\n') if new_content else []
            updated_lines = lines[:start_line-1] + new_lines + lines[end_line:]
            
            updated_content = '\n'.join(updated_lines)
            
            if not self._write_file(path, updated_content):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to write updated content"
                )
            
            return ToolResult(
                success=True,
                data=f"Updated lines {start_line}-{end_line} in {path}",
                metadata={
                    "lines_replaced": end_line - start_line + 1,
                    "new_lines_count": len(new_lines),
                    "total_lines": len(updated_lines)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error updating lines: {str(e)}"
            )
    
    def _replace_pattern(self, path: Path, original_content: str, **kwargs) -> ToolResult:
        """Replace pattern in file content."""
        pattern = kwargs["pattern"]
        replacement = kwargs["replacement"]
        use_regex = kwargs.get("use_regex", False)
        max_replacements = kwargs.get("max_replacements", 0)  # 0 = all
        
        try:
            if use_regex:
                try:
                    compiled_pattern = re.compile(pattern)
                    if max_replacements > 0:
                        updated_content = compiled_pattern.sub(replacement, original_content, count=max_replacements)
                    else:
                        updated_content = compiled_pattern.sub(replacement, original_content)
                    
                    # Count actual replacements
                    replacements_made = len(compiled_pattern.findall(original_content))
                    if max_replacements > 0:
                        replacements_made = min(replacements_made, max_replacements)
                        
                except re.error as e:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Invalid regex pattern: {str(e)}"
                    )
            else:
                # Simple string replacement
                if max_replacements > 0:
                    updated_content = original_content.replace(pattern, replacement, max_replacements)
                else:
                    updated_content = original_content.replace(pattern, replacement)
                
                replacements_made = original_content.count(pattern)
                if max_replacements > 0:
                    replacements_made = min(replacements_made, max_replacements)
            
            if replacements_made == 0:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Pattern not found in file"
                )
            
            if not self._write_file(path, updated_content):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to write updated content"
                )
            
            return ToolResult(
                success=True,
                data=f"Replaced {replacements_made} occurrences of pattern in {path}",
                metadata={
                    "pattern": pattern,
                    "replacement": replacement,
                    "replacements_made": replacements_made,
                    "use_regex": use_regex
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error replacing pattern: {str(e)}"
            )
    
    def _insert_at_line(self, path: Path, original_content: str, **kwargs) -> ToolResult:
        """Insert content at specific line."""
        line_number = kwargs["line_number"]
        content = kwargs["content"]
        
        try:
            lines = original_content.split('\n')
            
            # Validate line number (1-based, can insert after last line)
            if line_number < 1 or line_number > len(lines) + 1:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Line number must be between 1 and {len(lines) + 1}"
                )
            
            # Insert content (convert to 0-based indexing)
            new_lines = content.split('\n') if content else ['']
            updated_lines = lines[:line_number-1] + new_lines + lines[line_number-1:]
            
            updated_content = '\n'.join(updated_lines)
            
            if not self._write_file(path, updated_content):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to write updated content"
                )
            
            return ToolResult(
                success=True,
                data=f"Inserted content at line {line_number} in {path}",
                metadata={
                    "line_number": line_number,
                    "lines_inserted": len(new_lines),
                    "total_lines": len(updated_lines)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error inserting content: {str(e)}"
            )
    
    def _delete_lines(self, path: Path, original_content: str, **kwargs) -> ToolResult:
        """Delete specific lines from file."""
        start_line = kwargs["start_line"]
        end_line = kwargs["end_line"]
        
        try:
            lines = original_content.split('\n')
            
            # Validate line numbers
            if start_line < 1 or end_line < 1:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Line numbers must be >= 1"
                )
            
            if start_line > len(lines) or end_line > len(lines):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Line numbers exceed file length ({len(lines)})"
                )
            
            if start_line > end_line:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Start line must be <= end line"
                )
            
            # Delete lines (convert to 0-based indexing)
            updated_lines = lines[:start_line-1] + lines[end_line:]
            updated_content = '\n'.join(updated_lines)
            
            if not self._write_file(path, updated_content):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to write updated content"
                )
            
            return ToolResult(
                success=True,
                data=f"Deleted lines {start_line}-{end_line} from {path}",
                metadata={
                    "lines_deleted": end_line - start_line + 1,
                    "total_lines": len(updated_lines)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error deleting lines: {str(e)}"
            )
    
    def _apply_patch(self, path: Path, original_content: str, **kwargs) -> ToolResult:
        """Apply a unified diff patch to file."""
        patch_content = kwargs["patch_content"]
        
        try:
            # Parse patch content
            patch_lines = patch_content.strip().split('\n')
            
            # Simple patch parser (supports basic unified diff format)
            original_lines = original_content.split('\n')
            updated_lines = original_lines.copy()
            
            i = 0
            while i < len(patch_lines):
                line = patch_lines[i]
                
                if line.startswith('@@'):
                    # Parse hunk header: @@ -start,count +start,count @@
                    match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
                    if not match:
                        return ToolResult(
                            success=False,
                            data=None,
                            error="Invalid patch format"
                        )
                    
                    old_start = int(match.group(1)) - 1  # Convert to 0-based
                    new_start = int(match.group(3)) - 1  # Convert to 0-based
                    
                    # Process hunk
                    i += 1
                    line_offset = 0
                    
                    while i < len(patch_lines) and not patch_lines[i].startswith('@@'):
                        hunk_line = patch_lines[i]
                        
                        if hunk_line.startswith('-'):
                            # Delete line
                            if old_start + line_offset < len(updated_lines):
                                del updated_lines[old_start + line_offset]
                                line_offset -= 1
                        elif hunk_line.startswith('+'):
                            # Add line
                            new_content = hunk_line[1:]  # Remove '+' prefix
                            updated_lines.insert(old_start + line_offset + 1, new_content)
                            line_offset += 1
                        elif hunk_line.startswith(' '):
                            # Context line (no change)
                            pass
                        
                        i += 1
                else:
                    i += 1
            
            updated_content = '\n'.join(updated_lines)
            
            if not self._write_file(path, updated_content):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to write patched content"
                )
            
            return ToolResult(
                success=True,
                data=f"Applied patch to {path}",
                metadata={
                    "original_lines": len(original_lines),
                    "updated_lines": len(updated_lines),
                    "patch_applied": True
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error applying patch: {str(e)}"
            )
    
    def _replace_function(self, path: Path, original_content: str, **kwargs) -> ToolResult:
        """Replace entire function definition."""
        function_name = kwargs["function_name"]
        new_content = kwargs["new_content"]
        language = kwargs.get("language", "python")
        
        try:
            # Language-specific function patterns
            if language == "python":
                pattern = rf"^(\s*)(def\s+{re.escape(function_name)}\s*\([^)]*\).*?)(?=^\s*(?:def\s+|class\s+|\Z))"
            elif language == "javascript":
                pattern = rf"^(\s*)(function\s+{re.escape(function_name)}\s*\([^)]*\).*?)(?=^\s*(?:function\s+|var\s+|let\s+|const\s+|\Z))"
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Language {language} not supported for function replacement"
                )
            
            # Find and replace function
            match = re.search(pattern, original_content, re.MULTILINE | re.DOTALL)
            if not match:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Function {function_name} not found"
                )
            
            # Replace function with new content
            indentation = match.group(1)
            updated_content = original_content.replace(match.group(0), indentation + new_content)
            
            if not self._write_file(path, updated_content):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to write updated content"
                )
            
            return ToolResult(
                success=True,
                data=f"Replaced function {function_name} in {path}",
                metadata={
                    "function_name": function_name,
                    "language": language,
                    "original_length": len(match.group(0)),
                    "new_length": len(new_content)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error replacing function: {str(e)}"
            )
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["update_lines", "replace_pattern", "insert_at_line", "delete_lines", "apply_patch", "replace_function"],
                    "description": "Type of update operation"
                },
                "path": {
                    "type": "string",
                    "description": "Path to file to update"
                },
                "start_line": {
                    "type": "integer",
                    "description": "Start line number (1-based)"
                },
                "end_line": {
                    "type": "integer",
                    "description": "End line number (1-based)"
                },
                "new_content": {
                    "type": "string",
                    "description": "New content to insert/replace"
                },
                "pattern": {
                    "type": "string",
                    "description": "Pattern to search for"
                },
                "replacement": {
                    "type": "string",
                    "description": "Replacement text"
                },
                "use_regex": {
                    "type": "boolean",
                    "description": "Use regex for pattern matching",
                    "default": False
                },
                "max_replacements": {
                    "type": "integer",
                    "description": "Maximum number of replacements (0 = all)",
                    "default": 0
                },
                "line_number": {
                    "type": "integer",
                    "description": "Line number to insert at (1-based)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to insert"
                },
                "patch_content": {
                    "type": "string",
                    "description": "Unified diff patch content"
                },
                "function_name": {
                    "type": "string",
                    "description": "Name of function to replace"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language",
                    "default": "python"
                }
            },
            "required": ["action", "path"]
        }
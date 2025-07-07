"""FIND tool for advanced search capabilities."""

import os
import re
import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from ..core.base import Tool, ToolResult, ExecutionContext


class FindTool(Tool):
    """Tool for finding files and searching content."""
    
    def __init__(self):
        super().__init__(
            name="find",
            description="Find files and search content with advanced patterns"
        )
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        action = kwargs.get("action")
        
        if not action or action not in [
            "find_files", "search_content", "find_function", 
            "grep_recursive", "find_by_size", "find_by_date"
        ]:
            return False
        
        # Action-specific validation
        if action == "find_files" and not kwargs.get("pattern"):
            return False
        
        if action == "search_content" and not kwargs.get("query"):
            return False
        
        if action == "find_function" and not kwargs.get("function_name"):
            return False
        
        if action == "grep_recursive" and not kwargs.get("pattern"):
            return False
        
        return True
    
    def execute(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Execute the find tool."""
        if not self.validate_input(**kwargs):
            return ToolResult(
                success=False,
                data=None,
                error="Invalid input parameters"
            )
        
        action = kwargs["action"]
        
        try:
            if action == "find_files":
                return self._find_files(context, **kwargs)
            elif action == "search_content":
                return self._search_content(context, **kwargs)
            elif action == "find_function":
                return self._find_function(context, **kwargs)
            elif action == "grep_recursive":
                return self._grep_recursive(context, **kwargs)
            elif action == "find_by_size":
                return self._find_by_size(context, **kwargs)
            elif action == "find_by_date":
                return self._find_by_date(context, **kwargs)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error executing find tool: {str(e)}"
            )
    
    def _find_files(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Find files by name pattern."""
        pattern = kwargs["pattern"]
        directory = kwargs.get("directory", ".")
        max_depth = kwargs.get("max_depth", 10)
        include_hidden = kwargs.get("include_hidden", False)
        
        try:
            search_dir = Path(context.working_directory) / directory
            search_dir = search_dir.resolve()
            
            # Security check
            if not str(search_dir).startswith(str(context.working_directory.resolve())):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Search directory outside working directory"
                )
            
            if not search_dir.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Directory does not exist: {search_dir}"
                )
            
            matches = []
            self._find_files_recursive(search_dir, pattern, matches, 0, max_depth, include_hidden)
            
            # Convert paths to relative paths
            relative_matches = []
            for match in matches:
                try:
                    rel_path = match.relative_to(context.working_directory)
                    relative_matches.append({
                        "path": str(rel_path),
                        "absolute_path": str(match),
                        "type": "directory" if match.is_dir() else "file",
                        "size": match.stat().st_size if match.is_file() else None,
                        "modified": match.stat().st_mtime
                    })
                except ValueError:
                    # Skip files outside working directory
                    continue
            
            return ToolResult(
                success=True,
                data=relative_matches,
                metadata={
                    "pattern": pattern,
                    "search_directory": str(search_dir),
                    "match_count": len(relative_matches),
                    "max_depth": max_depth
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error finding files: {str(e)}"
            )
    
    def _find_files_recursive(self, directory: Path, pattern: str, matches: List[Path], 
                            current_depth: int, max_depth: int, include_hidden: bool):
        """Recursively find files matching pattern."""
        if current_depth > max_depth:
            return
        
        try:
            for item in directory.iterdir():
                # Skip hidden files unless requested
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                # Check if item matches pattern
                if fnmatch.fnmatch(item.name, pattern):
                    matches.append(item)
                
                # Recurse into directories
                if item.is_dir() and current_depth < max_depth:
                    self._find_files_recursive(item, pattern, matches, current_depth + 1, max_depth, include_hidden)
                    
        except PermissionError:
            # Skip directories we can't read
            pass
    
    def _search_content(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Search for content within files."""
        query = kwargs["query"]
        directory = kwargs.get("directory", ".")
        file_types = kwargs.get("file_types", ["*"])
        max_results = kwargs.get("max_results", 100)
        case_sensitive = kwargs.get("case_sensitive", False)
        use_regex = kwargs.get("use_regex", False)
        
        try:
            search_dir = Path(context.working_directory) / directory
            search_dir = search_dir.resolve()
            
            # Security check
            if not str(search_dir).startswith(str(context.working_directory.resolve())):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Search directory outside working directory"
                )
            
            if not search_dir.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Directory does not exist: {search_dir}"
                )
            
            # Compile regex pattern if needed
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                try:
                    pattern = re.compile(query, flags)
                except re.error as e:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Invalid regex pattern: {str(e)}"
                    )
            else:
                pattern = query if case_sensitive else query.lower()
            
            matches = []
            self._search_content_recursive(search_dir, pattern, file_types, matches, 
                                         max_results, case_sensitive, use_regex, context.working_directory)
            
            return ToolResult(
                success=True,
                data=matches,
                metadata={
                    "query": query,
                    "search_directory": str(search_dir),
                    "match_count": len(matches),
                    "file_types": file_types,
                    "case_sensitive": case_sensitive,
                    "use_regex": use_regex
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error searching content: {str(e)}"
            )
    
    def _search_content_recursive(self, directory: Path, pattern: Union[str, re.Pattern], 
                                file_types: List[str], matches: List[Dict], max_results: int,
                                case_sensitive: bool, use_regex: bool, working_dir: Path):
        """Recursively search content in files."""
        if len(matches) >= max_results:
            return
        
        try:
            for item in directory.iterdir():
                if len(matches) >= max_results:
                    break
                
                if item.is_file():
                    # Check if file type matches
                    if not any(fnmatch.fnmatch(item.name, ft) for ft in file_types):
                        continue
                    
                    # Skip large files (>10MB)
                    if item.stat().st_size > 10 * 1024 * 1024:
                        continue
                    
                    try:
                        with open(item, 'r', encoding='utf-8') as f:
                            for line_num, line in enumerate(f, 1):
                                if use_regex:
                                    if pattern.search(line):
                                        rel_path = item.relative_to(working_dir)
                                        matches.append({
                                            "file": str(rel_path),
                                            "line": line_num,
                                            "content": line.strip(),
                                            "match_type": "regex"
                                        })
                                else:
                                    search_line = line if case_sensitive else line.lower()
                                    if pattern in search_line:
                                        rel_path = item.relative_to(working_dir)
                                        matches.append({
                                            "file": str(rel_path),
                                            "line": line_num,
                                            "content": line.strip(),
                                            "match_type": "string"
                                        })
                                
                                if len(matches) >= max_results:
                                    break
                    except (UnicodeDecodeError, PermissionError):
                        # Skip binary files or files we can't read
                        continue
                
                elif item.is_dir() and not item.name.startswith('.'):
                    self._search_content_recursive(item, pattern, file_types, matches, 
                                                 max_results, case_sensitive, use_regex, working_dir)
                    
        except PermissionError:
            # Skip directories we can't read
            pass
    
    def _find_function(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Find function definitions in code files."""
        function_name = kwargs["function_name"]
        language = kwargs.get("language", "auto")
        directory = kwargs.get("directory", ".")
        
        # Language-specific function patterns
        patterns = {
            "python": [
                rf"def\s+{re.escape(function_name)}\s*\(",
                rf"async\s+def\s+{re.escape(function_name)}\s*\(",
                rf"class\s+{re.escape(function_name)}\s*[\(\:]"
            ],
            "javascript": [
                rf"function\s+{re.escape(function_name)}\s*\(",
                rf"const\s+{re.escape(function_name)}\s*=",
                rf"let\s+{re.escape(function_name)}\s*=",
                rf"var\s+{re.escape(function_name)}\s*=",
                rf"{re.escape(function_name)}\s*:\s*function",
                rf"{re.escape(function_name)}\s*=>\s*"
            ],
            "java": [
                rf"(public|private|protected)?\s*(static)?\s*\w+\s+{re.escape(function_name)}\s*\(",
                rf"class\s+{re.escape(function_name)}\s*"
            ],
            "c": [
                rf"\w+\s+{re.escape(function_name)}\s*\(",
                rf"struct\s+{re.escape(function_name)}\s*"
            ]
        }
        
        if language == "auto":
            # Use all patterns
            search_patterns = []
            for lang_patterns in patterns.values():
                search_patterns.extend(lang_patterns)
        else:
            search_patterns = patterns.get(language, [rf"{re.escape(function_name)}"])
        
        try:
            matches = []
            search_dir = Path(context.working_directory) / directory
            
            for pattern_str in search_patterns:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                result = self._search_content_recursive(
                    search_dir, pattern, ["*.py", "*.js", "*.java", "*.c", "*.cpp", "*.h"],
                    matches, 50, False, True, context.working_directory
                )
            
            return ToolResult(
                success=True,
                data=matches,
                metadata={
                    "function_name": function_name,
                    "language": language,
                    "patterns_used": search_patterns
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error finding function: {str(e)}"
            )
    
    def _grep_recursive(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Grep-like recursive search."""
        pattern = kwargs["pattern"]
        directory = kwargs.get("directory", ".")
        file_types = kwargs.get("file_types", ["*"])
        max_results = kwargs.get("max_results", 100)
        
        return self._search_content(
            context,
            query=pattern,
            directory=directory,
            file_types=file_types,
            max_results=max_results,
            use_regex=True
        )
    
    def _find_by_size(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Find files by size criteria."""
        min_size = kwargs.get("min_size", 0)
        max_size = kwargs.get("max_size", float('inf'))
        directory = kwargs.get("directory", ".")
        
        try:
            search_dir = Path(context.working_directory) / directory
            search_dir = search_dir.resolve()
            
            if not str(search_dir).startswith(str(context.working_directory.resolve())):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Search directory outside working directory"
                )
            
            matches = []
            for item in search_dir.rglob("*"):
                if item.is_file():
                    size = item.stat().st_size
                    if min_size <= size <= max_size:
                        rel_path = item.relative_to(context.working_directory)
                        matches.append({
                            "path": str(rel_path),
                            "size": size,
                            "modified": item.stat().st_mtime
                        })
            
            return ToolResult(
                success=True,
                data=matches,
                metadata={
                    "min_size": min_size,
                    "max_size": max_size,
                    "match_count": len(matches)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error finding by size: {str(e)}"
            )
    
    def _find_by_date(self, context: ExecutionContext, **kwargs) -> ToolResult:
        """Find files by modification date."""
        min_date = kwargs.get("min_date")  # Unix timestamp
        max_date = kwargs.get("max_date")  # Unix timestamp
        directory = kwargs.get("directory", ".")
        
        try:
            search_dir = Path(context.working_directory) / directory
            search_dir = search_dir.resolve()
            
            if not str(search_dir).startswith(str(context.working_directory.resolve())):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Search directory outside working directory"
                )
            
            matches = []
            for item in search_dir.rglob("*"):
                if item.is_file():
                    mtime = item.stat().st_mtime
                    if (min_date is None or mtime >= min_date) and \
                       (max_date is None or mtime <= max_date):
                        rel_path = item.relative_to(context.working_directory)
                        matches.append({
                            "path": str(rel_path),
                            "size": item.stat().st_size,
                            "modified": mtime
                        })
            
            return ToolResult(
                success=True,
                data=matches,
                metadata={
                    "min_date": min_date,
                    "max_date": max_date,
                    "match_count": len(matches)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error finding by date: {str(e)}"
            )
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["find_files", "search_content", "find_function", "grep_recursive", "find_by_size", "find_by_date"],
                    "description": "Type of search to perform"
                },
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (for find_files, grep_recursive)"
                },
                "query": {
                    "type": "string",
                    "description": "Search query (for search_content)"
                },
                "function_name": {
                    "type": "string",
                    "description": "Function name to find (for find_function)"
                },
                "directory": {
                    "type": "string",
                    "description": "Directory to search in (default: current)",
                    "default": "."
                },
                "file_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File types to include (e.g., ['*.py', '*.js'])",
                    "default": ["*"]
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 100
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum directory depth",
                    "default": 10
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Case sensitive search",
                    "default": False
                },
                "use_regex": {
                    "type": "boolean",
                    "description": "Use regex patterns",
                    "default": False
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (for find_function)",
                    "default": "auto"
                },
                "min_size": {
                    "type": "integer",
                    "description": "Minimum file size in bytes"
                },
                "max_size": {
                    "type": "integer",
                    "description": "Maximum file size in bytes"
                },
                "min_date": {
                    "type": "number",
                    "description": "Minimum modification date (Unix timestamp)"
                },
                "max_date": {
                    "type": "number",
                    "description": "Maximum modification date (Unix timestamp)"
                }
            },
            "required": ["action"]
        }
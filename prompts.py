"""
Centralized storage for all prompts used in code review analysis.
Each prompt is organized by analyzer type and purpose.
"""

# Common templates that can be used across different analyzers
DIFF_ANALYSIS_TEMPLATE = """You are a senior staff principle engineer performing a security and functionality focused code review.
Go through this PR diff line by line, focusing ONLY on bugs that could cause:
1. Runtime errors or crashes
2. Race conditions 
3. Memory leaks
4. State management issues
5. Security vulnerabilities
6. Data loss or corruption
7. Performance issues
8. Resource leaks

Remember: Only report issues that could actually break functionality or corrupt data at runtime."""

COMMENT_CATEGORIES = """
1. CRITICAL_BUG: Comments identifying serious issues that could cause crashes, data loss, security vulnerabilities, etc.
2. NITPICK: Minor suggestions about style, formatting, variable names, or trivial changes that don't affect functionality
3. OTHER: Everything else - general suggestions, questions, or feedback that don't fit the above"""

# Gemini-specific prompts
GEMINI_PROMPTS = {
    "diff_analysis": f"""{DIFF_ANALYSIS_TEMPLATE}

The output format should be the following JSON EXACTLY:
{{
    'issues': [
        {{
            'bug_description': '1-2 line description of how this bug impacts runtime behavior and how to fix it',
            'severity': 'HIGH|MEDIUM|LOW based on potential user impact',
            'bug_type': 'RACE_CONDITION|STATE_MANAGEMENT|MEMORY_LEAK|SECURITY|CRASH|CORRUPTION',
            'file_name': 'Affected file',
            'line_numbers': 'Relevant line numbers',
            'snippet': 'Code showing the bug'
        }}
    ]
}}""",

    "comment_categorization": f"""As a senior engineer, analyze these code review comments and categorize each one into exactly ONE of:
{COMMENT_CATEGORIES}

PR #{{pr_number}} by {{bot_name}}:
{{comments}}

Respond with a JSON array where each object has:
{{
    "comment_index": <index>,
    "category": "CRITICAL_BUG|NITPICK|OTHER",
    "reasoning": "Brief explanation of why this category was chosen"
}}
IMPORTANT: Each comment MUST be categorized. The category field MUST be exactly one of CRITICAL_BUG, NITPICK, or OTHER."""
}

# Claude-specific prompts
CLAUDE_PROMPTS = {
    "diff_analysis": f"""{DIFF_ANALYSIS_TEMPLATE}

Analyze this PR diff for potential bugs and issues:

{{diff}}

For each issue found, provide detailed analysis following this structure:
{{
    "description": "Clear explanation of the bug and its impact",
    "severity": "HIGH|MEDIUM|LOW",
    "category": "SECURITY|RACE_CONDITION|MEMORY_LEAK|PERFORMANCE|CRASH",
    "file": "affected_file.ext",
    "lines": "line numbers",
    "code": "relevant code snippet",
    "fix": "suggested fix approach"
}}""",

    "comment_categorization": f"""Analyze these code review comments and categorize each as either:
{COMMENT_CATEGORIES}

PR #{{pr_number}} comments from {{bot_name}}:
{{comments}}

Respond with a JSON array of objects:
[
    {{
        "comment_index": number,
        "category": "CRITICAL_BUG|NITPICK|OTHER",
        "reasoning": "Brief explanation"
    }}
]"""
}

# GPT-4-specific prompts
GPT4_PROMPTS = {
    "diff_analysis": f"""{DIFF_ANALYSIS_TEMPLATE}

Analyze this PR diff for potential bugs:

{{diff}}

Focus on issues that could cause:
1. Runtime errors or crashes
2. Race conditions
3. Memory leaks
4. State management issues
5. Security vulnerabilities
6. Data loss or corruption
7. Performance issues
8. Resource leaks

Provide analysis in this JSON format:
{{
    "issues": [
        {{
            "description": "Clear explanation of the bug",
            "severity": "HIGH|MEDIUM|LOW",
            "category": "SECURITY|RACE_CONDITION|MEMORY_LEAK|PERFORMANCE|CRASH",
            "file": "affected_file",
            "lines": "line numbers",
            "code": "relevant snippet",
            "fix": "suggested fix"
        }}
    ]
}}""",

    "comment_categorization": f"""Analyze code review comments and categorize each one.
Categories:
{COMMENT_CATEGORIES}

Analyze these code review comments from PR #{{pr_number}} by {{bot_name}}:

{{comments}}

Categorize each comment and explain your reasoning. Respond in JSON format:
{{
    "comments": [
        {{
            "index": number,
            "category": "CRITICAL_BUG|NITPICK|OTHER",
            "reasoning": "Brief explanation"
        }}
    ]
}}"""
}


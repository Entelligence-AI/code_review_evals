import json
import logging
from collections import defaultdict
import anthropic
from typing import List, Dict

from .base import BaseReviewAnalyzer
from ..github.api import ReviewComment, PRDiff
from ..utils.rate_limiter import RateLimiter, make_api_call_with_backoff

logger = logging.getLogger(__name__)

class ClaudeReviewAnalyzer(BaseReviewAnalyzer):
    def __init__(self, api_key: str, requests_per_minute: int = 60):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.rate_limiter = RateLimiter(requests_per_minute)

    async def analyze_diff(self, diff: PRDiff) -> List[ReviewComment]:
        """Analyze a PR diff using Claude"""
        prompt = """You are a senior staff principle engineer performing a security and functionality focused code review.
        Analyze this PR diff for potential bugs and issues:

        {diff}

        Focus on identifying serious issues that could cause:
        1. Runtime errors or crashes
        2. Race conditions
        3. Memory leaks
        4. State management issues
        5. Security vulnerabilities
        6. Data loss or corruption
        7. Performance issues
        8. Resource leaks

        For each issue found, provide detailed analysis following this structure:
        {
            "description": "Clear explanation of the bug and its impact",
            "severity": "HIGH|MEDIUM|LOW",
            "category": "SECURITY|RACE_CONDITION|MEMORY_LEAK|PERFORMANCE|CRASH",
            "file": "affected_file.ext",
            "lines": "line numbers",
            "code": "relevant code snippet",
            "fix": "suggested fix approach"
        }

        Only include serious technical issues that could affect runtime behavior or security."""

        try:
            def make_api_call():
                return self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": prompt.format(diff=diff.diff_content)
                    }]
                )

            response = await make_api_call_with_backoff(make_api_call)
            
            try:
                results = json.loads(response.content[0].text)
                if not isinstance(results, list):
                    results = [results]

                return [
                    ReviewComment(
                        file_name=result['file'],
                        chunk=result['code'],
                        comment=f"{result['description']}\n\nSuggested fix: {result['fix']}",
                        line_nums=result['lines'],
                        bot_name='claude',
                        pr_number=diff.pr_number,
                        category=result['category']
                    )
                    for result in results
                ]
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing Claude response: {str(e)}")
                return []

        except Exception as e:
            logger.error(f"Error analyzing diff with Claude: {str(e)}")
            return []

    async def analyze_comment_quality(self, comments: List[ReviewComment]) -> Dict[str, Dict[str, float]]:
        """Analyze the quality of bot comments using Claude"""
        bot_metrics = defaultdict(lambda: {
            'critical_bug_ratio': 0.0,
            'nitpick_ratio': 0.0,
            'other_ratio': 0.0,
            'total_comments': 0
        })

        # Group comments by bot and PR
        bot_pr_comments = defaultdict(lambda: defaultdict(list))
        for comment in comments:
            bot_pr_comments[comment.bot_name][comment.pr_number].append(comment)

        categorization_prompt = """Analyze these code review comments and categorize each as either:
            1. CRITICAL_BUG: Comments identifying serious technical issues
            2. NITPICK: Minor style/formatting suggestions
            3. OTHER: General feedback or questions

            PR #{pr_number} comments from {bot_name}:
            {comments}

            Respond with a JSON array of objects:
            [
                {
                    "comment_index": number,
                    "category": "CRITICAL_BUG|NITPICK|OTHER",
                    "reasoning": "Brief explanation"
                }
            ]"""

        for bot_name, pr_comments in bot_pr_comments.items():
            for pr_number, comment_list in pr_comments.items():
                try:
                    formatted_comments = "\n\n".join([
                        f"Comment {i}:\nFile: {c.file_name}\nLines: {c.line_nums}\nComment: {c.comment}\nCode:\n{c.chunk}"
                        for i, c in enumerate(comment_list)
                    ])

                    def make_api_call():
                        return self.client.messages.create(
                            model="claude-3-opus-20240229",
                            max_tokens=4096,
                            messages=[{
                                "role": "user",
                                "content": categorization_prompt.format(
                                    pr_number=pr_number,
                                    bot_name=bot_name,
                                    comments=formatted_comments
                                )
                            }]
                        )

                    response = await make_api_call_with_backoff(make_api_call)
                    
                    try:
                        results = json.loads(response.content[0].text)
                        if not isinstance(results, list):
                            results = [results]

                        bot_metrics[bot_name]['total_comments'] += len(comment_list)
                        for result in results:
                            category = result['category']
                            if category == 'CRITICAL_BUG':
                                bot_metrics[bot_name]['critical_bug_ratio'] += 1
                            elif category == 'NITPICK':
                                bot_metrics[bot_name]['nitpick_ratio'] += 1
                            else:
                                bot_metrics[bot_name]['other_ratio'] += 1

                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing Claude categorization response: {str(e)}")
                        continue

                except Exception as e:
                    logger.error(f"Error processing comments with Claude for {bot_name} PR #{pr_number}: {str(e)}")
                    continue

        # Convert counts to ratios
        for bot in bot_metrics:
            total = bot_metrics[bot]['total_comments']
            if total > 0:
                for metric in ['critical_bug_ratio', 'nitpick_ratio', 'other_ratio']:
                    bot_metrics[bot][metric] /= total

        return dict(bot_metrics)
    
    
import json
import logging
from collections import defaultdict
import google.generativeai as genai
from typing import List, Dict

from .base import BaseReviewAnalyzer
from ..github.api import ReviewComment, PRDiff
from ..utils.rate_limiter import RateLimiter, make_api_call_with_backoff

logger = logging.getLogger(__name__)

class GeminiReviewAnalyzer(BaseReviewAnalyzer):
    def __init__(self, api_key: str, requests_per_minute: int = 60):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash-002")
        self.rate_limiter = RateLimiter(requests_per_minute)

    async def analyze_diff(self, diff: PRDiff) -> List[ReviewComment]:
        """Analyze a PR diff using Gemini with rate limiting and retries"""
        from ..prompts import GEMINI_PROMPTS
        prompt = GEMINI_PROMPTS["diff_analysis"]

        try:
            def make_api_call():
                generation_config = genai.GenerationConfig(
                    response_mime_type="application/json"
                )
                return self.model.generate_content(
                    prompt.format(diff=diff.diff_content),
                    generation_config=generation_config
                )

            response = await make_api_call_with_backoff(make_api_call)
            
            # Extract text from response
            response_text = response.text if hasattr(response, 'text') else response.parts[0].text
            
            try:
                results = json.loads(response_text)
                issues = results.get('issues', [])

                return [
                    ReviewComment(
                        file_name=issue['file_name'],
                        chunk=issue['snippet'],
                        comment=f"{issue['bug_description']} (Severity: {issue['severity']})",
                        line_nums=issue['line_numbers'],
                        bot_name='gemini',
                        pr_number=diff.pr_number,
                        category=issue['bug_type']
                    )
                    for issue in issues
                ]

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing Gemini response: {str(e)}")
                logger.error(f"Raw response: {response_text}")
                return []

        except Exception as e:
            logger.error(f"Error analyzing diff: {str(e)}")
            return []

    async def analyze_comment_quality(self, comments: List[ReviewComment]) -> Dict[str, Dict[str, float]]:
        """Analyze comment quality with rate limiting and retries"""
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

        for bot_name, pr_comments in bot_pr_comments.items():
            for pr_number, comment_list in pr_comments.items():
                try:
                    formatted_comments = self._format_comments_for_analysis(comment_list)
                    
                    def make_api_call():
                        return self.model.generate_content(
                            self._build_categorization_prompt(pr_number, bot_name, formatted_comments),
                            generation_config=genai.GenerationConfig(
                                response_mime_type="application/json"
                            )
                        )

                    response = await make_api_call_with_backoff(make_api_call)
                    await self._process_quality_response(response, bot_metrics, bot_name, comment_list)

                except Exception as e:
                    logger.error(f"Error processing comments for {bot_name} PR #{pr_number}: {str(e)}")
                    continue

        return self._finalize_metrics(bot_metrics)

    def _format_comments_for_analysis(self, comments: List[ReviewComment]) -> str:
        """Format comments for analysis prompt"""
        return "\n\n".join([
            f"Comment {i}:\nFile: {c.file_name}\nLines: {c.line_nums}\n"
            f"Comment: {c.comment}\nCode:\n{c.chunk}"
            for i, c in enumerate(comments)
        ])

    def _build_categorization_prompt(self, pr_number: int, bot_name: str, comments: str) -> str:
        """Build the prompt for comment categorization"""
        from ..prompts import GEMINI_PROMPTS
        return GEMINI_PROMPTS["comment_categorization"].format(
            pr_number=pr_number,
            bot_name=bot_name,
            comments=comments
        )

    async def _process_quality_response(self, response, bot_metrics: dict, bot_name: str, comments: List[ReviewComment]):
        """Process and validate the categorization response"""
        try:
            response_text = response.text if hasattr(response, 'text') else response.parts[0].text
            results = json.loads(response_text)
            
            if not isinstance(results, list):
                logger.warning(f"Unexpected response format from Gemini for {bot_name}. Expected list, got {type(results)}")
                return

            bot_metrics[bot_name]['total_comments'] += len(comments)
            
            for result in results:
                if not isinstance(result, dict) or 'category' not in result:
                    logger.warning(f"Invalid result format in Gemini response: {result}")
                    continue
                    
                category = result['category'].upper()
                if category == 'CRITICAL_BUG':
                    bot_metrics[bot_name]['critical_bug_ratio'] += 1
                elif category == 'NITPICK':
                    bot_metrics[bot_name]['nitpick_ratio'] += 1
                else:
                    bot_metrics[bot_name]['other_ratio'] += 1

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gemini response for {bot_name}: {str(e)}")
            logger.error(f"Raw response: {response_text}")

    def _finalize_metrics(self, bot_metrics: dict) -> Dict[str, Dict[str, float]]:
        """Convert raw counts to ratios and finalize metrics"""
        final_metrics = {}
        
        for bot, metrics in bot_metrics.items():
            total = metrics['total_comments']
            if total > 0:
                final_metrics[bot] = {
                    'critical_bug_ratio': metrics['critical_bug_ratio'] / total,
                    'nitpick_ratio': metrics['nitpick_ratio'] / total,
                    'other_ratio': metrics['other_ratio'] / total,
                    'total_comments': total
                }
            else:
                final_metrics[bot] = {
                    'critical_bug_ratio': 0.0,
                    'nitpick_ratio': 0.0,
                    'other_ratio': 0.0,
                    'total_comments': 0
                }
                
        return final_metrics
    
    
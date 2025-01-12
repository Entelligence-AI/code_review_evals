import json
import logging
from collections import defaultdict
import google.generativeai as genai
from typing import List, Dict, Any

from .base import BaseAnalyzer
from models import ReviewComment, PRDiff
from utils.rate_limiter import RateLimiter, make_api_call_with_backoff
from prompts import GEMINI_PROMPTS

logger = logging.getLogger(__name__)

class GeminiAnalyzer(BaseAnalyzer):
    def __init__(self, api_key: str, requests_per_minute: int = 60):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash-002")
        self.rate_limiter = RateLimiter(requests_per_minute)


    async def analyze_diff(self, diff: PRDiff) -> List[ReviewComment]:
        """Analyze a PR diff using Gemini"""

        try:
            def make_api_call():
                logger.info("Make API call")
                generation_config = genai.GenerationConfig(
                    response_mime_type="application/json"
                )

                print(diff.diff_content)
                prompt = GEMINI_PROMPTS["diff_analysis"].format(diff=diff.diff_content)
                logger.info(f"Prompt: {prompt}")
                return self.model.generate_content(
                    GEMINI_PROMPTS["diff_analysis"].format(diff=diff.diff_content),
                    generation_config=generation_config
                )

            response = await make_api_call_with_backoff(make_api_call)
            response_text = response.text if hasattr(response, 'text') else response.parts[0].text
            
            # Log the raw response for debugging
            logger.debug(f"Raw Gemini response: {response_text}")
            
            try:
                parsed_response = json.loads(response_text)
                # Check if response has 'issues' key
                if isinstance(parsed_response, dict) and 'issues' in parsed_response:
                    results = parsed_response['issues']
                else:
                    # If no 'issues' key, treat the whole response as the results
                    results = [parsed_response] if isinstance(parsed_response, dict) else parsed_response

                # Filter out any malformed results
                valid_results = []
                for result in results:
                    if all(key in result for key in ['file_name', 'snippet', 'bug_description', 'line_numbers']):
                        valid_results.append(result)
                    else:
                        logger.warning(f"Skipping malformed result: {result}")

                return [
                    ReviewComment(
                        file_name=result['file_name'],
                        chunk=result['snippet'],
                        comment=result['bug_description'],
                        line_nums=result['line_numbers'],
                        bot_name='gemini',
                        pr_number=diff.pr_number,
                    )
                    for result in valid_results
                ]

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
                logger.error(f"Response text: {response_text}")
                return []

        except Exception as e:
            logger.error(f"Error analyzing diff: {str(e)}")
            logger.debug("Full error:", exc_info=True)
            return []


    async def analyze_comment_quality_in_batch(self, comments: List[ReviewComment]) -> Dict[str, Dict]:
        """Analyze comments in batches with detailed classification"""
        BATCH_SIZE = 25
        
        bot_metrics = defaultdict(lambda: {
            'critical_bug_ratio': 0.0,
            'nitpick_ratio': 0.0,
            'other_ratio': 0.0,
            'total_comments': 0
        })
        
        classifications = defaultdict(lambda: defaultdict(list))

        # Group comments by bot and PR
        bot_pr_comments = defaultdict(lambda: defaultdict(list))
        for comment in comments:
            bot_pr_comments[comment.bot_name][comment.pr_number].append(comment)

        for bot_name, pr_comments in bot_pr_comments.items():
            for pr_number, comment_list in pr_comments.items():
                for i in range(0, len(comment_list), BATCH_SIZE):
                    batch = comment_list[i:i + BATCH_SIZE]
                    
                    try:
                        formatted_comments = self._format_comments_for_analysis(batch)
                        analysis_results = await self._analyze_batch(
                            bot_name, pr_number, formatted_comments
                        )
                        
                        self._update_metrics_and_classifications(
                            bot_metrics, classifications, bot_name, pr_number, 
                            analysis_results, batch, i
                        )

                    except Exception as e:
                        logger.error(f"Error processing batch for {bot_name} PR #{pr_number}: {str(e)}")
                        continue

        return {
            'metrics': self._finalize_metrics(bot_metrics),
            'classifications': dict(classifications)
        }


    async def analyze_comment_quality(self, comments: List[ReviewComment]) -> Dict[str, Dict[str, float]]:
        """Simple comment quality analysis without detailed classifications"""
        result = await self.analyze_comment_quality_in_batch(comments)
        return result['metrics']


    def _format_comments_for_analysis(self, comments: List[ReviewComment]) -> str:
        return "\n\n".join([
            f"Comment {i}:\nFile: {c.file_name}\nLines: {c.line_nums}\n"
            f"Comment: {c.comment}\nCode:\n{c.chunk}"
            for i, c in enumerate(comments)
        ])


    async def _analyze_batch(self, bot_name: str, pr_number: int, formatted_comments: str) -> List[Dict]:
        def make_api_call():
            return self.model.generate_content(
                GEMINI_PROMPTS["comment_categorization"].format(
                    pr_number=pr_number,
                    bot_name=bot_name,
                    comments=formatted_comments
                ),
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )

        response = await make_api_call_with_backoff(make_api_call)
        response_text = response.text if hasattr(response, 'text') else response.parts[0].text
        
        try:
            results = json.loads(response_text)
            return results if isinstance(results, list) else [results]
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return []

    def _update_metrics_and_classifications(
        self, 
        bot_metrics: dict,
        classifications: dict,
        bot_name: str,
        pr_number: int,
        analysis_results: List[Dict],
        batch: List[ReviewComment],
        batch_start_idx: int
    ):
        bot_metrics[bot_name]['total_comments'] += len(batch)
        
        for idx, result in enumerate(analysis_results):
            category = result['category']
            comment = batch[idx]
            
            # Update metrics
            if category == 'CRITICAL_BUG':
                bot_metrics[bot_name]['critical_bug_ratio'] += 1
            elif category == 'NITPICK':
                bot_metrics[bot_name]['nitpick_ratio'] += 1
            else:
                bot_metrics[bot_name]['other_ratio'] += 1

            # Store classification
            classifications[bot_name][pr_number].append({
                'file_name': comment.file_name,
                'line_nums': comment.line_nums,
                'comment': comment.comment,
                'code_chunk': comment.chunk,
                'category': category,
                'reasoning': result.get('reasoning', 'No reasoning provided'),
                'comment_index': batch_start_idx + idx
            })

    def _finalize_metrics(self, bot_metrics: dict) -> Dict[str, Dict[str, float]]:
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
    

import asyncio
import logging
import os
from typing import List
import re
from datetime import datetime
from collections import defaultdict

from github.api import GitHubAPI
from analyzers.gemini import GeminiAnalyzer
from visualization.visualizer import ResultsVisualizer
from models import ReviewComment
import os
from dotenv import load_dotenv

# Load environment variables at the start of the script
load_dotenv()  

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_comments_from_log(comments_log_path: str) -> List[ReviewComment]:
    """Parse review comments from log file"""
    comments = []
    current_comment = None
    current_pr = None
    current_section = None
    current_content = []
    
    def save_current_comment():
        nonlocal current_comment
        if current_comment:
            if current_comment.comment:
                current_comment.comment = re.sub(r'<!--.*?-->', '', 
                    current_comment.comment, flags=re.DOTALL).strip()
            if current_comment.chunk:
                current_comment.chunk = current_comment.chunk.strip()
            comments.append(current_comment)
            current_comment = None


    def process_section_content():
        nonlocal current_content, current_section, current_comment
        if not current_comment or not current_section:
            return
        
        content = '\n'.join(current_content).strip()
        if current_section == 'comment':
            current_comment.comment = content
        elif current_section == 'code':
            current_comment.chunk = content
        
        current_content = []
        current_section = None


    with open(comments_log_path, 'r') as log_file:
        for line in log_file:
            line = line.rstrip('\n')
            
            if line.startswith('=== PR'):
                process_section_content()
                save_current_comment()
                try:
                    current_pr = int(re.search(r'PR #(\d+)', line).group(1))
                except (AttributeError, ValueError):
                    logger.warning(f"Could not parse PR number from line: {line}")
                continue

            if line.startswith('Bot:'):
                process_section_content()
                save_current_comment()
                current_comment = ReviewComment(
                    file_name='',
                    chunk='',
                    comment='',
                    line_nums='',
                    bot_name=line.split('Bot: ')[1].strip(),
                    pr_number=current_pr or 0
                )
                continue

            if current_comment:
                if line.startswith('File:'):
                    process_section_content()
                    current_comment.file_name = line.split('File: ')[1].strip()
                elif line.startswith('Lines:'):
                    process_section_content()
                    current_comment.line_nums = line.split('Lines: ')[1].strip()
                elif line.startswith('Comment:'):
                    process_section_content()
                    current_section = 'comment'
                    if len(line) > 8:
                        current_content.append(line.split('Comment: ')[1])
                elif line.startswith('Code Snippet:'):
                    process_section_content()
                    current_section = 'code'
                elif current_section:
                    current_content.append(line)

        process_section_content()
        save_current_comment()

    return [c for c in comments if c.comment.strip() and not re.match(r'^[:;][\w-]+[:;]$', c.comment.strip())]


def write_comment_to_log(file_handle, comment: ReviewComment):
    """Write a comment to the log file"""
    file_handle.write(f"Bot: {comment.bot_name}\n")
    if comment.file_name:
        file_handle.write(f"File: {comment.file_name}\n")
    if comment.line_nums:
        file_handle.write(f"Lines: {comment.line_nums}\n")
    file_handle.write(f"Comment: {comment.comment}\n")
    if comment.chunk:
        file_handle.write("Code Snippet:\n")
        file_handle.write(f"{comment.chunk}\n")
    file_handle.write("*" * 9 + "\n")


async def main():
    # Load configuration from environment
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO = os.getenv("GITHUB_REPO", "microsoft/typescript")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    if not all([GITHUB_TOKEN, GOOGLE_API_KEY]):
        raise ValueError("Missing required environment variables. Please set GITHUB_TOKEN and GOOGLE_API_KEY")
    
    # Initialize components
    github = GitHubAPI(GITHUB_TOKEN, REPO)
    analyzer = GeminiAnalyzer(GOOGLE_API_KEY)
    visualizer = ResultsVisualizer()
    
    try:
        output_dir = 'analysis_results'
        os.makedirs(output_dir, exist_ok=True)
        comments_log_path = os.path.join(output_dir, 'pr_comments.txt')
        
        # Either load existing comments or fetch new ones
        if os.path.exists(comments_log_path) and os.path.getsize(comments_log_path) > 0:
            logger.info("Reading comments from existing log file...")
            comments = parse_comments_from_log(comments_log_path)
            logger.info(f"Loaded {len(comments)} comments from log file")
        else:
            logger.info("Fetching new PR comments...")
            prs = await github.fetch_recent_prs(limit=100)
            comments = []
            
            with open(comments_log_path, 'w') as comments_log:
                for pr in prs:
                    pr_number = pr['number']
                    logger.info(f"Processing PR #{pr_number}...")
                    
                    comments_log.write(f"=== PR #{pr_number} Comments ===\n")
                    comments_log.write(f"PR Title: {pr.get('title', 'No Title')}\n")
                    comments_log.write(f"PR URL: {pr.get('html_url', 'No URL')}\n\n")
                    
                    try:
                        logger.info(f"Fetching PR {pr_number}")
                        diff = await github.fetch_pr_diff(pr_number)
                        logger.info(f"Fetching comments for PR {pr_number}")
                        bot_comments = await github.fetch_pr_comments(pr_number)
                        logger.info(f"Analyzing PR for {pr_number}")
                        gemini_comments = await analyzer.analyze_diff(diff)
                        
                        for comment in bot_comments + gemini_comments:
                            write_comment_to_log(comments_log, comment)
                            comments.append(comment)
                            
                    except Exception as e:
                        logger.error(f"Error processing PR #{pr_number}: {str(e)}")
                        comments_log.write(f"Error processing PR #{pr_number}: {str(e)}\n\n")
                        continue
        
        # Analyze comments and generate reports
        logger.info("Analyzing comment quality...")
        analysis_results = await analyzer.analyze_comment_quality_in_batch(comments)
        
        logger.info("Generating visualizations and reports...")
        
        # Create visualizations
        visualizer.create_impact_distribution_chart(
            analysis_results['metrics'],
            os.path.join(output_dir, 'comment_distribution.png')
        )
        
        visualizer.create_bot_comparison_chart(
            analysis_results['metrics'],
            os.path.join(output_dir, 'bot_comparison.png')
        )
        
        # Generate reports
        visualizer.save_detailed_report(
            analysis_results,
            os.path.join(output_dir, 'analysis_report.txt')
        )
        
        logger.info(f"""
        Analysis complete! Results saved in {output_dir}:
        1. comment_distribution.png - Visual breakdown of comment categories
        2. bot_comparison.png - Radar chart comparing bot performance
        3. analysis_report.txt - Detailed metrics and analysis
        """)
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())


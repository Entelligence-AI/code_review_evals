# %% [markdown]
# # Code Review Analyzer Demo
# 
# This notebook demonstrates how to use the Code Review Analyzer to analyze and evaluate code review comments from different AI code review bots.
# 
# ## Setup
# First, let's install the required packages and configure our environment.

# %%
# Install required packages
!pip install aiohttp google-generativeai anthropic openai pandas matplotlib seaborn python-dotenv pydantic typing-extensions

# Clone the repository (if running in Colab)
!git clone https://github.com/yourusername/CodeReviewAnalyzer.git
!cd CodeReviewAnalyzer

# %% [markdown]
# ## Configuration
# Enter your API keys below. These will be stored only for this session.

# %%
import os
from dotenv import load_dotenv

# Load from .env file if it exists
load_dotenv()

# Set your API keys here (or in .env file)
os.environ['GITHUB_TOKEN'] = os.getenv('GITHUB_TOKEN', 'your_github_token')
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY', 'your_gemini_api_key')
os.environ['ANTHROPIC_KEY'] = os.getenv('ANTHROPIC_KEY', 'your_claude_api_key') 
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your_openai_api_key')

# %% [markdown]
# ## Importing Required Modules

# %%
import asyncio
import logging
from datetime import datetime

from code_review_analyzer.github import GitHubAPI
from code_review_analyzer.analyzers import GeminiReviewAnalyzer, ClaudeReviewAnalyzer, GPT4ReviewAnalyzer
from code_review_analyzer.visualization import ResultsVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# %% [markdown]
# ## Analyzing Code Reviews
# Now let's analyze some code reviews from a GitHub repository.

# %%
async def analyze_reviews(repo_name: str, num_prs: int = 5):
    """
    Analyze code reviews from a GitHub repository
    
    Args:
        repo_name: GitHub repository in format 'owner/repo'
        num_prs: Number of most recent PRs to analyze
    """
    # Initialize components
    github = GitHubAPI(os.environ['GITHUB_TOKEN'], repo_name)
    
    # Initialize analyzers
    analyzers = {
        'gemini': GeminiReviewAnalyzer(os.environ['GOOGLE_API_KEY']),
        'claude': ClaudeReviewAnalyzer(os.environ['ANTHROPIC_KEY']),
        'gpt4': GPT4ReviewAnalyzer(os.environ['OPENAI_API_KEY'])
    }
    
    visualizer = ResultsVisualizer()
    
    try:
        # Fetch recent PRs
        logger.info(f"Fetching {num_prs} recent PRs from {repo_name}...")
        prs = await github.fetch_recent_prs(limit=num_prs)
        
        # Collect and analyze comments
        all_comments = []
        for pr in prs:
            pr_number = pr['number']
            logger.info(f"Processing PR #{pr_number}...")
            
            # Fetch PR data
            comments = await github.fetch_pr_comments(pr_number)
            diff = await github.fetch_pr_diff(pr_number)
            
            # Analyze with each bot
            for name, analyzer in analyzers.items():
                bot_comments = await analyzer.analyze_diff(diff)
                all_comments.extend(bot_comments)
                
            # Add existing bot comments
            all_comments.extend(comments)
        
        # Analyze comment quality
        logger.info("Analyzing comment quality...")
        metrics = {}
        for name, analyzer in analyzers.items():
            metrics[name] = await analyzer.analyze_comment_quality(all_comments)
        
        # Generate visualizations
        logger.info("Generating visualizations...")
        output_dir = 'analysis_results'
        os.makedirs(output_dir, exist_ok=True)
        
        visualizer.create_impact_distribution_chart(
            metrics,
            os.path.join(output_dir, 'comment_distribution.png')
        )
        
        visualizer.create_bot_comparison_chart(
            metrics,
            os.path.join(output_dir, 'bot_comparison.png')
        )
        
        visualizer.save_metrics_report(
            metrics,
            os.path.join(output_dir, 'analysis_report.txt')
        )
        
        visualizer.export_to_excel(
            metrics,
            os.path.join(output_dir, 'metrics.xlsx')
        )
        
        logger.info(f"""
        Analysis complete! Results saved in {output_dir}:
        1. comment_distribution.png - Visual breakdown of comment categories
        2. bot_comparison.png - Radar chart comparing bot performance
        3. analysis_report.txt - Detailed metrics and statistics
        4. metrics.xlsx - Excel file with all metrics
        """)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        raise

# %% [markdown]
# ## Running the Analysis
# Let's analyze a repository. You can modify the repository name and number of PRs to analyze.

# %%
# Repository to analyze
REPO_NAME = "microsoft/typescript"  # Example repository
NUM_PRS = 5  # Number of PRs to analyze

# Run the analysis
metrics = await analyze_reviews(REPO_NAME, NUM_PRS)

# Display results
from IPython.display import Image
Image('analysis_results/comment_distribution.png')

# %% [markdown]
# ## Viewing the Results
# The analysis results are saved in the `analysis_results` directory. You can also explore the metrics dictionary directly:

# %%
# Print metrics summary
for bot, data in metrics.items():
    print(f"\nBot: {bot}")
    print("-" * 20)
    for metric, value in data.items():
        if metric == 'total_comments':
            print(f"{metric}: {value}")
        else:
            print(f"{metric}: {value:.1%}")

            
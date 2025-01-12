{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Code Review Analysis with AI Models\n",
    "\n",
    "This notebook analyzes code reviews from any GitHub repository using AI models.\n",
    "\n",
    "## Setup\n",
    "First, let's install requirements and clone the repository:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "source": [
    "# Clone the repository\n",
    "!git clone https://github.com/Entelligence-AI/code_review_evals.git\n",
    "%cd code_review_evals\n",
    "\n",
    "# Install requirements\n",
    "!pip install -r requirements.txt\n",
    "!pip install nest-asyncio  # Required for running async code in notebooks"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Configuration\n",
    "Enter your API keys and repository details below:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "cellView": "form"
   },
   "source": [
    "#@title API Keys and Repository Settings\n",
    "GITHUB_TOKEN = \"\" #@param {type:\"string\"}\n",
    "GOOGLE_API_KEY = \"\" #@param {type:\"string\"}\n",
    "GITHUB_REPO = \"microsoft/typescript\" #@param {type:\"string\"}\n",
    "NUM_PRS = 5 #@param {type:\"slider\", min:1, max:100, step:1}\n",
    "\n",
    "import os\n",
    "os.environ['GITHUB_TOKEN'] = GITHUB_TOKEN\n",
    "os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY\n",
    "\n",
    "if not GITHUB_TOKEN or not GOOGLE_API_KEY:\n",
    "    raise ValueError(\"Please provide both GITHUB_TOKEN and GOOGLE_API_KEY\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Run Analysis\n",
    "Now let's analyze the repository using our code review evaluation tools:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "source": [
    "import asyncio\n",
    "import nest_asyncio\n",
    "nest_asyncio.apply()\n",
    "\n",
    "from github.api import GitHubAPI\n",
    "from analyzers.gemini import GeminiAnalyzer\n",
    "from visualization.visualizer import ResultsVisualizer\n",
    "\n",
    "async def analyze_repository():\n",
    "    # Initialize components\n",
    "    github = GitHubAPI(GITHUB_TOKEN, GITHUB_REPO)\n",
    "    analyzer = GeminiAnalyzer(GOOGLE_API_KEY)\n",
    "    visualizer = ResultsVisualizer()\n",
    "    \n",
    "    print(f\"Analyzing {GITHUB_REPO}...\")\n",
    "    \n",
    "    # Fetch and analyze PRs\n",
    "    prs = await github.fetch_recent_prs(NUM_PRS)\n",
    "    print(f\"Fetched {len(prs)} PRs\")\n",
    "    \n",
    "    comments = []\n",
    "    for pr in prs:\n",
    "        pr_number = pr['number']\n",
    "        print(f\"Processing PR #{pr_number}...\")\n",
    "        \n",
    "        try:\n",
    "            # Fetch PR data\n",
    "            pr_comments = await github.fetch_pr_comments(pr_number)\n",
    "            diff = await github.fetch_pr_diff(pr_number)\n",
    "            \n",
    "            # Analyze with Gemini\n",
    "            gemini_comments = await analyzer.analyze_diff(diff)\n",
    "            \n",
    "            comments.extend(pr_comments)\n",
    "            comments.extend(gemini_comments)\n",
    "            \n",
    "        except Exception as e:\n",
    "            print(f\"Error processing PR #{pr_number}: {str(e)}\")\n",
    "            continue\n",
    "    \n",
    "    # Analyze quality and generate visualizations\n",
    "    print(\"\\nAnalyzing comment quality...\")\n",
    "    analysis_results = await analyzer.analyze_comment_quality_in_batch(comments)\n",
    "    \n",
    "    # Create visualizations\n",
    "    print(\"\\nGenerating visualizations...\")\n",
    "    visualizer.create_impact_distribution_chart(\n",
    "        analysis_results['metrics'],\n",
    "        'comment_distribution.png'\n",
    "    )\n",
    "    \n",
    "    visualizer.create_bot_comparison_chart(\n",
    "        analysis_results['metrics'],\n",
    "        'bot_comparison.png'\n",
    "    )\n",
    "    \n",
    "    visualizer.save_detailed_report(\n",
    "        analysis_results,\n",
    "        'analysis_report.txt'\n",
    "    )\n",
    "    \n",
    "    return analysis_results\n",
    "\n",
    "# Run the analysis\n",
    "results = await analyze_repository()\n",
    "\n",
    "# Display results\n",
    "from IPython.display import Image, Markdown\n",
    "display(Markdown(\"## Comment Distribution\"))\n",
    "display(Image('comment_distribution.png'))\n",
    "display(Markdown(\"## Bot Comparison\"))\n",
    "display(Image('bot_comparison.png'))\n",
    "\n",
    "# Print summary metrics\n",
    "print(\"\\nSummary Metrics:\")\n",
    "for bot, metrics in results['metrics'].items():\n",
    "    print(f\"\\nBot: {bot}\")\n",
    "    print(f\"Total Comments: {metrics['total_comments']}\")\n",
    "    print(f\"Critical Bug Ratio: {metrics['critical_bug_ratio']:.1%}\")\n",
    "    print(f\"Nitpick Ratio: {metrics['nitpick_ratio']:.1%}\")\n",
    "    print(f\"Other Ratio: {metrics['other_ratio']:.1%}\")"
   ]
  }
 ],
 "metadata": {
  "colab": {
   "name": "Code Review Analysis",
   "provenance": []
  },
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

# Code Review Analyzer

A tool to analyze and evaluate code review comments from different AI code review bots using LLMs (Claude, GPT-4, and Gemini).  This library will pull all the comments left on a codebase by different bots, analyze them using the same evaluation logic and report back scores on effectiveness per bot.

## Features

- Fetches PR data and code review comments from GitHub repositories
- Analyzes code review comments using multiple LLM providers:
  - Google's Gemini
  - Anthropic's Claude
  - OpenAI's GPT-4
- Categorizes comments into:
  - Critical Bugs
  - Nitpicks
  - Other feedback
- Generates visual analysis and detailed reports
- Includes rate limiting and retry mechanisms
- Supports async operations for better performance

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with your API keys:

```env
GITHUB_TOKEN=your_github_token
GOOGLE_API_KEY=your_gemini_api_key
ANTHROPIC_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Usage

1. Basic usage:

```python
from code_review_analyzer import GitHubAPI, ReviewAnalyzer, ResultsVisualizer

# Initialize components
github = GitHubAPI(github_token, repo_name)
analyzer = ReviewAnalyzer(google_api_key)
visualizer = ResultsVisualizer()

# Fetch and analyze PRs
prs = await github.fetch_recent_prs(limit=100)
comments = await github.fetch_pr_comments(pr_number)
metrics = await analyzer.analyze_comment_quality(comments)

# Generate visualizations
visualizer.create_impact_distribution_chart(metrics, 'distribution.png')
visualizer.save_metrics_report(metrics, 'report.txt')
```

2. Try it in Google Colab: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/CodeReviewAnalyzer/blob/main/notebooks/analyze_code_reviews.ipynb)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


# Code Review Evaluator

A tool to analyze and evaluate code review comments from different AI code review bots using LLMs.

## Features

- Fetches and analyzes Pull Request data from GitHub repositories
- Evaluates code review comments using Google's Gemini model
- Categorizes comments into:
  - Critical Bugs
  - Nitpicks
  - Other feedback
- Generates visual analysis and detailed reports

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/Entelligence-AI/code_review_evals.git
cd code_review_evals
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

4. Run the analysis:
```bash
python main.py
```

## Environment Setup

Required environment variables in your `.env` file:
```
GITHUB_TOKEN=your_github_personal_access_token_here
GOOGLE_API_KEY=your_gemini_api_key_here
GITHUB_REPO=owner/repo  # default: microsoft/typescript
NUM_PRS=5  # number of PRs to analyze
```

To get the required API keys:
- GitHub Token: https://github.com/settings/tokens
  - Needs `repo` scope access
- Google API Key: https://makersuite.google.com/app/apikey
  - Enable Gemini API access

## Output

The tool generates several outputs in the `analysis_results` directory:
1. `comment_distribution.png` - Visual breakdown of comment categories
2. `bot_comparison.png` - Comparison of different bot performances
3. `analysis_report.txt` - Detailed metrics and analysis

## Alternative Usage: Jupyter Notebook

For interactive analysis, you can use the provided notebook:
```bash
jupyter notebook notebooks/code_review_analysis.ipynb
```

## Development

Project structure:
```
code_review_evals/
├── analyzers/        # Analysis modules for different LLMs
├── github/          # GitHub API interaction
├── utils/           # Utility functions
├── visualization/   # Visualization tools
├── models.py        # Data models
├── prompts.py       # LLM prompts
├── main.py         # Main execution script
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

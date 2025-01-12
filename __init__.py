"""Code Review Evaluator - A tool for analyzing code review comments from different AI models"""

from .github.api import GitHubAPI
from .analyzers.gemini import GeminiAnalyzer
from .visualization.visualizer import ResultsVisualizer
from .models import ReviewComment, PRDiff, CommentAnalysis, ReviewCommentResponse

__version__ = "0.1.0"
__all__ = [
    'GitHubAPI',
    'GeminiAnalyzer',
    'ResultsVisualizer',
    'ReviewComment',
    'PRDiff',
    'CommentAnalysis',
    'ReviewCommentResponse'
]

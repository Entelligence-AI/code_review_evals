from abc import ABC, abstractmethod
from typing import List, Dict
from enum import Enum
from pydantic import BaseModel

from ..github.api import ReviewComment

class ImpactLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class ReviewCommentCategory(str, Enum):
    CRITICAL_BUG = "Critical Bug"
    NITPICK = "Nitpick"
    OTHER = "Other"

class CommentAnalysis(BaseModel):
    comment: str
    category: ReviewCommentCategory
    impact: ImpactLevel
    reasoning: str
    file_name: str | None = None
    line_numbers: str | None = None

class ReviewCommentResponse(BaseModel):
    bot: str
    comments: List[CommentAnalysis]

class BaseReviewAnalyzer(ABC):
    """Base class for review analyzers"""
    
    @abstractmethod
    async def analyze_diff(self, diff: 'PRDiff') -> List[ReviewComment]:
        """Analyze a PR diff to find potential issues"""
        pass

    @abstractmethod
    async def analyze_comment_quality(self, comments: List[ReviewComment]) -> Dict[str, Dict[str, float]]:
        """Analyze the quality of bot comments"""
        pass
    
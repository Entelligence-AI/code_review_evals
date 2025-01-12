from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

@dataclass
class ReviewComment:
    file_name: str
    chunk: str
    comment: str
    line_nums: str
    bot_name: str
    pr_number: int
    category: Optional[str] = None

@dataclass
class PRDiff:
    pr_number: int
    diff_content: str
    files_changed: List[str]

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
    file_name: Optional[str] = None
    line_numbers: Optional[str] = None

class ReviewCommentResponse(BaseModel):
    bot: str
    comments: List[CommentAnalysis]

    
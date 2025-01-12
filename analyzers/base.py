from abc import ABC, abstractmethod
from typing import List, Dict
from models import ReviewComment, PRDiff

class BaseAnalyzer(ABC):
    """Base class for all review analyzers"""
    
    @abstractmethod
    async def analyze_diff(self, diff: PRDiff) -> List[ReviewComment]:
        """Analyze a PR diff to find potential issues"""
        pass

    @abstractmethod
    async def analyze_comment_quality(self, comments: List[ReviewComment]) -> Dict[str, Dict[str, float]]:
        """Analyze the quality of bot comments"""
        pass

    @abstractmethod
    async def analyze_comment_quality_in_batch(self, comments: List[ReviewComment]) -> Dict[str, Dict]:
        """Analyze comments in batches for more detailed analysis"""
        pass


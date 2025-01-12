import aiohttp
import logging
from typing import List
from models import ReviewComment, PRDiff

logger = logging.getLogger(__name__)

class GitHubAPI:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.diff_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3.diff"
        }

    async def fetch_recent_prs(self, limit: int = 10) -> List[dict]:
        """Fetch recent PRs from the repository"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            url = f"https://api.github.com/repos/{self.repo}/pulls"
            prs = []
            page = 1

            while len(prs) < limit:
                params = {
                    "state": "all",
                    "per_page": min(10, limit - len(prs)),
                    "page": page,
                    "sort": "created",
                    "direction": "desc"
                }

                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch PRs: {await response.text()}")

                    batch = await response.json()
                    if not batch:
                        break

                    prs.extend(batch)
                    page += 1

            return prs[:limit]


    async def fetch_pr_diff(self, pr_number: int) -> PRDiff:
        """Fetch the diff content for a PR"""
        logger.info(f"Fetching PR {pr_number}")
        async with aiohttp.ClientSession(headers=self.diff_headers) as session:
            url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}"

            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch PR diff: {await response.text()}")

                diff_content = await response.text()
                files_changed = []
                
                # More robust file path extraction
                for line in diff_content.split("\n"):
                    if line.startswith("+++ b/"):
                        try:
                            # Remove the "+++ b/" prefix to get the file path
                            file_path = line[6:]  # "+++ b/" is 6 characters
                            if file_path and file_path != '/dev/null':  # Skip deleted files
                                files_changed.append(file_path)
                        except Exception as e:
                            logger.warning(f"Could not parse file path from line: {line}")
                            continue

                logger.debug(f"Found {len(files_changed)} changed files in PR {pr_number}")
                return PRDiff(
                    pr_number=pr_number,
                    diff_content=diff_content,
                    files_changed=files_changed
                )
            

    async def fetch_pr_comments(self, pr_number: int) -> List[ReviewComment]:
        """Fetch review comments for a PR"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}/comments"

            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch PR comments: {await response.text()}")

                comments = await response.json()
                return [
                    ReviewComment(
                        file_name=comment['path'],
                        chunk=comment.get('diff_hunk', ''),
                        comment=comment['body'],
                        line_nums=f"{comment.get('line', '')}-{comment.get('original_line', '')}",
                        bot_name=comment['user']['login'],
                        pr_number=pr_number
                    )
                    for comment in comments
                    if 'bot' in comment['user']['type'].lower()
                ]
            

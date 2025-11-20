"""GitHub Repository Summarizer package."""

# Re-export core components at the package level for convenient imports.
from .repo_scraper import get_github_repo_info
from .db import Database
from .llm import summarize_readme, find_similar_repos

__version__ = "0.1.0"

__all__ = [
    "get_github_repo_info",
    "Database",
    "summarize_readme",
    "find_similar_repos",
]
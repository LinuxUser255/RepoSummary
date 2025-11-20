# `src/__init__.py` in RepoSummary

## What this file does

The `src/__init__.py` file turns the `src` directory into a proper Python package and defines the public interface of the **GitHub Repository Summarizer** project.

```python
"""GitHub Repository Summarizer package."""
# __init__.py now lazy loads modules only when src is imported.

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
```

In plain terms, this file:

- Marks `src/` as a package so it can be imported as `src`.
- Re-exports selected functions and classes from internal modules (`repo_scraper`, `db`, and `llm`).
- Defines a `__version__` string for the package.
- Uses `__all__` to specify the symbols that are considered part of the package’s public API.

## Use case: why structure it this way

In a Python package, `__init__.py` is commonly used to provide a **clean, unified import surface**. Instead of forcing callers to know the internal module layout, you can expose the most important pieces at the package level.

Here, the project exposes exactly the core operations needed for the main workflow:

- `get_github_repo_info` — scrape repository metadata and README content.
- `Database` — handle persistence for repositories, summaries, and related data.
- `summarize_readme` — call the LLM to summarize the README (or repository content).
- `find_similar_repos` — use embeddings and the database to find repositories similar to a given summary.

This design lets other parts of the code (or any external user of the package) write imports like:

```python
from src import Database, get_github_repo_info, summarize_readme, find_similar_repos
```

without needing to know that `Database` lives in `db.py`, the scraper in `repo_scraper.py`, and the LLM logic in `llm.py`.

## How it is used in this codebase

The primary use of `src/__init__.py` in this project is in `main.py`, which orchestrates the end‑to‑end flow of the GitHub Repository Summarizer CLI:

```python
from src import Database, get_github_repo_info, summarize_readme, find_similar_repos
```

`main.py` then uses these imports to:

1. **Initialize the database** via `Database()`.
2. **Scrape a GitHub repo** using `get_github_repo_info(owner, repo_name)`.
3. **Generate a summary** of the repo’s README via `summarize_readme(readme, language)`.
4. **Find similar repositories** with `find_similar_repos(summary, language)`.

Because `__init__.py` exports all of these symbols at the package level, `main.py` can remain concise and readable, importing everything it needs from a single place (`src`) instead of juggling multiple module‑level imports like:

```python
from src.repo_scraper import get_github_repo_info
from src.db import Database
from src.llm import summarize_readme, find_similar_repos
```

In summary, `src/__init__.py` acts as the **public gateway** to the project’s core capabilities, providing a stable, convenient API surface for the rest of the application (and any potential external users) while hiding the internal module structure.
#!/usr/bin/env python3

"""
GitHub Repo Summarizer
======================

A lightweight Python web scraper that retrieves the README of a public GitHub
repository and uses the **Grok API (xAI)** to generate a concise, bullet-point
summary of the project.

Features
--------
- Scrape any public GitHub repository's README via HTTP
- Summarize content using Grok (``grok-4`` or ``grok-3``) through the xAI API
- Return **only** a clean, structured bullet-point description:
    * Project purpose
    * Core technologies / programming languages
    * Key features or modules
    * Target audience or use-case
- Securely manage secrets via ``.env`` (never hard-coded)
- Minimal dependencies for fast setup and execution

Requirements
------------
- Python 3.8 or higher
- Packages:
    * ``requests``
    * ``beautifulsoup4``
    * ``python-dotenv``
    * ``openai>=1.0.0`` (used for xAI API compatibility)


See the README.md for setup instructions and usage examples.
-----

Notes
-----
- The API endpoint ``https://api.x.ai/v1`` is fully compatible with the OpenAI SDK.
- Use ``grok-4`` for maximum reasoning power; switch to ``grok-3-mini`` for lower cost/speed.
- Monitor token usage and billing at the `xAI Console <https://console.x.ai>`_.

License
-------
GPLv3
"""
# main.py ties everything together following the flowchart:
# 1. Enter GitHub Repo -> 2. Scrape from GitHub -> 3. Save to DB
# 4. AI Analysis -> 5. Find Similar Repos -> 6. Show Report

from src import Database, get_github_repo_info, summarize_readme, find_similar_repos


def main():
    """
    Main workflow for GitHub Repo Summarizer.
    Follows the flowchart: Scrape -> Save -> Analyze -> Find Similar -> Report
    """
    # Initialize database
    db = Database()

    # Step 1: Get repo input
    print("=" * 60)
    print("GitHub Repository Summarizer")
    print("=" * 60)
    repo_input = input("\nEnter GitHub repository (owner/repo): ").strip()

    # Parse input
    if '/' not in repo_input:
        print("Error: Please use format 'owner/repo' (e.g., 'tiangolo/fastapi')")
        return

    owner, repo_name = repo_input.split('/', 1)

    # Step 2: Scrape from GitHub
    print(f"\n[1/5] Scraping {owner}/{repo_name} from GitHub...")
    try:
        repo_info = get_github_repo_info(owner, repo_name)
        language = repo_info['language']
        readme = repo_info['readme']
        print(f"  ✓ Language: {language or 'Not specified'}")
        print(f"  ✓ README: {len(readme)} characters")
    except Exception as e:
        print(f"Error scraping repository: {e}")
        return

    # Step 3: AI Analysis
    print(f"\n[2/5] Analyzing with Grok AI...")
    summary = summarize_readme(readme, language) # function called from llm.py
    if not summary:
        print("Error: Failed to generate summary")
        return
    print("  ✓ Summary generated")

    # Step 4: Save to DB
    print(f"\n[3/5] Saving to database...")
    db.save_repo(owner, repo_name, language, readme, summary)
    print("  ✓ Saved")

    # Step 5: Find Similar Repos
    print(f"\n[4/5] Finding similar repositories...")
    similar_repos = find_similar_repos(summary, language)
    if similar_repos:
        print(f"  ✓ Found {len(similar_repos)} similar repos")
    else:
        print("  ! No similar repos found")

    # Step 6: Show Report
    print(f"\n[5/5] " + "=" * 60)
    print("REPORT")
    print("=" * 60)
    print(f"\nRepository: {owner}/{repo_name}")
    print(f"Language: {language or 'Not specified'}")
    print(f"\nSummary:")
    print(summary)

    if similar_repos:
        print(f"\n\nSimilar Repositories:")
        for i, repo in enumerate(similar_repos, 1):
            print(f"  {i}. {repo}")

    print("\n" + "=" * 60)
    print("\nDone! Data saved to database.")


if __name__ == "__main__":
    main()




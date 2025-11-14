# This file is primarily responsible for scraping the GitHub repository README
# This is where the oxylabs webscraper API logic will go in the future
# for my purposes, much of the current main.py code go here
# this file is doing the searching and scraping
# gathering related repos will be in here too
import os
# need to import the Grok API
import json
import os
import time
from unicodedata import category

import requests
from certifi import contents
from dotenv import load_dotenv
# import the BeautifulSoup library for parsing HTML
from bs4 import BeautifulSoup
import requests
import base64

load_dotenv()

def get_github_repo_info(owner: str, repo: str, ref: str = None) -> dict:
    """
    Fetch repo metadata (incl. primary language) and README content.

    Args:
        owner (str): Repo owner.
        repo (str): Repo name.
        ref (str): Branch (optional, uses repo's default branch if None).

    Returns:
        dict: {'language': str|null, 'readme': str}.

    Raises:
        requests.RequestException: On API errors.
    """
    # Step 1: Get repo info (for language and default branch)
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Repo-Summarizer/1.0"
    }
    repo_response = requests.get(repo_url, headers=headers)
    repo_response.raise_for_status()
    repo_data = repo_response.json()
    language = repo_data.get("language")  # extracts the language field
    
    # Use the repo's default branch if ref not specified
    if ref is None:
        ref = repo_data.get("default_branch", "main")

    # Step 2: Try the dedicated README endpoint first
    readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme?ref={ref}"
    readme_content = None
    try:
        readme_response = requests.get(readme_url, headers=headers)
        if readme_response.status_code == 200:
            rd = readme_response.json()
            if isinstance(rd, dict) and rd.get("encoding") == "base64" and "content" in rd:
                readme_content = base64.b64decode(rd["content"]).decode("utf-8", errors="replace")
        elif readme_response.status_code == 404:
            # Fall through to directory listing
            pass
        else:
            readme_response.raise_for_status()
    except requests.RequestException:
        # Fall back to contents listing below
        pass

    # Step 3: Fallback — list repo contents and locate a README-like file
    if not readme_content:
        list_url = f"https://api.github.com/repos/{owner}/{repo}/contents?ref={ref}"
        content_response = requests.get(list_url, headers=headers)
        content_response.raise_for_status()
        content_data = content_response.json()

        readme_candidates = {"readme", "readme.md", "readme.rst", "readme.txt"}
        readme_item = None
        if isinstance(content_data, list):
            for item in content_data:
                name = item.get("name", "").lower()
                if name in readme_candidates:
                    readme_item = item
                    break

        if readme_item:
            # Prefer raw download if available (simpler than base64 decode)
            download_url = readme_item.get("download_url")
            if download_url:
                resp = requests.get(download_url, headers={"User-Agent": headers["User-Agent"]})
                resp.raise_for_status()
                readme_content = resp.text
            else:
                # Fallback: fetch file content JSON and decode base64
                file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{readme_item.get('path')}?ref={ref}"
                file_resp = requests.get(file_url, headers=headers)
                file_resp.raise_for_status()
                file_json = file_resp.json()
                if isinstance(file_json, dict) and file_json.get("encoding") == "base64" and "content" in file_json:
                    readme_content = base64.b64decode(file_json["content"]).decode("utf-8", errors="replace")

    if not readme_content:
        readme_content = "No README found."

    return {"language": language, "readme": readme_content}

#info = get_github_repo_info("tiangolo", "fastapi")
#    print(f"Language: {info['language']}")  # Output: Language: Python
#    print(f"README preview: {info['readme'][:200]}...")



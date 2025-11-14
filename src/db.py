from tinydb import TinyDB, Query
from datetime import datetime
import os

class Database:
    def __init__(self, db_path="data.json"):
        dirname = os.path.dirname(db_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        self.db = TinyDB(db_path)
        self.repos = self.db.table("repositories")

    def save_repo(self, owner, repo_name, language, readme, summary):
        """Save repo info and summary to database"""
        repo_key = f"{owner}/{repo_name}"
        self.repos.insert({
            'repo': repo_key,
            'owner': owner,
            'name': repo_name,
            'language': language,
            'readme': readme[:500],  # Store first 500 chars
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
        print(f"Saved {repo_key} to database")

    def get_repo(self, owner, repo_name):
        """Get repo from database"""
        repo_key = f"{owner}/{repo_name}"
        Repo = Query()
        return self.repos.get(Repo.repo == repo_key)

    def search_repos(self, search_term):
        """Search repos by content"""
        Repo = Query()
        results = self.repos.search(Repo.readme.search(search_term, flags=0))
        for result in results:
            print(f"Found: {result['repo']}")
            print(f"Language: {result.get('language', 'N/A')}")
            print(f"Summary: {result.get('summary', 'N/A')[:100]}...")
            print("-" * 50)
        return results


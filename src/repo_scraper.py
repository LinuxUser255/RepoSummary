from dotenv import load_dotenv
import requests
import base64
import json

load_dotenv()

def fetch_codebase_structure(owner: str, repo: str, ref: str, headers: dict) -> str:
    """
    Fetch repository structure and sample code files when no README exists.
    
    Args:
        owner (str): Repository owner
        repo (str): Repository name  
        ref (str): Branch reference
        headers (dict): API headers
        
    Returns:
        str: Formatted description of repo structure and contents
    """
    try:
        # Get repository tree structure
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
        tree_response = requests.get(tree_url, headers=headers)
        
        if tree_response.status_code != 200:
            # Fallback to contents API for root directory
            contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents?ref={ref}"
            contents_response = requests.get(contents_url, headers=headers)
            
            if contents_response.status_code != 200:
                return "No README found. Unable to fetch repository structure."
                
            contents = contents_response.json()
            return format_contents_as_structure(owner, repo, ref, contents, headers)
        
        tree_data = tree_response.json()
        tree = tree_data.get('tree', [])
        
        # Analyze repository structure
        result = f"# Repository: {owner}/{repo}\n\n"
        result += "## No README found - Analyzing codebase structure\n\n"
        
        # Categorize files
        config_files = []
        source_files = []
        directories = set()
        
        for item in tree:
            path = item['path']
            item_type = item['type']
            
            if item_type == 'tree':
                directories.add(path)
            elif item_type == 'blob':
                # Identify config files
                if path in ['package.json', 'Cargo.toml', 'pyproject.toml', 'requirements.txt', 
                           'setup.py', 'Makefile', 'CMakeLists.txt', '.gitignore', 'Dockerfile',
                           'docker-compose.yml', 'composer.json', 'pom.xml', 'build.gradle']:
                    config_files.append(path)
                # Identify main source files
                elif any(path.endswith(ext) for ext in ['.py', '.js', '.ts', '.go', '.rs', '.c', '.cpp', 
                                                        '.java', '.rb', '.php', '.swift', '.kt']):
                    # Prioritize main/index files
                    if any(name in path.lower() for name in ['main', 'index', 'app', 'server']):
                        source_files.insert(0, path)
                    elif len(source_files) < 10:  # Limit to prevent too much data
                        source_files.append(path)
        
        # Add directory structure
        result += "### Directory Structure:\n"
        top_dirs = [d for d in directories if '/' not in d]
        for dir_name in sorted(top_dirs)[:10]:  # Show top 10 directories
            result += f"- {dir_name}/\n"
            # Show subdirectories (one level)
            subdirs = [d for d in directories if d.startswith(dir_name + '/') and d.count('/') == 1]
            for subdir in sorted(subdirs)[:5]:
                result += f"  - {subdir.split('/')[-1]}/\n"
        
        # Fetch and include config files content
        if config_files:
            result += "\n### Configuration Files Found:\n"
            for config_file in config_files[:5]:  # Limit to 5 config files
                result += f"\n**{config_file}:**\n"
                content = fetch_file_content(owner, repo, config_file, ref, headers)
                if content:
                    # Truncate large config files
                    if len(content) > 500:
                        content = content[:500] + "\n... (truncated)"
                    result += f"```\n{content}\n```\n"
        
        # Fetch sample source files
        if source_files:
            result += "\n### Key Source Files:\n"
            for source_file in source_files[:3]:  # Analyze top 3 source files
                result += f"\n**{source_file}:**\n"
                content = fetch_file_content(owner, repo, source_file, ref, headers)
                if content:
                    # Show first 50 lines or 1000 chars of code
                    lines = content.split('\n')[:50]
                    preview = '\n'.join(lines)
                    if len(preview) > 1000:
                        preview = preview[:1000] + "\n... (truncated)"
                    result += f"```\n{preview}\n```\n"
        
        return result
        
    except Exception as e:
        return f"No README found. Error analyzing repository structure: {str(e)}"

def fetch_file_content(owner: str, repo: str, path: str, ref: str, headers: dict) -> str:
    """
    Fetch content of a specific file from the repository.
    
    Args:
        owner (str): Repository owner
        repo (str): Repository name
        path (str): File path
        ref (str): Branch reference
        headers (dict): API headers
        
    Returns:
        str: File content or None if failed
    """
    try:
        file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
        response = requests.get(file_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('encoding') == 'base64' and 'content' in data:
                return base64.b64decode(data['content']).decode('utf-8', errors='replace')
            elif data.get('download_url'):
                # Try direct download
                dl_response = requests.get(data['download_url'], headers={'User-Agent': headers['User-Agent']})
                if dl_response.status_code == 200:
                    return dl_response.text
    except Exception:
        pass
    return None

def format_contents_as_structure(owner: str, repo: str, ref: str, contents: list, headers: dict) -> str:
    """
    Format repository contents when tree API is not available.
    
    Args:
        owner (str): Repository owner
        repo (str): Repository name
        ref (str): Branch reference
        contents (list): List of content items from GitHub API
        headers (dict): API headers
        
    Returns:
        str: Formatted repository structure
    """
    result = f"# Repository: {owner}/{repo}\n\n"
    result += "## No README found - Analyzing repository contents\n\n"
    result += "### Root Directory Files:\n"
    
    for item in contents:
        if item['type'] == 'dir':
            result += f"- {item['name']}/ (directory)\n"
        else:
            result += f"- {item['name']}\n"
            # Fetch important config files
            if item['name'] in ['package.json', 'Cargo.toml', 'pyproject.toml', 'requirements.txt']:
                content = fetch_file_content(owner, repo, item['path'], ref, headers)
                if content and len(content) < 500:
                    result += f"  Content:\n```\n{content}\n```\n"
    
    return result

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

    # Step 4: If no README, fetch codebase structure and files
    if not readme_content or readme_content == "No README found.":
        readme_content = fetch_codebase_structure(owner, repo, ref, headers)

    return {"language": language, "readme": readme_content}

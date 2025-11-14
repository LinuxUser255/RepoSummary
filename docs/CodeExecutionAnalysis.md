# Code Execution Analysis (Order)

## **1. Script Execution Begins**
```bash
python3 main.py
```
Python interpreter starts executing `main.py` from line 1

---

## **2. Module Loading Phase (Lines 1-52)**

### **2a. Docstring parsed** (lines 3-45)
- Module docstring loaded into memory (not executed)

### **2b. Import statements execute** (lines 50-52)

#### **Import 1: `from src.repo_scraper import get_github_repo_info`**
   - Python enters `src/repo_scraper.py`
   - Executes all module-level code:
     - Line 6-19: Import statements (`os`, `json`, `requests`, `BeautifulSoup`, `base64`, etc.)
     - Line 21: `load_dotenv()` executes → reads `.env` file into environment
     - Line 23-63: Function `get_github_repo_info()` **defined** (not executed yet)
   - Returns to `main.py` with function reference

#### **Import 2: `from src.db import Database`**
   - Python enters `src/db.py`
   - Executes all module-level code:
     - Line 1-3: Import statements (`TinyDB`, `Query`, `datetime`, `os`)
     - Line 5-42: Class `Database` **defined** (not instantiated yet)
   - Returns to `main.py` with class reference

#### **Import 3: `from src.llm import summarize_readme, find_similar_repos`**
   - Python enters `src/llm.py`
   - Executes all module-level code:
     - Line 1-3: Import statements (`os`, `load_dotenv`, `OpenAI`)
     - Line 10: `load_dotenv()` executes again (idempotent, safe)
     - Line 13-60: Function `summarize_readme()` **defined** (not executed)
     - Line 63-104: Function `find_similar_repos()` **defined** (not executed)
   - Returns to `main.py` with function references

---

## **3. Function Definition** (lines 55-124)
- Line 55-124: Function `main()` is **defined** (not executed yet)

---

## **4. Name Guard Check** (line 127)
```python
if __name__ == "__main__":
```
- Python checks: `__name__ == "__main__"` → **True** (script run directly, not imported)
- Enters the conditional block

---

## **5. Main Function Call** (line 128)
```python
main()
```
**Execution enters `main()` function...**

---

## **6. Inside `main()` - Sequential Execution**

### **Step 6a: Database Initialization** (line 61)
```python
db = Database()
```
- Calls `Database.__init__()` in `src/db.py`
  - Line 7-9: Checks if directory exists (empty string, so skips)
  - Line 10: `self.db = TinyDB(db_path)` → Creates/opens `data.json` file
  - Line 11: `self.repos = self.db.table("repositories")` → Gets/creates "repositories" table
- Returns `Database` instance to `db` variable

---

### **Step 6b: User Input** (lines 64-67)
```python
print("=" * 60)
print("GitHub Repository Summarizer")
print("=" * 60)
repo_input = input("\nEnter GitHub repository (owner/repo): ").strip()
```
- Prints header
- **BLOCKS** waiting for user input
- User types (e.g., `"tiangolo/fastapi"`)
- Stores stripped input in `repo_input`

---

### **Step 6c: Input Validation** (lines 70-74)
```python
if '/' not in repo_input:
    print("Error: Please use format 'owner/repo'...")
    return
owner, repo_name = repo_input.split('/', 1)
```
- Checks for `/` character
- If missing → prints error and **exits** `main()` early
- If valid → splits into `owner` and `repo_name` variables

---

### **Step 6d: GitHub Scraping** (lines 77-86)
```python
print(f"\n[1/5] Scraping {owner}/{repo_name} from GitHub...")
try:
    repo_info = get_github_repo_info(owner, repo_name)
```
- Prints status message
- **Calls** `get_github_repo_info()` in `src/repo_scraper.py`:
  
  #### Inside `get_github_repo_info()`:
  - Line 39: Builds GitHub API URL
  - Line 40-43: Creates headers dict
  - Line 44: **HTTP GET request** to `https://api.github.com/repos/{owner}/{repo}`
  - Line 45: Raises exception if status code ≠ 200
  - Line 46: Parses JSON response
  - Line 47: Extracts `language` field
  - Line 50: Builds contents URL
  - Line 51: **HTTP GET request** for repository contents
  - Line 52: Raises exception if failed
  - Line 53: Parses JSON
  - Line 54-61: Loops through files, finds `readme.md`, decodes base64 content
  - Line 63: **Returns** dict `{"language": "Python", "readme": "# FastAPI..."}`

- Back in `main()`:
  - Line 80-81: Extracts `language` and `readme` from returned dict
  - Line 82-83: Prints success messages with checkmarks
  - If exception occurs → line 85-86: prints error and **exits** `main()`

---

### **Step 6e: AI Analysis** (lines 89-94)
```python
print(f"\n[2/5] Analyzing with Grok AI...")
summary = summarize_readme(readme, language)
```
- Prints status
- **Calls** `summarize_readme()` in `src/llm.py`:

  #### Inside `summarize_readme()`:
  - Line 24-27: Creates `OpenAI` client with Grok API credentials
  - Line 30-39: Builds system prompt string
  - Line 42: Builds user message (first 4000 chars of README)
  - Line 44-45: Prepends language info if available
  - Line 48-56: **HTTP POST request** to `https://api.x.ai/v1/chat/completions`
    - Sends system + user messages
    - Grok processes the README
    - **BLOCKS** waiting for API response (could take 2-10 seconds)
  - Line 57: Extracts and strips response text
  - **Returns** bullet-point summary string

- Back in `main()`:
  - Line 91-93: If `None` returned → prints error and **exits**
  - Line 94: Prints success message

---

### **Step 6f: Database Save** (lines 97-99)
```python
print(f"\n[3/5] Saving to database...")
db.save_repo(owner, repo_name, language, readme, summary)
```
- Prints status
- **Calls** `db.save_repo()`:
  
  #### Inside `Database.save_repo()`:
  - Line 15: Creates repo key string `"tiangolo/fastapi"`
  - Line 16-24: Inserts dict into TinyDB table
  - **Writes** to `data.json` file on disk
  - Line 25: Prints confirmation

- Back in `main()`:
  - Line 99: Prints checkmark

---

### **Step 6g: Find Similar Repos** (lines 102-107)
```python
print(f"\n[4/5] Finding similar repositories...")
similar_repos = find_similar_repos(summary, language)
```
- Prints status
- **Calls** `find_similar_repos()` in `src/llm.py`:

  #### Inside `find_similar_repos()`:
  - Line 74-77: Creates `OpenAI` client
  - Line 79-85: Builds prompt asking for similar repos
  - Line 88-96: **HTTP POST request** to Grok API
    - **BLOCKS** waiting for response
  - Line 99: Parses response, splits by newlines
  - Line 100: Filters lines containing `/`, limits to 5
  - **Returns** list like `["encode/httpx", "psf/requests", ...]`

- Back in `main()`:
  - Line 104-107: Prints count or warning

---

### **Step 6h: Show Report** (lines 110-124)
```python
print(f"\n[5/5] " + "=" * 60)
print("REPORT")
...
```
- Line 110-116: Prints report header and summary
- Line 118-121: If similar repos exist → loops and prints each
- Line 123-124: Prints footer and completion message

---

## **7. Function Return** 
- `main()` reaches end → returns `None`

---

## **8. Script Exit**
- No more code after line 128
- Python interpreter exits with status code `0` (success)

---

## **Summary Flow:**
```
Start → Imports (load modules) → Define main() → Name guard (✓) 
→ Call main() → Init DB → Get user input → Scrape GitHub (HTTP) 
→ Call Grok AI (HTTP) → Save to TinyDB → Find similar repos (HTTP) 
→ Print report → Return from main() → Exit
```

import os
from dotenv import load_dotenv
from openai import OpenAI

"""
Grok API integration for analyzing GitHub repositories.
Uses xAI's Grok model via OpenAI-compatible API.
"""

load_dotenv()


def summarize_readme(readme_content: str, language: str = None) -> str:
    """
    Summarize GitHub README using Grok API.

    Args:
        readme_content (str): The README content to summarize.
        language (str): Primary programming language of the repo.

    Returns:
        str: Bullet-point summary of the repository.
    """
    client = OpenAI(     # Creates an OpenAI client with Grok API key.
        api_key=os.getenv("GROK_API_KEY"),
        base_url="https://api.x.ai/v1"
    )

    # Prepare the system prompt
    system_prompt = (
        "You are a concise GitHub repository summarizer. "
        "Return ONLY a bullet-point list (Markdown format using '- ') that describes:\n"
        "• The main purpose of the project\n"
        "• Core technologies and programming languages used\n"
        "• Key features or modules\n"
        "• Target audience or use-case\n\n"
        "Do NOT include installation steps, code examples, or any other text. "
        "Keep it concise and factual."
    )

    # Prepare user message
    user_message = f"Summarize this GitHub repository in bullet points:\n\n{readme_content[:4000]}"

    if language:
        user_message = f"Primary Language: {language}\n\n{user_message}"

    try:
        response = client.chat.completions.create(
            model="grok-code-fast-1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling Grok API: {e}")
        return None


def find_similar_repos(readme_summary: str, language: str = None) -> list:
    """
    Ask Grok to suggest similar GitHub repositories based on summary.

    Args:
        readme_summary (str): The summarized README.
        language (str): Primary programming language.

    Returns:
        list: List of similar repo suggestions (owner/repo format).
    """
    client = OpenAI(
        api_key=os.getenv("GROK_API_KEY"),
        base_url="https://api.x.ai/v1"
    )

    prompt = (
        f"Based on this repository summary:\n{readme_summary}\n\n"
        f"Language: {language or 'Unknown'}\n\n"
        "Suggest 5 similar popular GitHub repositories. "
        "Return ONLY the repository names in 'owner/repo' format, one per line. "
        "No descriptions, no numbers, just the repo paths."
    )

    try: # send a POST request to Grok API
        response = client.chat.completions.create(
            model="grok-code-fast-1",
            messages=[
                {"role": "system", "content": "You are a GitHub repository expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200
        )

        # Parse the response to extract repo names
        content = response.choices[0].message.content.strip()
        repos = [line.strip() for line in content.split('\n') if '/' in line]
        return repos[:5]  # Return max 5
    except Exception as e:
        print(f"Error finding similar repos: {e}")
        return []



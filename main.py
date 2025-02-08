import os
import re
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from html import unescape

# Load environment variables
load_dotenv()

SNAC_HOST = os.getenv("SNAC_HOST")
API_TOKEN = os.getenv("API_TOKEN")

console = Console()

# Ensure credentials exist
if not SNAC_HOST or not API_TOKEN:
    console.print("[red]Error: Missing SNAC_HOST or API_TOKEN in .env file.[/red]")
    exit(1)

def post_status(content):
    """Post a new status to SNAC."""
    url = f"{SNAC_HOST}/api/v1/statuses"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    data = {"status": content}

    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        console.print("[green]Post successful![/green]")
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error posting status: {e}[/red]")

def fetch_posts():
    """Fetch recent posts from the SNAC timeline."""
    # this end point fetches all the post of users
    # url = f"{SNAC_HOST}/api/v1/timelines/public"

    #this is for posts from the people a user follows

    url = f"{SNAC_HOST}/api/v1/timelines/home"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    try:
        console.print("[yellow]Fetching posts...[/yellow]")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        posts = response.json()
        
        if not posts:
            console.print("[red]No posts found.[/red]")
        return posts

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error fetching posts: {e}[/red]")
        return []

def format_post(post):
    """Extract relevant fields and clean up content."""
    account = post.get("account", {})
    display_name = account.get("display_name", account.get("acct", "Unknown user"))
    created_at = post.get("created_at", "Unknown time")
    raw_content = post.get("content", "")

    # Remove HTML tags from content
    clean_content = unescape(re.sub(r"<.*?>", "", raw_content)).strip()

    if not clean_content:
        clean_content = "(No text content)"

    return f"**@{display_name}**\n\n{clean_content}\n\n*Posted at: {created_at}*\n"

def display_posts():
    """Fetch and display posts in a formatted way."""
    posts = fetch_posts()
    
    if not posts:
        return

    for post in posts:
        formatted_post = format_post(post)
        console.print(Markdown(formatted_post))
        console.print("-" * 40)

# Run it
display_posts()


import re
import os
import httpx
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Header, Footer, Static
from textual.widgets import RichLog
from rich.markdown import Markdown
from html import unescape
from typing import ClassVar

# Load environment variables
load_dotenv()
SNAC_HOST = os.getenv("SNAC_HOST")
API_TOKEN = os.getenv("API_TOKEN")

class SnacClient(App):
    # Define TITLE as a class variable
    TITLE: ClassVar[str] = "welcome to linuxusers.in"
    CSS_PATH: ClassVar[str] = "snac.tcss"

   

    def compose(self) -> ComposeResult:
        yield Static(self.TITLE, id="title")
        yield Header()
        self.content = ScrollableContainer()
        yield self.content
        yield Footer()

    async def on_mount(self) -> None:
        await self.fetch_timeline()

    async def fetch_timeline(self):
        url = f"{SNAC_HOST}/api/v1/timelines/home"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                posts = response.json()
                for post in posts:
                    username = f"[bold green]@[/][bright_green]{post['account']['display_name']}[/bright_green]"
                    raw_content = post['content']
                    content = unescape(re.sub(r"<.*?>", "", raw_content)).strip()
                    # Wrap the post in a box with hackeristic formatting
                    post_widget = Static(
                        f"{username}\n\n[green]{content}[/green]",
                        classes="hacker-box"
                    )
                    self.content.mount(post_widget)
        except httpx.HTTPError as e:
            self.content.mount(Static(f"[red]ERROR: {e}[/red]", classes="error"))



#     async def fetch_timeline(self):
#         url = f"{SNAC_HOST}/api/v1/timelines/home"
#         headers = {"Authorization": f"Bearer {API_TOKEN}"}
#         try:
#             async with httpx.AsyncClient(timeout=20) as client:
#                 response = await client.get(url, headers=headers)
#                 response.raise_for_status()
#                 posts = response.json()
#                 for post in posts:
#                     username = f"[bold cyan]@{post['account']['display_name']}[/bold cyan]"
#                     raw_content = post['content']
#                     content = unescape(re.sub(r"<.*?>", "", raw_content)).strip()
#                 # Wrap the post in a box with custom formatting
#                     post_widget = Static(
#                     f"{username}\n\n[white]{content}[/white]",
#                     classes="post-box"
#                     )
#                     self.content.mount(post_widget)
#         except httpx.HTTPError as e:
#             self.content.mount(Static(f"Error fetching posts: {e}", classes="error"))



# this officially works. if things fail and i dont know i can restart from here
#     async def fetch_timeline(self):
#         url = f"{SNAC_HOST}/api/v1/timelines/home"        
#         headers = {"Authorization": f"Bearer {API_TOKEN}"}
#         try:
#             async with httpx.AsyncClient(timeout=20) as client:
#                 response = await client.get(url, headers=headers)
#                 response.raise_for_status()
#                 posts = response.json()
#                 for post in posts:
#                     username = f"[bold]{post['account']['display_name']}[/bold]"
#                     raw_content = post['content']
#                     content = unescape(re.sub(r"<.*?>", "", raw_content)).strip()
#                     self.content.mount(Static(f"{username}\n{content}", classes="post"))
#         except httpx.HTTPError as e:
#             self.content.mount(Static(f"Error fetching posts: {e}", classes="error"))

if __name__ == "__main__":
    SnacClient().run()


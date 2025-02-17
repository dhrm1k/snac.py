import re
import os
import httpx
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Horizontal
from textual.widgets import Header, Footer, Static, Button, RichLog, Input
from textual.screen import Screen
from rich.markdown import Markdown
from html import unescape
from typing import ClassVar

# Load environment variables
load_dotenv()
SNAC_HOST = os.getenv("SNAC_HOST")
API_TOKEN = os.getenv("API_TOKEN")

def post_status(content):
    url = f"{SNAC_HOST}/api/v1/statuses"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    data = {"status": content}
    response = httpx.post(url, headers=headers, data=data)
    
    if response.status_code in [200, 201]:
        print("Post successful!")
        return True
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return False

def fetch_notifications():
    url = f"{SNAC_HOST}/api/v1/notifications"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = httpx.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching notifications: {response.status_code}, {response.text}")
        return []

class PostScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Write your post:")
        self.input_field = Input(placeholder="Type your post here...", id="post_input")
        yield self.input_field
        yield Button("Submit", id="submit_button")

    async def on_button_pressed(self, event) -> None:
        if event.button.id == "submit_button":
            content = self.input_field.value.strip()
            if content:
                if post_status(content):
                    self.app.pop_screen()
                    await self.app.fetch_timeline()

class SnacClient(App):
    TITLE = "welcome to linuxusers.in"
    CSS_PATH = "snac.tcss"

    def compose(self) -> ComposeResult:
        yield Static(self.TITLE, id="title")
        yield Header()
        self.content = ScrollableContainer()
        yield self.content
        with Horizontal(id="navbar"):
            yield Button("Post", id="post_button", classes="navbar-button")
            yield Button("Notifications", id="notifications_button", classes="navbar-button")
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
                self.content.remove_children()
                for post in posts:
                    username = f"[bold green]@[/][bright_green]{post['account']['display_name']}[/bright_green]"
                    raw_content = post['content']
                    content = unescape(re.sub(r"<.*?>", "", raw_content)).strip()
                    post_widget = Static(f"{username}\n\n[green]{content}[/green]", classes="hacker-box")
                    self.content.mount(post_widget)
        except httpx.HTTPError as e:
            self.content.mount(Static(f"[red]ERROR: {e}[/red]", classes="error"))

    async def on_button_pressed(self, event) -> None:
        if event.button.id == "post_button":
            self.push_screen(PostScreen())
        elif event.button.id == "notifications_button":
            notifications = fetch_notifications()
            if notifications:
                self.content.mount(Static(f"[yellow]Notifications:[/yellow]\n" + "\n".join([n['type'] for n in notifications]), classes="notification-box"))
            else:
                self.content.mount(Static("[yellow]No new notifications.[/yellow]", classes="notification-box"))

if __name__ == "__main__":
    SnacClient().run()

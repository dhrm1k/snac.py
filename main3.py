import re
import os
import webbrowser
import httpx
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, Button, Label
from textual.screen import Screen, ModalScreen
from html import unescape
from typing import ClassVar

# Load environment variables
load_dotenv()
SNAC_HOST = os.getenv("SNAC_HOST")
API_TOKEN = os.getenv("API_TOKEN")

class PostScreen(Screen):
    """Screen for composing a new post."""
    def compose(self) -> ComposeResult:
        yield Static("Write your post:", classes="post-label")
        self.input_field = Input(placeholder="Type your post here...", id="post-input")
        yield self.input_field
        yield Button("Submit", id="submit-post", classes="action-button")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit-post":
            content = self.input_field.value.strip()
            if content:
                await self.post_status(content)
                self.app.pop_screen()
                await self.app.fetch_timeline()

    async def post_status(self, content: str):
        url = f"{SNAC_HOST}/api/v1/statuses"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        data = {"status": content}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                self.app.notify("Toot posted successfully!", severity="success")
        except httpx.HTTPError as e:
            self.app.notify(f"Failed to post toot: {e}", severity="error")

    async def on_key(self, event):
        """Handle key presses."""
        if event.key == "escape":
            self.app.pop_screen()

class PostDetailScreen(ModalScreen):
    """Screen for displaying post details."""
    def __init__(self, post):
        super().__init__()
        self.post = post

    def compose(self) -> ComposeResult:
        username = f"[bold green]@[/][bright_green]{self.post['account']['display_name']}[/bright_green]"
        raw_content = self.post['content']
        content = unescape(re.sub(r"<.*?>", "", raw_content)).strip()
        yield Static(f"{username}\n\n[green]{content}[/green]", classes="post-detail")
        yield Button("Open in Browser", id="open-browser", classes="action-button")
        yield Button("Reply", id="reply", classes="action-button")
        yield Button("Favorite", id="favorite", classes="action-button")
        yield Button("Bookmark", id="bookmark", classes="action-button")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "open-browser":
            webbrowser.open(self.post['url'])
        elif event.button.id == "reply":
            await self.app.reply_to_post(self.post)
        elif event.button.id == "favorite":
            await self.app.favorite_post(self.post)
        elif event.button.id == "bookmark":
            await self.app.bookmark_post(self.post)

    async def on_key(self, event):
        """Handle key presses."""
        if event.key == "escape":
            self.app.pop_screen()

class SnacClient(App):
    TITLE = "Welcome to linuxusers.in"
#    CSS_PATH = "snac.tcss"
    BINDINGS = [("n", "new_toot", "New Toot")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self.TITLE, id="title")
        self.timeline = ScrollableContainer(id="timeline")
        yield self.timeline
        with Horizontal(id="navbar"):
            yield Button("Post", id="post-button", classes="navbar-item")
            yield Button("Notifications", id="notifications-button", classes="navbar-item")
        yield Footer()

    async def on_mount(self) -> None:
        await self.fetch_timeline()

    async def fetch_timeline(self):
        """Fetch the home timeline and display posts."""
        url = f"{SNAC_HOST}/api/v1/timelines/home"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                posts = response.json()
                self.timeline.remove_children()
                for post in posts:
                    username = f"[bold green]@[/][bright_green]{post['account']['display_name']}[/bright_green]"
                    raw_content = post['content']
                    content = unescape(re.sub(r"<.*?>", "", raw_content)).strip()
                    post_widget = Static(f"{username}\n\n[green]{content}[/green]", classes="post")
                    post_widget.post_data = post  # Attach post data to the widget
                    post_widget.on_click = lambda: self.show_post(post_widget.post_data)
                    self.timeline.mount(post_widget)
        except httpx.HTTPError as e:
            self.timeline.mount(Static(f"[red]ERROR: {e}[/red]", classes="error"))

    def show_post(self, post):
        """Display the selected post in a modal screen."""
        self.push_screen(PostDetailScreen(post))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the navbar."""
        if event.button.id == "post-button":
            self.push_screen(PostScreen())
        elif event.button.id == "notifications-button":
            await self.fetch_notifications()

    async def reply_to_post(self, post):
        """Reply to the selected post."""
        reply_input = Input(placeholder="Type your reply...", id="reply-input")
        send_button = Button("Send Reply", id="send-reply", classes="action-button")
        self.push_screen(ModalScreen(reply_input, send_button))

    async def favorite_post(self, post):
        """Favorite the selected post."""
        url = f"{SNAC_HOST}/api/v1/statuses/{post['id']}/favourite"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(url, headers=headers)
                response.raise_for_status()
                self.notify("Post favorited!", severity="success")
        except httpx.HTTPError as e:
            self.notify(f"Failed to favorite post: {e}", severity="error")

    async def bookmark_post(self, post):
        """Bookmark the selected post."""
        url = f"{SNAC_HOST}/api/v1/statuses/{post['id']}/bookmark"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(url, headers=headers)
                response.raise_for_status()
                self.notify("Post bookmarked!", severity="success")
        except httpx.HTTPError as e:
            self.notify(f"Failed to bookmark post: {e}", severity="error")

    async def fetch_notifications(self):
        """Fetch and display notifications."""
        url = f"{SNAC_HOST}/api/v1/notifications"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                notifications = response.json()
                if notifications:
                    self.timeline.mount(Static(f"[yellow]Notifications:[/yellow]\n" + "\n".join([n['type'] for n in notifications]), classes="notification-box"))
                else:
                    self.timeline.mount(Static("[yellow]No new notifications.[/yellow]", classes="notification-box"))
        except httpx.HTTPError as e:
            self.timeline.mount(Static(f"[red]ERROR: {e}[/red]", classes="error"))

    def action_new_toot(self):
        """Action for posting a new toot."""
        self.push_screen(PostScreen())

if __name__ == "__main__":
    SnacClient().run()

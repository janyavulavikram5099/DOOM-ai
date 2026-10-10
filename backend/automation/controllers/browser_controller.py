"""
VIKRAM AI / DOOM AI - Browser Controller
Automates Chrome & Edge:
1. Web searches with auto-navigation to first result
2. Gmail email drafting
3. Navigation and tab controls
"""

import logging
import time
import urllib.parse
import webbrowser
from typing import Any

from ..action_engine import UIActionEngine
from ..base_controller import BaseAppController
from ...execution.browser_executor import BrowserExecutor

logger = logging.getLogger("vikram.automation.browser")


class BrowserController(BaseAppController):
    name = "Browser"
    aliases = ["chrome", "google chrome", "browser", "edge", "microsoft edge"]

    def launch(self) -> tuple[bool, str]:
        return BrowserExecutor.open_chrome()

    def close(self) -> tuple[bool, str]:
        from ...execution.application_executor import ApplicationExecutor
        return ApplicationExecutor.close("chrome")

    def execute_action(self, action: str, params: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        action_lower = action.lower().strip()

        if action_lower == "open":
            ok, msg = self.launch()
            return ok, msg, {}

        if action_lower == "close":
            ok, msg = self.close()
            return ok, msg, {}

        if action_lower in ["search_and_open_top_result", "search_and_open"]:
            query = params.get("query") or params.get("search_query") or ""
            return self.search_and_open(query, open_first=True)

        if action_lower in ["search", "search_web", "google"]:
            query = params.get("query") or params.get("search_query") or ""
            open_first = bool(params.get("open_first_result", False))
            return self.search_and_open(query, open_first=open_first)

        elif action_lower in ["draft_email", "send_email", "email"]:
            recipient = params.get("recipient") or params.get("contact") or ""
            subject = params.get("subject") or "Message from Master"
            body = params.get("body") or params.get("message") or ""
            return self.draft_email(recipient, subject, body)

        elif action_lower in ["open_url", "navigate"]:
            url = params.get("url") or params.get("website") or ""
            return self.navigate_to(url)

        return False, f"Unsupported action '{action}' for Browser.", {}

    def search_and_open(self, query: str, open_first: bool = False) -> tuple[bool, str, dict[str, Any]]:
        """Searches Google for a query and optionally clicks / opens the top result."""
        if not query:
            return False, "Search query was empty, Master.", {}

        # 1. Execute search in Chrome with default profile
        BrowserExecutor.search_web(query, engine="google", browser="chrome")
        hwnd = UIActionEngine.wait_for_window("Chrome", ["chrome.exe"], timeout=5.0)

        if open_first and hwnd:
            UIActionEngine.set_foreground(hwnd)
            time.sleep(1.2)  # Wait for Google results page to render
            # Navigate to the first organic search link via Tab / Enter
            UIActionEngine.press_key("tab")
            time.sleep(0.1)
            UIActionEngine.press_key("enter")
            return True, f"Opened top search result for {query}, Master.", {"query": query, "opened_first": True}

        return True, f"Searching for {query}, Master.", {"query": query}

    def draft_email(self, recipient: str, subject: str, body: str) -> tuple[bool, str, dict[str, Any]]:
        """Opens Gmail with a pre-filled draft to the recipient with message body."""
        enc_rec = urllib.parse.quote(recipient)
        enc_sub = urllib.parse.quote(subject)
        enc_body = urllib.parse.quote(body)
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={enc_rec}&su={enc_sub}&body={enc_body}"

        BrowserExecutor.open_chrome(gmail_url)
        return True, f"Email drafted to {recipient or 'recipient'}, Master.", {"recipient": recipient, "subject": subject, "body": body}

    def navigate_to(self, url: str) -> tuple[bool, str, dict[str, Any]]:
        """Navigates to a specific website."""
        BrowserExecutor.open_website(url)
        return True, f"Opening {url}, Master.", {"url": url}

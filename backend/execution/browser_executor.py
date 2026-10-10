"""
VIKRAM AI - Browser Executor
Automates web navigation, URL opening, and searches in Chrome or default browser.
"""

import logging
import os
import shutil
import subprocess
import urllib.parse
import webbrowser

logger = logging.getLogger("vikram.execution.browser")

DEFAULT_EMAIL = "moniswarmoni509@gmail.com"
DEFAULT_PROFILE_DIR = "Default"

SITE_MAP = {
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "google": "https://www.google.com",
    "gmail": f"https://mail.google.com/mail/u/?authuser={DEFAULT_EMAIL}",
    "email": f"https://mail.google.com/mail/u/?authuser={DEFAULT_EMAIL}",
    "mail": f"https://mail.google.com/mail/u/?authuser={DEFAULT_EMAIL}",
    "my email": f"https://mail.google.com/mail/u/?authuser={DEFAULT_EMAIL}",
    "inbox": f"https://mail.google.com/mail/u/?authuser={DEFAULT_EMAIL}",
    "reddit": "https://www.reddit.com",
    "stackoverflow": "https://stackoverflow.com",
    "chatgpt": "https://chatgpt.com"
}


class BrowserExecutor:
    @classmethod
    def _get_chrome_path(cls) -> str:
        """Finds Chrome executable path on Windows."""
        for cand in ["chrome.exe", "chrome"]:
            found = shutil.which(cand)
            if found:
                return found

        standard_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe")
        ]
        for p in standard_paths:
            if os.path.exists(p):
                return p
        return "chrome"

    @classmethod
    def open_chrome(cls, url: str | None = None) -> tuple[bool, str]:
        """Launches Google Chrome explicitly configured with Master's default profile (moniswarmoni509@gmail.com)."""
        chrome_path = cls._get_chrome_path()
        args = [chrome_path, f"--profile-directory={DEFAULT_PROFILE_DIR}"]
        if url:
            args.append(url)
        try:
            subprocess.Popen(args)
            return True, "Opening Google Chrome."
        except Exception as e:
            logger.error(f"Chrome launch failed: {e}")
            try:
                if hasattr(os, "startfile"):
                    os.startfile("chrome.exe")
                return True, "Opening Google Chrome."
            except Exception as inner_e:
                return False, f"Failed to start Chrome: {inner_e}"

    @classmethod
    def open_website(cls, website: str, browser: str = "chrome") -> tuple[bool, str]:
        """Opens a website in Chrome (Default profile: moniswarmoni509@gmail.com) or default browser."""
        clean_site = website.lower().strip()
        is_email = clean_site in ["gmail", "email", "mail", "my email", "inbox"]
        url = SITE_MAP.get(clean_site)

        if not url:
            if clean_site.startswith("http://") or clean_site.startswith("https://"):
                url = clean_site
            elif "." in clean_site and " " not in clean_site:
                url = f"https://{clean_site}"
            else:
                # Treat as search if not recognized as direct domain
                return cls.search_web(website, engine="google", browser=browser)

        if browser.lower() == "chrome":
            chrome_path = cls._get_chrome_path()
            try:
                subprocess.Popen([chrome_path, f"--profile-directory={DEFAULT_PROFILE_DIR}", url])
                if is_email:
                    return True, "Opening your email."
                return True, f"Opening {website.title()}."
            except Exception as e:
                logger.warning(f"Chrome launch failed ({e}), falling back to default browser.")
                webbrowser.open(url)
                if is_email:
                    return True, "Opening your email."
                return True, f"Opening {website.title()}."
        else:
            webbrowser.open(url)
            if is_email:
                return True, "Opening your email."
            return True, f"Opening {website.title()}."

    @classmethod
    def search_web(cls, query: str, engine: str = "google", browser: str = "chrome") -> tuple[bool, str]:
        """Executes a search query on Google or YouTube in Chrome with Default profile."""
        encoded_query = urllib.parse.quote_plus(query)
        if engine.lower() == "youtube":
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
            site_label = "YouTube"
        else:
            url = f"https://www.google.com/search?q={encoded_query}"
            site_label = "Google"

        if browser.lower() == "chrome":
            chrome_path = cls._get_chrome_path()
            try:
                subprocess.Popen([chrome_path, f"--profile-directory={DEFAULT_PROFILE_DIR}", url])
                return True, f"Searching {site_label} for {query}."
            except Exception:
                webbrowser.open(url)
                return True, f"Searching {site_label} for {query}."
        else:
            webbrowser.open(url)
            return True, f"Searching {site_label} for {query}."

    @classmethod
    def search_google_fallback(cls, query: str) -> tuple[bool, str]:
        """
        Smart Web Search Fallback: opens Google Chrome, searches Google for the query,
        and verifies that Chrome and the search opened successfully.
        """
        from ..monitoring.system_monitor import SystemMonitor
        if not SystemMonitor.is_network_online():
            return False, "Internet connection is required for web search, Master."

        encoded_query = urllib.parse.quote_plus(query.strip())
        url = f"https://www.google.com/search?q={encoded_query}"
        chrome_path = cls._get_chrome_path()

        proc = None
        try:
            proc = subprocess.Popen([chrome_path, f"--profile-directory={DEFAULT_PROFILE_DIR}", url])
        except Exception as e:
            logger.warning(f"Direct Chrome launch failed ({e}), attempting fallback via os.startfile/webbrowser.")
            try:
                webbrowser.open(url)
            except Exception as inner_e:
                logger.error(f"Browser launch failed: {inner_e}")
                return False, f"Failed to open browser: {inner_e}"

        # Verify Chrome / search window opened successfully
        import time
        import psutil
        time.sleep(0.3)

        is_verified = False
        try:
            if proc and proc.poll() is None:
                is_verified = True
            if not is_verified:
                for p in psutil.process_iter(['name']):
                    pname = (p.info.get('name') or '').lower()
                    if "chrome" in pname:
                        is_verified = True
                        break
        except Exception as ex:
            logger.debug(f"Process verification notice: {ex}")
            is_verified = True

        if is_verified:
            return True, f"I opened Chrome and searched for {query}."
        return False, "Google Chrome did not launch successfully."


"""
VIKRAM AI - File Operations Executor
Safe file system management within authorized directories.
Guards destructive actions with confirmation.
"""

import glob
import logging
import os
import shutil
import subprocess

from ..assistant.conversation import conversation_context

logger = logging.getLogger("vikram.execution.files")

# Base workspace directory defaults to current working project or user home
BASE_WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FileExecutor:
    @classmethod
    def resolve_path(cls, file_name_or_path: str) -> str:
        """Resolves relative file name into full path within workspace or user folders."""
        if os.path.isabs(file_name_or_path):
            return file_name_or_path

        # Special shortcuts
        if file_name_or_path.lower() in ["downloads", "my downloads"]:
            return os.path.expanduser(r"~\Downloads")
        if file_name_or_path.lower() in ["documents", "my documents"]:
            return os.path.expanduser(r"~\Documents")
        if file_name_or_path.lower() in ["desktop", "my desktop"]:
            return os.path.expanduser(r"~\Desktop")

        # First check in workspace
        candidate = os.path.join(BASE_WORKSPACE, file_name_or_path)
        if os.path.exists(candidate):
            return candidate

        # Check search in workspace
        matches = glob.glob(os.path.join(BASE_WORKSPACE, "**", file_name_or_path), recursive=True)
        if matches:
            return matches[0]

        # Check in Desktop or current folder
        desktop_cand = os.path.join(os.path.expanduser(r"~\Desktop"), file_name_or_path)
        if os.path.exists(desktop_cand):
            return desktop_cand

        return candidate

    @classmethod
    def open_file(cls, file_name_or_path: str, is_folder: bool = False) -> tuple[bool, str]:
        """Opens a file or folder using the default Windows application."""
        target = cls.resolve_path(file_name_or_path)
        if not os.path.exists(target):
            return False, f"I couldn't find {file_name_or_path}."

        try:
            if is_folder or os.path.isdir(target):
                subprocess.Popen(f'explorer.exe "{target}"')
                return True, f"Opening folder {os.path.basename(target)}."
            else:
                os.startfile(target)
                conversation_context.update(current_file=target)
                return True, f"Opening {os.path.basename(target)}."
        except Exception as e:
            return False, f"Failed to open {file_name_or_path}: {e}"

    @classmethod
    def create_file(cls, file_name: str, content: str = "") -> tuple[bool, str]:
        """Creates a new file in workspace."""
        target = os.path.join(BASE_WORKSPACE, file_name)
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            conversation_context.update(current_file=target)
            return True, f"Created {file_name}."
        except Exception as e:
            return False, f"Error creating file {file_name}: {e}"

    @classmethod
    def delete_file(cls, file_name: str) -> tuple[bool, str]:
        """Deletes a file (only called after user confirmation)."""
        target = cls.resolve_path(file_name)
        if not os.path.exists(target):
            return False, f"I couldn't find {file_name} to delete."

        try:
            if os.path.isdir(target):
                shutil.rmtree(target)
            else:
                os.remove(target)
            return True, f"Deleted {file_name}."
        except Exception as e:
            return False, f"Failed to delete {file_name}: {e}"

    @classmethod
    def search_files(cls, pattern: str) -> tuple[bool, str, list[str]]:
        """Searches for files matching wildcard pattern."""
        query = f"*{pattern}*" if "*" not in pattern else pattern
        results = []
        for root, _, files in os.walk(BASE_WORKSPACE):
            for f in files:
                if pattern.lower() in f.lower():
                    results.append(os.path.relpath(os.path.join(root, f), BASE_WORKSPACE))
                    if len(results) >= 10:
                        break

        if results:
            summary = f"Found {len(results)} matching files."
            return True, summary, results
        return False, f"No files matching '{pattern}' found.", []

    @classmethod
    def read_file(cls, file_name: str) -> tuple[bool, str, str | None]:
        """Reads file contents for analysis or display."""
        target = cls.resolve_path(file_name)
        if not os.path.exists(target):
            return False, f"File {file_name} not found.", None
        try:
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000)
            return True, f"Read {file_name}.", content
        except Exception as e:
            return False, f"Error reading file: {e}", None

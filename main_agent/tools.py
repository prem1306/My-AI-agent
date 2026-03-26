import os
import subprocess
import shutil
import logging
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger("SystemTools")

class SecurityManager:
    """Manages permissions and whitelisting for system operations."""

    # Resolved from config — no hardcoded paths
    ALLOWED_DIRS = [
        os.path.abspath(config.SANDBOX_DIR),
        os.path.abspath(config.SAFE_ZONE_DIR),
    ]

    ALLOWED_COMMANDS = [
        "dir", "ls", "echo", "whoami", "date", "time",
        "notepad", "calc", "explorer"
    ]

    @staticmethod
    def validate_path(path: str) -> bool:
        """Ensure path is within allowed directories."""
        abs_path = os.path.abspath(path)
        for allowed in SecurityManager.ALLOWED_DIRS:
            if abs_path.startswith(allowed):
                return True
        logger.warning(f"Access denied to path: {path}")
        return False

    @staticmethod
    def validate_command(command: str) -> bool:
        """Ensure command is whitelisted."""
        cmd_base = command.split()[0].lower()
        if cmd_base in SecurityManager.ALLOWED_COMMANDS:
            return True
        logger.warning(f"Command blocked: {command}")
        return False


class FileTools:
    """Safe file system operations."""

    @staticmethod
    def safe_read(path: str) -> str:
        if not SecurityManager.validate_path(path):
            return "Error: Access Denied"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    def safe_write(path: str, content: str) -> str:
        if not SecurityManager.validate_path(path):
            return "Error: Access Denied"
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return "Success: File written"
        except Exception as e:
            return f"Error writing file: {e}"

    @staticmethod
    def safe_delete_folder(path: str) -> str:
        if not SecurityManager.validate_path(path):
            return "Error: Access Denied"
        try:
            shutil.rmtree(path)
            return "Success: Folder deleted"
        except Exception as e:
            return f"Error deleting folder: {e}"

    @staticmethod
    def list_sandbox() -> str:
        """List contents of the sandbox directory."""
        try:
            items = os.listdir(config.SANDBOX_DIR)
            if not items:
                return "Sandbox is empty."
            return "\n".join(items)
        except Exception as e:
            return f"Error listing sandbox: {e}"


class SystemTools:
    """Safe system execution tools."""

    @staticmethod
    def run_shell_command(command: str) -> str:
        if not SecurityManager.validate_command(command):
            return "Error: Command not whitelisted"
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=5
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error executing command: {e}"

    @staticmethod
    def open_application(app_path: str) -> str:
        """Opens a whitelisted application."""
        whitelisted_apps = ["notepad", "calc", "explorer"]
        if app_path.lower() not in whitelisted_apps:
            return f"Error: '{app_path}' is not a whitelisted application."
        try:
            subprocess.Popen(app_path)
            return f"Launched: {app_path}"
        except Exception as e:
            return f"Error launching app: {e}"

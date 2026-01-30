import subprocess
import sys

def select_folder_dialog():
    """
    Opens a native folder selection dialog.
    Currently supports macOS via AppleScript ('osascript').
    """
    try:
        if sys.platform == "darwin":
            # AppleScript to choose folder
            script = 'POSIX path of (choose folder with prompt "Select Target Directory")'
            result = subprocess.check_output(['osascript', '-e', script], text=True)
            return result.strip()
        else:
            # Fallback for Linux/Windows (if needed in future)
            # For now return None or error
            return None
    except subprocess.CalledProcessError:
        # User cancelled
        return None
    except Exception as e:
        print(f"Error opening dialog: {e}")
        return None

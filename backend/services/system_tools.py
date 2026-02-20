import subprocess
import sys
import os

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
        print(f"CRITICAL ERROR: Could not open native folder dialog: {e}")
        print("This often happens when the server is hosted remotely or doesn't have access to the display.")
        return None

def list_directory_contents(path: str):
    """
    Lists folders and files in the given path for remote browsing.
    """
    try:
        if not path or path == "":
            path = os.path.expanduser("~")
            
        if not os.path.exists(path):
            return {"error": "Path does not exist"}

        items = []
        for item in os.listdir(path):
            if item.startswith('.'): continue
            
            full_path = os.path.join(path, item)
            is_dir = os.path.isdir(full_path)
            items.append({
                "name": item,
                "path": full_path,
                "is_dir": is_dir
            })
            
        # Sort so directories come first, then alphabetically
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        
        return {
            "current_path": os.path.abspath(path),
            "parent_path": os.path.dirname(os.path.abspath(path)),
            "items": items
        }
    except Exception as e:
        return {"error": str(e)}


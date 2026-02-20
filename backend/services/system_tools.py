import subprocess
import sys
import os
import string

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
    Supports Windows drive letters by allowing navigation to 'DRIVES_ROOT'.
    """
    try:
        is_windows = sys.platform == "win32"
        
        # If no path provided, start at Home
        if not path or path == "":
            path = os.path.expanduser("~")

        # Special case for Windows: My Computer (all drives)
        if is_windows and path.upper() == "DRIVES_ROOT":
            drives = []
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    drives.append({
                        "name": f"Local Disk ({letter}:)",
                        "path": drive_path,
                        "is_dir": True,
                        "is_drive": True
                    })
            return {
                "current_path": "My Computer",
                "parent_path": None,
                "items": drives,
                "is_windows": True
            }

        if not os.path.exists(path):
            return {"error": "Path does not exist"}

        items = []
        try:
            for item in os.listdir(path):
                if item.startswith('.'): continue
                
                full_path = os.path.join(path, item)
                try:
                    is_dir = os.path.isdir(full_path)
                    items.append({
                        "name": item,
                        "path": full_path,
                        "is_dir": is_dir
                    })
                except PermissionError:
                    continue # Skip items we can't access
        except PermissionError:
            return {"error": "Permission denied accessing this directory."}
            
        # Sort so directories come first, then alphabetically
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        
        # Calculate parent path
        abs_path = os.path.abspath(path)
        parent_path = os.path.dirname(abs_path)
        
        # If we are at a drive root on Windows (e.g. C:\), parent should be DRIVES_ROOT
        if is_windows:
            # Check if current path is a drive root like 'C:\'
            if len(abs_path.rstrip('\\')) <= 3: # C:\ or C:
                parent_path = "DRIVES_ROOT"
        elif abs_path == "/":
            parent_path = None

        return {
            "current_path": abs_path,
            "parent_path": parent_path,
            "items": items,
            "is_windows": is_windows
        }
    except Exception as e:
        return {"error": str(e)}


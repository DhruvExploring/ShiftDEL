from cryptography.fernet import Fernet
import os

# Generate a key or load it (in a real app, manage this securely)
# For this demo, we'll generate one and store it in memory or a file, 
# but since the app assumes a "Sender" sets it up, we can generate it on startup or request.
# Here we'll use a simple file-based key storage for persistence across reloads.

KEY_FILE = "secret.key"

def load_key():
    if os.path.exists(KEY_FILE):
        return open(KEY_FILE, "rb").read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key

key = load_key()
cipher_suite = Fernet(key)

def encrypt_data(data: str) -> str:
    """Encrypts a string."""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    """Decrypts a string."""
    try:
        return cipher_suite.decrypt(token.encode()).decode()
    except Exception:
        return None

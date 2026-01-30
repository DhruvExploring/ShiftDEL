import os
import json
import shutil
import base64
import random
import uuid
from cryptography.fernet import Fernet
import numpy as np
import cv2
from backend.services.face_logic import verify_face, set_reference_image, FACE_LIB_AVAILABLE

# A fixed master key for encrypting the vault's metadata key. 
# In a real scenario, this might be derived from a password or hardware token.
# For this portable app, we embed it (obfuscation level security).
MASTER_APP_SECRET = b'gAAAAABkZ9_random_static_key_placeholder_for_demo=' 
# Note: Fernet keys need to be valid base64 urlsafe 32 bytes.
# We will generate a proper one for the code below or just generate one on fly for session? 
# No, for portability, if the app restarts, it needs to be constant. 
# Let's use a hardcoded valid key for this MVP to ensure the app can decrypt its own vaults.
VALID_MASTER_KEY = b'TopSecretKey_For_FaceLock_Demo_App_12345678=' 

def secure_delete(path):
    """
    Overwrites the file with random bytes before deleting to prevent forensic recovery.
    """
    if not os.path.exists(path):
        return

    try:
        length = os.path.getsize(path)
        with open(path, "wb") as f:
            f.write(os.urandom(length))
            f.flush()
            os.fsync(f.fileno())
        os.remove(path)
    except Exception as e:
        print(f"Error during secure delete of {path}: {e}")

def create_vault(target_dir, reference_img_bytes, secret_files):
    """
    Creates a secure vault in the target_dir offloading the files.
    secret_files: List of {"filename": str, "content": bytes}
    """
    if not os.path.exists(target_dir):
        return False, "Target directory does not exist."

    vault_path = os.path.join(target_dir, "SecureVault")
    if os.path.exists(vault_path):
        return False, "Vault already exists in this directory."
    
    os.makedirs(vault_path)

    # 1. Extract Face Encodings from Reference
    ref_encoding, error = set_reference_image(reference_img_bytes)
    if error:
        shutil.rmtree(vault_path)
        return False, error

    # 2. Generate Vault Key (AES)
    vault_key = Fernet.generate_key()
    cipher = Fernet(vault_key)

    # 3. Encrypt Files
    encrypted_file_paths = []
    for file_obj in secret_files:
        filename = file_obj['filename']
        content = file_obj['content']
        encrypted_content = cipher.encrypt(content)
        
        # Save payload
        safe_filename = base64.urlsafe_b64encode(filename.encode()).decode() + ".enc"
        file_path = os.path.join(vault_path, safe_filename)
        with open(file_path, "wb") as f:
            f.write(encrypted_content)
        encrypted_file_paths.append(safe_filename)

    # 4. Encrypt the Vault Key using Master Key
    # Ideally we'd use the face encoding to derive the key, but fuzzy extraction is hard.
    # We will just gate the key release with face check.
    # We store the Vault Key encrypted by a hardcoded master key, 
    # so only THIS app can open it, and only if face matches.
    master_cipher = Fernet(VALID_MASTER_KEY)
    encrypted_vault_key = master_cipher.encrypt(vault_key).decode()

    # 5. Create Metadata
    metadata = {
        "reference_encoding": ref_encoding,
        "encrypted_vault_key": encrypted_vault_key,
        "files": encrypted_file_paths,
        "failure_count": 0
    }

    with open(os.path.join(vault_path, "metadata.json"), "w") as f:
        json.dump(metadata, f)

    return True, f"Vault created at {vault_path}"

def unlock_vault(source_dir, live_img_bytes):
    """
    Verifies face and unlocks the vault.
    Returns: (Success, ListOfFiles or Message)
    ListOfFiles: [{"filename": str, "content": b64_str, "type": mime, "url": stream_url}]
    """
    vault_path = os.path.join(source_dir, "SecureVault")
    meta_path = os.path.join(vault_path, "metadata.json")

    if not os.path.exists(meta_path):
        return False, "No SecureVault found in this directory."

    with open(meta_path, "r") as f:
        metadata = json.load(f)

    # Check failure count
    if metadata.get("failure_count", 0) >= 3:
        return False, "Vault is DESTROYED due to excessive failed attempts."

    # Verify Face
    match, error_msg = verify_face(live_img_bytes, metadata["reference_encoding"])

    if not match:
        # Increment failure
        metadata["failure_count"] = metadata.get("failure_count", 0) + 1
        with open(meta_path, "w") as f:
            json.dump(metadata, f)
        
        if metadata["failure_count"] >= 3:
            # TRIGGER SELF DESTRUCT!!
            for fname in metadata["files"]:
                secure_delete(os.path.join(vault_path, fname))
            secure_delete(meta_path)
            # secure_delete(vault_path) # remove dir
            return False, "Face mismatch. Vault DESTROYED."
        
        return False, f"Face mismatch. Attempts remaining: {3 - metadata['failure_count']}"

    # If Match: Decrypt
    try:
        master_cipher = Fernet(VALID_MASTER_KEY)
        vault_key = master_cipher.decrypt(metadata["encrypted_vault_key"].encode())
        vault_cipher = Fernet(vault_key)

        decrypted_files = []
        for enc_fname in metadata["files"]:
            enc_path = os.path.join(vault_path, enc_fname)
            if not os.path.exists(enc_path):
                continue
            
            with open(enc_path, "rb") as f:
                enc_data = f.read()
            
            # Decrypt file content
            file_content = vault_cipher.decrypt(enc_data)
            
            # Restore filename (base64 decode the filename part minus .enc)
            original_b64 = enc_fname.replace(".enc", "")
            original_filename = base64.urlsafe_b64decode(original_b64).decode()
            
            # Determine type
            mime_type = "application/octet-stream"
            is_video = False
            
            # Browser Compatibility: Force .mov -> video/mp4
            if original_filename.lower().endswith(".mp4"): 
                mime_type = "video/mp4"
                is_video = True
            elif original_filename.lower().endswith(".mov"): 
                mime_type = "video/mp4" # LIE to browser to force H.264 attempt
                is_video = True
            elif original_filename.lower().endswith(".jpg") or original_filename.lower().endswith(".jpeg"): 
                mime_type = "image/jpeg"
            elif original_filename.lower().endswith(".png"):
                mime_type = "image/png"
            elif original_filename.lower().endswith(".txt"): 
                mime_type = "text/plain"

            file_obj = {
                "filename": original_filename,
                "type": mime_type,
            }

            if is_video:
                # Video Streaming Strategy: Write to temp_stream
                # We use a UUID to prevent collisions
                file_uuid = str(uuid.uuid4())
                # Force .mp4 extension so StaticFiles serves correct content-type header
                temp_filename = f"{file_uuid}.mp4" 
                temp_path = os.path.join("backend/temp_stream", temp_filename)
                
                with open(temp_path, "wb") as f:
                    f.write(file_content)
                
                # Stream URL
                file_obj["url"] = f"http://localhost:8000/api/stream/{temp_filename}"
                file_obj["content"] = "" # Empty content to save bandwidth
            else:
                # Standard Base64 for images/text
                b64_content = base64.b64encode(file_content).decode()
                file_obj["content"] = b64_content

            decrypted_files.append(file_obj)

        # Reset failure count on success
        metadata["failure_count"] = 0
        with open(meta_path, "w") as f:
            json.dump(metadata, f)

        return True, decrypted_files

    except Exception as e:
        return False, f"Decryption error: {str(e)}"

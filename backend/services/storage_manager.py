import os
import json
import shutil
import base64
import random
import uuid
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
import numpy as np
import cv2
from backend.services.face_logic import verify_face, set_reference_image, FACE_LIB_AVAILABLE
from backend.core.ephemeral_crypto import EphemeralCrypto
from backend.services.relay_client import EphemeralRelayClient
import asyncio
from datetime import datetime, timedelta

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

async def create_vault(target_dir, reference_img_bytes, secret_files):
    """
    Creates a secure vault with Ephemeral Metadata Pipeline.
    """
    if not os.path.exists(target_dir):
        return False, "Target directory does not exist."

    vault_path = os.path.join(target_dir, "SecureVault")
    if os.path.exists(vault_path):
        return False, "Vault already exists."
    
    os.makedirs(vault_path)

    face_encoding, error = set_reference_image(reference_img_bytes)
    if error:
        shutil.rmtree(vault_path)
        return False, error

    # 2. Ephemeral Session Creation
    session_id = str(uuid.uuid4())
    session_key = EphemeralCrypto.generate_session_key()
    
    # 3. Payload Encryption (AES-256-GCM)
    encrypted_file_info = []
    for file_obj in secret_files:
        filename = file_obj['filename']
        content = file_obj['content']
        content_type = file_obj.get('content_type', 'application/octet-stream')
        
        # Encrypt with GCM
        encrypted_content = EphemeralCrypto.encrypt_payload(session_key, content)
        
        safe_filename = base64.urlsafe_b64encode(filename.encode()).decode() + ".enc"
        file_path = os.path.join(vault_path, safe_filename)
        with open(file_path, "wb") as f:
            f.write(encrypted_content)
            
        encrypted_file_info.append({
            "enc_filename": safe_filename,
            "orig_filename": filename,
            "content_type": content_type
        })

    # 4. RSA Metadata Wrapping
    private_key, public_key = EphemeralCrypto.generate_rsa_keypair()
    
    # Save Private Key Locally (This is the receiver's key in a real pair)
    # For this demo, we store it in the app's secure storage area, not on USB.
    priv_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(os.path.join(os.path.expanduser("~"), f".shiftdel_{session_id}.pem"), "wb") as f:
        f.write(priv_key_pem)

    metadata = {
        "session_key": base64.b64encode(session_key).decode(),
        "face_encoding": face_encoding,
        "files": encrypted_file_info,
        "expiry": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    }
    
    wrapped_metadata = EphemeralCrypto.wrap_metadata_hybrid(public_key, metadata)

    # 5. Push to Relay
    relay = EphemeralRelayClient()
    success = await relay.create_session(session_id, wrapped_metadata)
    
    if not success:
        shutil.rmtree(vault_path)
        return False, "Failed to connect to Security Relay."

    # 6. Save Minimal Link on USB
    manifest = {
        "session_id": session_id,
        "note": "Sensitive metadata moved to Ephemeral Relay."
    }
    with open(os.path.join(vault_path, "session.json"), "w") as f:
        json.dump(manifest, f)

    return True, f"Ephemeral Vault created at {vault_path} (Session: {session_id})"

def destroy_local_vault(vault_path, session_id):
    """
    Overwrites and removes the local vault and private key.
    """
    if os.path.exists(vault_path):
        print(f"[SECURITY] Initiating local destruction of {vault_path}...")
        for root, dirs, files in os.walk(vault_path, topdown=False):
            for name in files:
                secure_delete(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(vault_path)
    
    priv_path = os.path.join(os.path.expanduser("~"), f".shiftdel_{session_id}.pem")
    if os.path.exists(priv_path):
        os.remove(priv_path)

async def unlock_vault(source_dir, live_img_bytes):
    """
    Unlocks Ephemeral Vault by communicating with Relay.
    """
    vault_path = os.path.join(source_dir, "SecureVault")
    session_manifest = os.path.join(vault_path, "session.json")

    if not os.path.exists(session_manifest):
        return False, "Invalid Ephemeral Vault (Missing session reference)."

    with open(session_manifest, "r") as f:
        manifest = json.load(f)
    
    session_id = manifest["session_id"]
    relay = EphemeralRelayClient()
    
    # 1. Fetch Encrypted Metadata from Relay
    session_data = await relay.verify_session(session_id)
    if not session_data:
        # DESTRUCTIVE LOGIC: Session missing = destroyed or expired.
        destroy_local_vault(vault_path, session_id)
        return False, "Vault destroyed due to too many failed attempts or expiry."
    
    # 2. Local RSA Unwrapping
    try:
        priv_path = os.path.join(os.path.expanduser("~"), f".shiftdel_{session_id}.pem")
        with open(priv_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        
        metadata = EphemeralCrypto.unwrap_metadata_hybrid(private_key, session_data["encrypted_metadata"])
    except Exception as e:
        return False, f"Integrity check failed: {str(e)}"

    # 3. Robust Face Matching (Euclidean Distance)
    is_match, face_error = verify_face(live_img_bytes, metadata["face_encoding"])
    
    if not is_match:
        # Tell relay to increment fail
        success, fail_info = await relay.release_key(session_id, "invalid_token_to_trigger_fail")
        if fail_info.get("fails", 0) >= 3:
            destroy_local_vault(vault_path, session_id)
            return False, "Maximum attempts reached. VAULT DESTROYED."
        return False, face_error or f"Biometric mismatch. ({fail_info.get('fails',0)}/3)"

    # 4. Key Release
    success, release_data = await relay.release_key(session_id, session_data["release_token"])
    if not success:
        if release_data.get("fails", 0) >= 3:
            destroy_local_vault(vault_path, session_id)
            return False, "Relay denied key. VAULT DESTROYED."
        return False, f"Relay denied key release. ({release_data.get('fails',0)}/3)"

    # 5. Decryption (AES-256-GCM)
    try:
        session_key = base64.b64decode(metadata["session_key"])
        decrypted_files = []
        for file_info in metadata["files"]:
            enc_fname = file_info["enc_filename"]
            enc_path = os.path.join(vault_path, enc_fname)
            with open(enc_path, "rb") as f:
                payload = f.read()
            
            raw_content = EphemeralCrypto.decrypt_payload(session_key, payload)
            
            decrypted_files.append({
                "filename": file_info["orig_filename"],
                "content": base64.b64encode(raw_content).decode(),
                "type": file_info["content_type"]
            })

        # 6. Cleanup & Delivery Sync
        await relay.mark_delivered(session_id)
        os.remove(priv_path) # Wipe local private key
        
        # USB Wipe Logic (Optional based on user preference, here we mark as delivered)
        return True, decrypted_files

    except Exception as e:
        return False, f"Pipeline Error: {str(e)}"

from fastapi import APIRouter, File, UploadFile, HTTPException, Body, Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List

from backend.services.storage_manager import create_vault, unlock_vault
from backend.services.system_tools import select_folder_dialog
import json
import os

router = APIRouter()

# Mount Static for Video Streaming
# ensuring directory exists
os.makedirs("backend/temp_stream", exist_ok=True)

class BrowseResponse(BaseModel):
    path: str

@router.post("/system/browse")
async def browse_folder():
    path = select_folder_dialog()
    if not path:
        return {"cancelled": True}
    return {"path": path}


@router.post("/vault/create")
async def create_vault_endpoint(
    target_dir: str = Form(...),
    secret_text: str = Form(None),
    reference_image: UploadFile = File(...),
    files: List[UploadFile] = File(None)
):
    """
    Creates a secure vault in the specified target directory.
    """
    # 1. Read Reference Image
    ref_bytes = await reference_image.read()
    
    # 2. Collect Secret Files
    secret_payload = []
    
    if secret_text:
        secret_payload.append({
            "filename": "message.txt",
            "content": secret_text.encode()
        })
        
    if files:
        for f in files:
            content = await f.read()
            secret_payload.append({
                "filename": f.filename,
                "content": content
            })
            
    if not secret_payload:
         raise HTTPException(status_code=400, detail="No content to encrypt.")

    # 3. Create Vault
    success, msg = create_vault(target_dir, ref_bytes, secret_payload)
    
    if not success:
        raise HTTPException(status_code=400, detail=msg)
        
    return {"success": True, "message": msg}

@router.post("/vault/unlock")
async def unlock_vault_endpoint(
    source_dir: str = Form(...),
    face_image: UploadFile = File(...)
):
    """
    Unlocks a vault from the source directory using facial verification.
    """
    face_bytes = await face_image.read()
    
    success, result = unlock_vault(source_dir, face_bytes)
    
    if not success:
        # result is error message
        raise HTTPException(status_code=403, detail=result)
        
    # result is list of decrypted files
    return {"success": True, "files": result}


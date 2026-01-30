try:
    import face_recognition as fc
    import numpy as np
    import cv2
    FACE_LIB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: face_recognition/cv2/numpy not available: {e}. Using Mock Logic.")
    FACE_LIB_AVAILABLE = False
    fc = None
    np = None
    cv2 = None

def set_reference_image(image_bytes):
    """
    Decodes the image bytes and returns the face encoding.
    Returns: (encoding, error_message)
    """
    if not FACE_LIB_AVAILABLE:
        return "MOCK_ENCODING_LIST", None

    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
             return None, "Could not decode image."
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        encodings = fc.face_encodings(rgb)
        if len(encodings) == 0:
             return None, "No face found in reference photo."
        
        return encodings[0].tolist(), None
    except Exception as e:
        return None, f"Error processing reference image: {str(e)}"

def verify_face(live_img_bytes, reference_encoding):
    """
    Decodes live image and compares with reference encoding.
    Returns: (match_boolean, error_message)
    """
    if not FACE_LIB_AVAILABLE:
        return True, None # Always match in mock mode

    if not reference_encoding:
        return False, "No reference encoding provided."

    try:
        nparr = np.frombuffer(live_img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return False, "Could not decode live image."
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        encodings = fc.face_encodings(rgb)
        if len(encodings) == 0:
            return False, "No face found in live image."
            
        known_enc = np.array(reference_encoding)
        # Compare
        results = fc.compare_faces([known_enc], encodings[0], tolerance=0.5) # slightly stricter for vault
        
        if results[0]:
            return True, None
        else:
            return False, "Face mismatch."

    except Exception as e:
        return False, f"Error during verification: {str(e)}"



try:
    import face_recognition as fc
    FACE_LIB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: face_recognition not available: {e}. Using Mock Logic.")
    FACE_LIB_AVAILABLE = False
    fc = None


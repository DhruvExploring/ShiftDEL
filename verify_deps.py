import sys
try:
    import dlib
    print(f"dlib version: {dlib.__version__}")
    print(f"dlib paths: {dlib.__file__}")
    import face_recognition
    print("face_recognition loaded successfully")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

import os

def detect_file_type(file_path):
    return os.path.splitext(file_path)[1].lower()

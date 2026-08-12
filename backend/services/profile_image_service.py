"""
Profile picture upload service.
- save_profile_image(): validates, saves, returns filename
- delete_profile_image(): removes old file from disk
"""
import os
import uuid
from flask import current_app
from PIL import Image
import io


ALLOWED = {'jpg', 'jpeg', 'png'}
MAX_DIMENSION = 512   # resize to at most 512x512 to save space


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED


def save_profile_image(file_storage):
    """
    Validate and save an uploaded profile picture.
    Returns (filename: str | None, error: str | None)
    """
    if not file_storage or file_storage.filename == '':
        return None, "No file selected."

    if not allowed_file(file_storage.filename):
        return None, "Only JPG and PNG files are allowed."

    try:
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream)
        img.verify()                  # catches corrupt files
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream).convert('RGB')
    except Exception:
        return None, "Uploaded file is not a valid image."

    # Resize if too large
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    if ext == 'jpg':
        ext = 'jpeg'
    filename = f"{uuid.uuid4().hex}.{ext}"

    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    buf = io.BytesIO()
    img.save(buf, format=ext.upper(), quality=85, optimize=True)
    buf.seek(0)

    save_path = os.path.join(upload_dir, filename)
    with open(save_path, 'wb') as f:
        f.write(buf.read())

    return filename, None


def delete_profile_image(filename):
    """Remove a profile picture file from disk. Silent on missing files."""
    if not filename:
        return
    try:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"[PROFILE IMG DELETE ERROR] {e}")

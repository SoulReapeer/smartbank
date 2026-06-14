"""
QR Transfer Service
- generate_qr_for_account(): builds a QR code image (PNG bytes) encoding the account number
- decode_qr_image(): reads an uploaded image file and extracts the embedded account number
"""
import io
import qrcode
from qrcode.constants import ERROR_CORRECT_M
import cv2
import numpy as np
from PIL import Image


QR_PREFIX = "SMARTBANK:"  # simple namespacing so SmartBank QR codes are identifiable


def generate_qr_for_account(account_number):
    """
    Generate a QR code PNG (bytes) encoding the account number.
    Format: SMARTBANK:<account_number>
    """
    payload = f"{QR_PREFIX}{account_number}"

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1E3A8A", back_color="#FFFFFF").convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()


def decode_qr_image(file_stream):
    """
    Decode an uploaded image (file-like object) and extract the account number.

    Returns:
        (account_number: str | None, error: str | None)
    """
    try:
        file_stream.seek(0)
        img = Image.open(file_stream).convert("RGB")
    except Exception:
        return None, "Uploaded file is not a valid image."

    # Convert PIL image -> OpenCV format (BGR numpy array)
    np_img = np.array(img)
    cv_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)

    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(cv_img)

    if not data:
        # Try grayscale fallback (helps with some low-contrast images)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        data, points, _ = detector.detectAndDecode(gray)

    if not data:
        return None, "No QR code detected in the uploaded image."

    if data.startswith(QR_PREFIX):
        account_number = data[len(QR_PREFIX):].strip()
    else:
        # Accept raw account-number-only QR codes too (e.g. ACC20261234)
        account_number = data.strip()

    if not account_number:
        return None, "QR code does not contain a valid account number."

    return account_number, None

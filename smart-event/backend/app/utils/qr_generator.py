import qrcode
import os
import json
from app.core.config import settings

def generate_qr_code(ticket_code: str, booking_id: int) -> str:
    data = json.dumps({
        "ticket_code": ticket_code,
        "booking_id": booking_id
    })
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Ensure directory exists
    os.makedirs(settings.QR_CODE_DIR, exist_ok=True)
    
    file_path = f"{settings.QR_CODE_DIR}/{ticket_code}.png"
    img.save(file_path)
    
    return file_path

from PIL import Image
from io import BytesIO

def generate_img(width: int, height: int) -> bytes:
    """Generate random img and return its bytes."""
    color = (255, 0, 0)
    new_img = Image.new("RGB", (width, height), color)
    img_io = BytesIO()
    new_img.save(img_io, format='JPEG', quality=100)

    return img_io.getvalue()

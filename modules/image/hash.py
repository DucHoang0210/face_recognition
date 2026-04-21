import hashlib

def hash_image(image_path):
    with open(image_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
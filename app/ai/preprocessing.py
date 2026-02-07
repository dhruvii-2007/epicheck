from PIL import Image
import numpy as np

def preprocess_image(image_path: str, img_size=224):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((img_size, img_size))
    arr = np.array(img).astype("float32") / 255.0
    arr = np.transpose(arr, (2, 0, 1))  # CHW
    return np.expand_dims(arr, axis=0)

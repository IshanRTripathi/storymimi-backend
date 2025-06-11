import os
from pathlib import Path

# Create a simple 1x1 pixel PNG image (red color)
red_pixel = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "89000000017352474200aece1ce90000000467414d410000b18f0bfc61050000"
    "000c49444154789c636060606000000005000001a5f645380000000049454e44ae426082"
)

# Create a simple 1x1 pixel PNG image (blue color)
blue_pixel = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "89000000017352474200aece1ce90000000467414d410000b18f0bfc61050000"
    "000c49444154789c6360c0030000000200000195f64538000000004945"
    "4e44ae426082"
)

# Create a simple 1x1 pixel PNG image (green color)
green_pixel = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "89000000017352474200aece1ce90000000467414d410000b18f0bfc61050000"
    "000c49444154789c6360183000000002000001a0f64538000000004945"
    "4e44ae426082"
)

# Get the path to the mock data directory
MOCK_DATA_DIR = Path(__file__).parent / "data"

# Create the images directory if it doesn't exist
os.makedirs(MOCK_DATA_DIR / "images", exist_ok=True)

# Write the sample images
with open(MOCK_DATA_DIR / "images" / "sample_image_1.png", "wb") as f:
    f.write(red_pixel)

with open(MOCK_DATA_DIR / "images" / "sample_image_2.png", "wb") as f:
    f.write(blue_pixel)

with open(MOCK_DATA_DIR / "images" / "sample_image_3.png", "wb") as f:
    f.write(green_pixel)

print("Sample images created successfully.")
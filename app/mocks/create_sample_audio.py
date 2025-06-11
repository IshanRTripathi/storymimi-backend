import os
from pathlib import Path

# Create a simple empty MP3 file (not actually playable)
empty_mp3 = bytes.fromhex(
    "494433030000000000545432000000000054414c42000000000000"
)

# Get the path to the mock data directory
MOCK_DATA_DIR = Path(__file__).parent / "data"

# Create the audio directory if it doesn't exist
os.makedirs(MOCK_DATA_DIR / "audio", exist_ok=True)

# Write the sample audio files
with open(MOCK_DATA_DIR / "audio" / "sample_audio_1.mp3", "wb") as f:
    f.write(empty_mp3)

with open(MOCK_DATA_DIR / "audio" / "sample_audio_2.mp3", "wb") as f:
    f.write(empty_mp3)

with open(MOCK_DATA_DIR / "audio" / "sample_audio_3.mp3", "wb") as f:
    f.write(empty_mp3)

print("Sample audio files created successfully.")
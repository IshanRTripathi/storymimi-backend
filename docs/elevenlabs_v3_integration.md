ElevenLabs Text-to-Speech API
ElevenLabs’ TTS API uses an API key passed in the xi-api-key header
elevenlabs.io
. You convert text to speech by sending a POST request to:
bash
Copy
Edit
https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
where {voice_id} is the ID of the voice you want to use
elevenlabs.io
. For authentication, include your key in the header, e.g.:
http
Copy
Edit
xi-api-key: YOUR_ELEVENLABS_API_KEY
Content-Type: application/json
The request body (JSON) should contain the text and optional parameters. For example:
json
Copy
Edit
{
  "text": "Hello world",
  "model_id": "eleven_multilingual_v2"
}
By default the API uses a high-quality multilingual model (v2). You can also set output_format via a query parameter (e.g. ?output_format=mp3_22050_32) to control the MP3 sample rate/bitrate
elevenlabs.io
elevenlabs.io
. The response body is the raw audio file data (MP3 by default)
elevenlabs.io
. In Python, you can use the requests library to call this endpoint and write response.content to an MP3 file.
ElevenLabs “Normal” vs “v3” Modes
ElevenLabs recently introduced the new v3 model, which is more expressive. You can use v3 via the same TTS endpoint by specifying the model ID eleven_v3 in the request
elevenlabs.io
. For example, set "model_id": "eleven_v3" (assuming your account has access). The API path remains /v1/text-to-speech/{voice_id}, but you choose model_id="eleven_v3" instead of the default
elevenlabs.io
elevenlabs.io
. Alternatively, ElevenLabs offers a new Text-to-Dialogue endpoint for multi-speaker v3 dialogues (using a JSON array of {speaker_id, text}), but as of 2025 this endpoint is still in preview
elevenlabs.io
help.elevenlabs.io
. For most cases, using v3 in the standard endpoint is sufficient. In summary:
Normal mode: Use default or v2 models (e.g. eleven_multilingual_v2) in /v1/text-to-speech
elevenlabs.io
.
v3 mode: Use model_id eleven_v3 in the same endpoint
elevenlabs.io
 (and optionally use audio tags or dialogue mode for advanced control).
After sending the request, the API returns the MP3 audio in the HTTP response. In Python, check for response.status_code == 200 and then write response.content to a file. For example:
python
Copy
Edit
res = requests.post(url, headers=headers, json=payload, params={"output_format": "mp3_22050_32"})
if res.status_code == 200:
    with open("output.mp3", "wb") as f:
        f.write(res.content)
This saves the MP3 audio locally
elevenlabs.io
.
Supabase Storage API
Supabase Storage is a built-in file storage backed by S3/Postgres. To upload a file via HTTP, use the Supabase Storage REST API. The endpoint to upload (create) a new object is:
ruby
Copy
Edit
POST https://<your-supabase-url>/storage/v1/object/{bucket}/{path}
where {bucket} is your bucket name (e.g. audio) and {path} is the file path (often just the filename). For example:
ruby
Copy
Edit
https://projectxyz.supabase.co/storage/v1/object/audio/output.mp3
supabase.com
. Authentication for this API requires your Supabase service_role key (full privileges) or an authenticated JWT with write permissions. Include the key both as an apikey header and as a Bearer token. For example (as shown in a Supabase discussion):
http
Copy
Edit
Authorization: Bearer YOUR_SERVICE_ROLE_KEY
apikey: YOUR_SERVICE_ROLE_KEY
Content-Type: audio/mpeg
Then send the file bytes in the request body (not as JSON). A Content-Type matching the file (e.g. audio/mpeg for MP3) is required
github.com
. For instance, using curl this looks like:
bash
Copy
Edit
curl --request POST \
  --url 'https://projectxyz.supabase.co/storage/v1/object/audio/output.mp3' \
  --header 'Content-Type: audio/mpeg' \
  --header 'apikey: <YOUR_SERVICE_ROLE_KEY>' \
  --header 'Authorization: Bearer <YOUR_SERVICE_ROLE_KEY>' \
  --data-binary '@./output.mp3'
This sends output.mp3 to the audio bucket. (The official docs describe this endpoint under “Upload a new object”
supabase.com
.) You can optionally add query parameters or headers like x-upsert: false if you want to avoid overwriting. In Python, you would do something like:
python
Copy
Edit
with open("output.mp3", "rb") as f:
    res = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/audio/output.mp3",
        headers={
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Content-Type": "audio/mpeg"
        },
        data=f
    )
Check res.status_code; a 200 means success.
Public URL for Uploaded File
If your bucket is public (set via Supabase dashboard or API), files can be accessed via a standard URL without additional auth
supabase.com
. The format is:
pgsql
Copy
Edit
https://<your-supabase-url>/storage/v1/object/public/{bucket}/{path}
For example: https://projectxyz.supabase.co/storage/v1/object/public/audio/output.mp3
supabase.com
. After uploading, you can form this URL directly to return or display to users. (For private buckets, you’d need to generate a signed URL or use the object/authenticated path with proper JWT
supabase.com
.)
Example Python Script
python
Copy
Edit
#!/usr/bin/env python3
import requests

# ==== Configuration (replace placeholders) ====
ELEVEN_API_KEY = "YOUR_ELEVENLABS_API_KEY"
VOICE_ID = "YOUR_VOICE_ID"
USE_V3 = False  # Set True to use model_id "eleven_v3"

SUPABASE_URL = "https://your-project.supabase.co"   # e.g. "https://abcd1234.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "YOUR_SUPABASE_SERVICE_ROLE_KEY"
BUCKET_NAME = "audio"
LOCAL_FILE = "output.mp3"  # local path to save TTS output

# Input text (hardcoded for this script)
text_to_speak = "Hello world, this is a test of ElevenLabs text-to-speech."

# --- 1. Convert text to speech via ElevenLabs API ---
tts_endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
headers = {
    "xi-api-key": ELEVEN_API_KEY,
    "Content-Type": "application/json"
}
payload = {
    "text": text_to_speak
}
# Specify v3 model if requested
if USE_V3:
    payload["model_id"] = "eleven_v3"
# You can also adjust output_format if needed (default is mp3_44100_128)
params = {"output_format": "mp3_22050_32"}

try:
    response = requests.post(tts_endpoint, json=payload, headers=headers, params=params)
    response.raise_for_status()
    # Write MP3 content to file
    with open(LOCAL_FILE, "wb") as out_file:
        out_file.write(response.content)
    print(f"Audio saved to {LOCAL_FILE}")
except requests.exceptions.RequestException as e:
    print("Error generating speech:", e)
    exit(1)

# --- 2. Upload MP3 file to Supabase Storage ---
upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{LOCAL_FILE}"
supabase_headers = {
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Content-Type": "audio/mpeg"
}
try:
    with open(LOCAL_FILE, "rb") as audio_file:
        upload_resp = requests.post(upload_url, headers=supabase_headers, data=audio_file)
    upload_resp.raise_for_status()
    print(f"Upload successful: {LOCAL_FILE} -> bucket '{BUCKET_NAME}'")
except requests.exceptions.RequestException as e:
    print("Error uploading to Supabase:", e)
    exit(1)

# --- 3. Construct Public URL (if bucket is public) ---
public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{LOCAL_FILE}"
print("Public URL:", public_url)
Instructions: Fill in your ElevenLabs API key and voice ID, and your Supabase project URL and service role key. The script sends the hardcoded text to ElevenLabs (in normal or v3 mode), saves the MP3, then uploads it to the audio bucket in Supabase, and finally prints the public URL of the uploaded file. Error checks are included for both API calls. All steps use only the official HTTP APIs as documented above
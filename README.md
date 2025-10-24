# Quizly

Small Django + DRF project for creating and managing quizzes. Features:

- JWT authentication using SimpleJWT
- Automatic quiz generation from YouTube transcripts (optional LLM)
- API endpoints for registration, login, quiz creation and management

Important: ffmpeg must be installed and available in PATH before setting up
the project — yt-dlp and Whisper require ffmpeg for audio processing.

Installation checklist
1. Ensure ffmpeg is installed and on PATH (see below).
2. Create and use the virtualenv in the project root: `python -m venv env`.
3. Install dependencies: `(env) python -m pip install -r requirements.txt`.
4. Apply migrations: `(env) python manage.py migrate`.
5. Start server: `(env) python manage.py runserver`.
6. If using the frontend from a different origin (e.g. Live Server at :5500), add that origin to CORS (see CORS section).

CORS: see the "CORS" section below for the minimal steps.

This README contains:

- ffmpeg installation instructions (Windows / macOS / Linux)
- Project setup (virtualenv, dependencies, migrations)
- Important environment variables
- Short API overview
- Tests & troubleshooting

## Requirements

- Python 3.10+ (development used Python 3.13)
- ffmpeg available on PATH
- optionally: GPU/CUDA for Whisper (set `WHISPER_USE_CUDA`)

## Installing FFMPEG

There are several trusted sources for Windows builds (e.g. Gyan or
BtbN). Download a ZIP build and extract it locally.

### Windows — manual (GUI approach)

1. Download an up-to-date FFmpeg build:

   https://ffmpeg.org/download.html

   Recommended Windows builds: https://www.gyan.dev/ffmpeg/builds/
   or https://github.com/BtbN/FFmpeg-Builds/releases

2. Extract the ZIP, e.g. to `C:\ffmpeg`.

3. Add `C:\ffmpeg\bin` to your PATH:

   - Right click "This PC" → Properties → Advanced system settings → Environment Variables
   - Edit `Path` under user or system variables → New → add `C:\ffmpeg\bin`

   Or in PowerShell (for current user):

```powershell
setx PATH "$($env:Path);C:\ffmpeg\bin"
# Open a new PowerShell session after running setx
```

4. Verify installation:

```powershell
ffmpeg -version
```

### Windows — winget (if available)

```powershell
winget install --id Gyan.FFmpeg -e
```

### macOS (Homebrew)

```bash
brew update
brew install ffmpeg
```

### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install ffmpeg
```

## Project setup

Recommended steps (PowerShell examples):

```powershell
# 1) Create virtual environment
python -m venv env

# 2) Activate (PowerShell)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned; .\env\Scripts\Activate.ps1

# If Activate.ps1 is blocked, you can call the venv python directly:
.\env\Scripts\python.exe -m pip install -r requirements.txt

# 3) Install dependencies
pip install -r requirements.txt

# 4) Run migrations
python manage.py migrate

# 5) Optional: create superuser
python manage.py createsuperuser

# 6) Start development server
python manage.py runserver
```

If you cannot run `Activate.ps1`, use the venv Python directly as shown above.

## Important environment variables

- `GEMINI_API_KEY` — API key for the LLM used to generate quizzes
- `WHISPER_USE_CUDA` — set to `1` to enable CUDA for Whisper

Example (PowerShell):

```powershell
setx GEMINI_API_KEY "your_api_key_here"
setx WHISPER_USE_CUDA 1
```

Open a new shell after `setx` so the variables are available.

## API overview (short)

- POST `/api/register/` — Register (username, email, password, confirmed_password)
- POST `/api/login/` — Login; sets `access_token` and `refresh_token` as HttpOnly cookies and returns basic user info
- POST `/api/token/refresh/` — Refresh access token (reads refresh from cookie)
- POST `/api/logout/` — Blacklist refresh token (if enabled) and clear cookies
- POST `/api/createQuiz/` — Create a quiz from a YouTube URL (auth required)
- GET  `/api/quizzes/` — List own quizzes (auth required)
- GET  `/api/quizzes/<pk>/` — Quiz detail (auth and creator required)

The tests include example requests and expected responses.

## Tests

Run Django tests with:

```powershell
.\env\Scripts\python.exe manage.py test
# or, if venv is activated:
python manage.py test
```

## Troubleshooting

- `ModuleNotFoundError: No module named 'django'` → venv not activated. Use the venv python or activate the environment.
- `Activate.ps1` blocked → temporarily set PowerShell execution policy: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` or use the venv python directly.
- `ffmpeg` not found → check `ffmpeg -version` and PATH. On Windows: ensure `ffmpeg\bin` is in PATH.

## CORS (Cross-Origin Resource Sharing)

Note: `django-cors-headers` is included in `requirements.txt` for this project.

Make sure your frontend origin (e.g. `http://127.0.0.1:5500`) is listed in
`CORS_ALLOWED_ORIGINS` and `CORS_ALLOW_CREDENTIALS = True` is set in
`core/settings.py`, then restart the dev server. From the frontend send
requests with credentials (`credentials: 'include'` / `withCredentials: true`) when using cookies.

---
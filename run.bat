@echo off
cd /d "%~dp0"

if not exist .venv (
    py -m venv .venv
)

call .venv\Scriptsctivate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Setup complete.
echo 1. Copy .env.example to .env and add your SerpAPI, Hunter, and Gmail values.
echo 2. Generate queue: python main.py "software engineer Mastercard Pune" --limit 5 --min-confidence 80
echo 3. Dry-run sender: python sender.py
echo 4. Real send after review: python sender.py --send
cmd /k

I:\Playground\techguys\tailoredCV\run_pipeline.bat@echo off
REM --- FIX 1: Force the script to look in the correct folder ---
cd /d "I:\Playground\techguys\tailoredCV\"

SETLOCAL

REM Check if the virtual environment directory exists.
IF NOT EXIST .venv (
    echo "Creating virtual environment..."
    python -m venv .venv
    IF ERRORLEVEL 1 (
        echo "ERROR: Failed to create virtual environment. Exiting."
        exit /b 1
    )
)

echo "Activating virtual environment..."
CALL .venv\Scripts\activate.bat

echo "Installing dependencies..."
pip install --upgrade -r requirements.txt

echo.
echo "--- Validation Step: Checking for Chrome ---"
CALL :validate_chrome

:: --- PHASE 0: SCRAPE LINKEDIN FOR NETWORKING ---
echo "Running the Linkedin Networking Bot..."
:: Now that venv is active, we just use 'python'
.venv\Scripts\python "I:\Playground\techguys\tailoredCV\0_LinkedIn_Networking\scrape_linkedin_networking_bot.py"

echo "================================================="
echo  "PIPELINE FINISHED SUCCESSFULLY"
echo "================================================="
echo.
GOTO :EOF

REM --- SUBROUTINES ---

:validate_chrome
echo.
echo "--- Checking for Chrome Scrapper Debugger instance ---"
tasklist /FI "WINDOWTITLE eq Chrome Personal LinkedIn Debugger*" | find "chrome.exe" > nul
IF ERRORLEVEL 1 (
    echo "  - Starting new Chrome instance..."
    START "Chrome Scrapper Debugger" chrome.bat
) ELSE (
    echo "  - Chrome is already running."
)

echo.
echo "--- Bringing Chrome to the front ---"
powershell -command "$wshell = New-Object -ComObject wscript.shell; $wshell.AppActivate('Chrome Personal LinkedIn Debugger*'); Start-Sleep -Milliseconds 250"
GOTO :EOF
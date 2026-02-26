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
echo [PHASE 0] Running the Linkedin Networking Bot...
:: Now that venv is active, we just use 'python'
python "0_LinkedIn_Networking\scrape_linkedin_networking_bot.py"

if %errorlevel% neq 0 (
    echo [ERROR] The Networking Scraper script failed. Aborting the pipeline.
    goto end
)
echo [PHASE 0] Scraper completed.
echo.

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


::Temporary debug break
goto end


:: --- PHASE 1: SCRAPE LINKEDIN FOR NEW OPPORTUNITIES ---
echo [PHASE 1] Running the LinkedIn Scraper...
:: Now that venv is active, we just use 'python'
python "1_Scraper\scrape_linkedin.py"

if %errorlevel% neq 0 (
    echo [ERROR] The Scraper script failed. Aborting the pipeline.
    goto end
)
echo [PHASE 1] Scraper completed.
echo.




:: --- PHASE 2: TAILOR DATA WITH GOOGLE AI ---
echo [PHASE 2] Running the AI Data Tailor...
:: Now that venv is active, we just use 'python'
python "2_Data_Tailor\tailor_data.py"

if %errorlevel% neq 0 (
    echo [ERROR] The AI Data Tailor script failed. Aborting the pipeline.
    goto end
)
echo [PHASE 2] AI Data Tailoring completed.
echo.


:: --- PHASE 3: GENERATE FINAL DOCUMENTS ---
echo [PHASE 3] Running the Final Document Generator...
:: Now that venv is active, we just use 'python'
python "2_Generator\generate_documents.py"

if %errorlevel% neq 0 (
    echo [ERROR] The Document Generator script failed. Aborting the pipeline.
    goto end
)
echo [PHASE 3] Document Generation completed.
echo.


echo =================================================
echo  PIPELINE FINISHED SUCCESSFULLY AT %TIME%
echo =================================================
echo.

:end
:: Use the 'pause' command if you want the window to stay open after finishing.
:: Great for manual testing. Comment it out (using ::) for scheduled tasks.
:: pause
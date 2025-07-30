@echo off
:: ============================================================================
:: Master Pipeline Script for the Job Application Automator
:: ============================================================================
:: This script now ACTIVATES the virtual environment before running the pipeline.
:: ============================================================================

:: Change the directory to the location of this batch file.
cd /d "%~dp0"

echo =================================================
echo  STARTING JOB APPLICATION PIPELINE AT %TIME%
echo =================================================
echo.

:: --- STEP 0: ACTIVATE THE VIRTUAL ENVIRONMENT ---
echo [STEP 0] Activating the Python virtual environment...

:: Check if the venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at ".\venv\".
    echo Please create the venv first using: python -m venv venv
    goto end
)

:: Activate the venv. The 'call' command is crucial.
call "venv\Scripts\activate.bat"
echo [STEP 0] Virtual environment activated.
echo.


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
@echo off
setlocal enabledelayedexpansion

REM --- Configuration ---
set "PYTHON_EXE=python"
set "BOT_SCRIPT=i:\Playground\techguys\tailoredCV\0_LinkedIn_Networking\scrape_linkedin_networking_bot.py"
set "PROFILES_JSON=i:\Playground\techguys\tailoredCV\data\profiles.json"
set "SESSION_JSON=i:\Playground\techguys\tailoredCV\data\profile-session-manager.json"

echo --- LinkedIn Bot Pipeline ---

REM --- 1. Determine a random enabled profile to use ---
echo Determining random profile...
for /f "tokens=1,2,3* delims=;" %%a in ('powershell -NoProfile -Command "$p = @((Get-Content -Raw $env:PROFILES_JSON ^| ConvertFrom-Json).profiles ^| Where-Object { $_.enabled }); if ($p.Count -gt 0) { $last = if (Test-Path $env:SESSION_JSON) { (Get-Content -Raw $env:SESSION_JSON ^| ConvertFrom-Json).last_used_profile_id } else { $null }; $c = @($p ^| Where-Object { $_.id -ne $last }); if ($c.Count -eq 0) { $c = $p }; $s = $c[(Get-Random -Maximum $c.Count)]; Write-Output ($s.id, $s.script, $s.port, $s.connect_url -join ';') }"') do (
    set "NEXT_PROFILE_ID=%%a"
    set "NEXT_PROFILE_SCRIPT=%%b"
    set "NEXT_PROFILE_PORT=%%c"
    set "NEXT_PROFILE_CONNECT_URL=%%d"
)

if not defined NEXT_PROFILE_ID (
    echo ERROR: No enabled profile was found. Please check %PROFILES_JSON%.
    goto :eof
)

echo Next profile to use: !NEXT_PROFILE_ID! (Port: !NEXT_PROFILE_PORT!)

REM --- 2. Update the session file with the profile we are about to use ---
echo Updating session manager with current profile: !NEXT_PROFILE_ID!
powershell -NoProfile -Command "$session = Get-Content -Raw -Path '%SESSION_JSON%' | ConvertFrom-Json; $session.last_used_profile_id = '!NEXT_PROFILE_ID!'; $session | ConvertTo-Json | Set-Content -Path '%SESSION_JSON%'"

REM --- 2. Launch the selected Chrome profile ---
echo Launching Chrome profile using: !NEXT_PROFILE_SCRIPT!
start "" "!NEXT_PROFILE_SCRIPT!"
echo Waiting for Chrome to initialize...
timeout /t 10 /nobreak >nul

REM --- 3. Run the Python Bot Script with the correct port ---
echo Starting Python bot script for port !NEXT_PROFILE_PORT!...
%PYTHON_EXE% "%BOT_SCRIPT%" --port !NEXT_PROFILE_PORT! --connect_url "!NEXT_PROFILE_CONNECT_URL!" --profile_id "!NEXT_PROFILE_ID!"

echo.
echo --- Pipeline finished for profile !NEXT_PROFILE_ID! ---
endlocal
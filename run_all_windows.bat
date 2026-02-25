@echo off
setlocal EnableExtensions

REM Always run from this script directory
cd /d "%~dp0"

echo ===========================
echo  VECTOR + site2.0 runner
echo ===========================

REM -------- Flask (VECTOR) --------
start "VECTOR Flask" cmd /k ^
"cd /d "%~dp0" && ^
if exist .venv\Scripts\activate.bat (call .venv\Scripts\activate.bat) && ^
python app.py"

REM -------- Next.js (site2.0) --------
set "NEXT_DIR=%~dp0inclusive_frontend\site2"
if not exist "%NEXT_DIR%\package.json" (
  echo.
  echo [ERROR] Не найден Next.js проект: %NEXT_DIR%
  echo Проверь, что папка inclusive_frontend\site2 существует и внутри есть package.json
  echo.
  pause
  exit /b 1
)

start "Inclusive Next" cmd /k ^
"cd /d "%NEXT_DIR%" && ^
if not exist node_modules (npm install) && ^
npm run dev"

echo.
echo Done. Flask: http://127.0.0.1:5000
echo Next : http://127.0.0.1:3000
echo.
endlocal

@echo off
setlocal
cd /d "%~dp0"      rem -> estás en ...\ECOBOT\ecobot
if exist ..\venv\Scripts\activate (
  call ..\venv\Scripts\activate
) else (
  py -m venv ..\venv
  call ..\venv\Scripts\activate
)
pip install -r requirements.txt -q
echo.
echo ====== Lanzando EcoBot (consola) ======
echo.
py -m app.server
endlocal


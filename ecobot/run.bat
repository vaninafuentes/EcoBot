@echo off
setlocal

REM Ir a la carpeta del script
cd /d "%~dp0"

REM Activar venv si no está
if not exist venv (
  py -m venv venv
)

call venv\Scripts\activate

REM Dependencias mínimas
pip install --quiet rich pytest

echo.
echo ====== Lanzando EcoBot (consola) ======
echo.

py -m app.server

endlocal

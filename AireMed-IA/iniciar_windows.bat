@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Creando entorno virtual...
  py -3 -m venv .venv
  if errorlevel 1 python -m venv .venv
)
echo Instalando dependencias base...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
 echo Error instalando dependencias. Verifica internet y Python 3.10-3.12.
 pause
 exit /b 1
)
echo Abriendo dashboard en http://localhost:8501
.venv\Scripts\python.exe -m streamlit run app.py
pause

@echo off
REM Gera os executaveis (pasta dist\). Precisa de internet so para instalar o PyInstaller.
py -3.13 -m pip install pygame pyinstaller
py -3.13 -m PyInstaller --onefile --name servidor servidor.py
py -3.13 -m PyInstaller --onefile --name cliente cliente.py
py -3.13 -m PyInstaller --onefile --name monitor monitor.py
echo.
echo Executaveis em dist\servidor.exe, dist\cliente.exe e dist\monitor.exe
pause

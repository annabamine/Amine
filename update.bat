@echo off
cd /d "%~dp0"
git add .
git commit -m "Mise à jour automatique"
git push
pause
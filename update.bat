@echo off
cd /d "%~dp0"
git add valorisation.py requirements.txt manifest.json .gitignore
git commit -m "Mise a jour"
git push
pause
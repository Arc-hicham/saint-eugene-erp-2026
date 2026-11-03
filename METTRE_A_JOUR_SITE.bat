@echo off
title Mise a jour du Site GitHub Pages - Saint Eugene ERP 2026
set "PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI"
cd /d "%~dp0"

echo ======================================================================
echo   MISE A JOUR AUTOMATIQUE DU SITE WEB (GitHub Pages)
echo ======================================================================
echo.
set /p PASS="Entrez votre code d'acces actuel (Appuyez sur Entree pour 'SaintEugene2026') : "
if "%PASS%"=="" set "PASS=SaintEugene2026"

echo.
echo [1/2] Reconstruction et chiffrement de index.html...
python encrypt_web_portal.py "%PASS%"

echo.
echo [2/2] Envoi des modifications sur GitHub Pages...
git add -A
git commit -m "Update titles, configuration and data for Saint Eugene ERP 2026"
git push origin main

echo.
echo ======================================================================
echo   TERMINE ! Vos modifications seront visibles dans ~30 secondes sur :
echo   https://arc-hicham.github.io/saint-eugene-erp-2026/
echo ======================================================================
pause

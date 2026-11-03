@echo off
title Changer le Mot de Passe du Site Web - Saint Eugene ERP 2026
set "PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI"
cd /d "%~dp0"

echo ======================================================================
echo   MODIFICATION DU CODE D'ACCES PRIVE (GitHub Pages)
echo ======================================================================
echo.
set /p NEW_PASS="Entrez le nouveau code d'acces secret a partager : "
if "%NEW_PASS%"=="" (
    echo Operation annulee.
    pause
    exit /b 1
)

python encrypt_web_portal.py "%NEW_PASS%"
git add index.html
git commit -m "Update encrypted access portal password"
git pull --rebase origin main
git push origin main

echo.
echo ======================================================================
echo   Nouveau code d'acces "%NEW_PASS%" actif d'ici ~30 secondes sur :
echo   https://arc-hicham.github.io/saint-eugene-erp-2026/
echo ======================================================================
pause

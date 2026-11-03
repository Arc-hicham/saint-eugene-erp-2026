@echo off
title Publication GitHub - Saint Eugene ERP 2026
set "PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI"
cd /d "%~dp0"

echo ======================================================================
echo   PUBLICATION AUTOMATIQUE SUR GITHUB : saint-eugene-erp-2026
echo ======================================================================
echo.

gh auth status >nul 2>&1
if errorlevel 1 (
    echo [Etape 1/2] Connexion securisee a votre compte GitHub via le navigateur...
    echo   1. Appuyez sur ENTREE lorsqu'on vous le demande
    echo   2. Entrez le code a 8 caracteres affiche ci-dessous sur github.com/login/device
    echo.
    gh auth login --hostname github.com --git-protocol https --web
)

echo.
echo [Etape 2/2] Creation du depot "saint-eugene-erp-2026" et envoi du code (git push)...
gh repo create saint-eugene-erp-2026 --public --description "Mini-ERP Frappe v15 sur mesure - Hotel Saint Eugene 4* Alger (Exercice 2026 - DZD / SCF)" --source=. --remote=origin --push
if errorlevel 1 (
    git branch -M main
    git push -u origin main
)

echo.
echo ======================================================================
echo   TERMINE ! Ouverture de votre depot GitHub dans le navigateur...
echo ======================================================================
gh repo view --web
pause

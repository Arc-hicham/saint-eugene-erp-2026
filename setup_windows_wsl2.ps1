# ==============================================================================
# Script PowerShell 1-Clic (Windows 10/11) — Déploiement WSL2 + Frappe v15 + Saint Eugène
# Usage : Clic droit -> "Exécuter avec PowerShell (en tant qu'Administrateur)"
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "=== Déploiement Mini-ERP Hôtel Saint Eugène 4★ (Frappe v15 / WSL2) ===" -ForegroundColor Cyan

# 1. Vérification de la distribution Ubuntu sous WSL2
$distros = wsl --list --quiet 2>$null
if (-not ($distros -match "Ubuntu")) {
    Write-Host "[Étape 1/2] WSL2 / Ubuntu n'est pas encore installé sur ce poste Windows." -ForegroundColor Yellow
    Write-Host "Installation automatique de WSL2 + Ubuntu-22.04 (droits Administrateur requis)..." -ForegroundColor Yellow
    wsl --install -d Ubuntu-22.04
    Write-Host "IMPORTANT : Redémarrez Windows, créez votre utilisateur Ubuntu au premier lancement, puis relancez ce script !" -ForegroundColor Green
    exit 0
}

# 2. Conversion du chemin Windows vers /mnt/c/... dans WSL2
$WinPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$DriveLetter = $WinPath.Substring(0, 1).ToLower()
$RelPath = $WinPath.Substring(2).Replace("\", "/")
$WslAppPath = "/mnt/$DriveLetter$RelPath"

Write-Host "[Étape 2/2] Préparation des prérequis Frappe v15 (MariaDB 10.6, Redis, Node 18, wkhtmltopdf, Bench) dans Ubuntu WSL2..." -ForegroundColor Cyan

$BootstrapBash = @"
set -euo pipefail
sudo apt-get update -y
sudo apt-get install -y git python3-dev python3-venv python3-pip redis-server mariadb-server mariadb-client \
    libmariadb-dev pkg-config curl xvfb libfontconfig wkhtmltopdf build-essential

if ! command -v node >/dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
sudo npm install -g yarn

if ! command -v bench >/dev/null 2>&1; then
    pip3 install --user frappe-bench
    export PATH="`$HOME/.local/bin:`$PATH"
fi

sudo service mariadb start
sudo service redis-server start

rm -rf "`$HOME/saint_eugene_src"
cp -r "$WslAppPath" "`$HOME/saint_eugene_src"
chmod +x "`$HOME/saint_eugene_src/install_docker_wsl2.sh"
export PATH="`$HOME/.local/bin:`$PATH"
"`$HOME/saint_eugene_src/install_docker_wsl2.sh" "`$HOME/saint_eugene_src"
"@

wsl -d Ubuntu-22.04 -- bash -lc $BootstrapBash

Write-Host "==============================================================================" -ForegroundColor Green
Write-Host " Déploiement terminé ! Pour démarrer l'ERP :" -ForegroundColor Green
Write-Host "   wsl -d Ubuntu-22.04 -- bash -lc 'cd ~/frappe-bench-se && ~/.local/bin/bench start'" -ForegroundColor White
Write-Host " Puis ouvrez : http://sainteugene.localhost:8000" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Green

# Sync local repo with https://github.com/motormouthvis/poi-filter-testing
# Usage: from repo root, run:  .\scripts\sync.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "Pulling origin/main..."
git pull --ff-only origin main

Write-Host "Staging all changes..."
git add -A

$status = git status --porcelain
if (-not $status) {
    Write-Host "Already in sync - nothing to commit."
    exit 0
}

Write-Host "Committing:"
git status -sb
$msg = "Sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git commit -m $msg

Write-Host "Pushing to origin/main..."
git push origin main

Write-Host "Done. Local and GitHub are in sync."

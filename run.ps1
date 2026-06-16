# DuCO-Agent Runner Script for Windows
# Run this script to execute the full pipeline

$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

Write-Host "Starting DuCO-Agent pipeline..." -ForegroundColor Cyan
python main.py $args

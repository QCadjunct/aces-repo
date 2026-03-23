param(
    [ValidateSet("run", "edit")]
    [string]$Mode = "run",
    [int]$Port = 2718
)
$RepoRoot  = $PSScriptRoot
$MonitorPy = Join-Path $RepoRoot "ui\aces_monitor.py"
$Venv      = Join-Path $RepoRoot ".venv\Scripts\marimo.exe"

if (-not (Test-Path $MonitorPy)) {
    Write-Error "aces_monitor.py not found at: $MonitorPy"
    exit 1
}
if (-not (Test-Path $Venv)) {
    Write-Error "Marimo not found at: $Venv — run: uv sync"
    exit 1
}

$env:PYTHONPATH = $RepoRoot

Write-Host ""
Write-Host "  ACMS Monitor" -ForegroundColor Cyan
Write-Host "  Mind Over Metadata LLC -- Peter Heller" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Mode : $Mode" -ForegroundColor White
Write-Host "  Port : $Port" -ForegroundColor White
Write-Host "  URL  : http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host ""

if ($Mode -eq "edit") {
    Write-Host "  Starting in EDIT mode..." -ForegroundColor Yellow
    & $Venv edit $MonitorPy --port $Port
} else {
    Write-Host "  Starting in RUN mode..." -ForegroundColor Green
    & $Venv run $MonitorPy --port $Port
}

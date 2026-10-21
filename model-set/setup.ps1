# Local LLM Model Set - Windows setup (PowerShell)
#
# What this does, in order, with nothing hidden:
#   1. Checks Docker Desktop is installed and running.
#   2. Starts the hardened Ollama container (loopback only - see
#      docker-compose.yml).
#   3. Pulls the model bundle you chose (default: "starter" = Qwen3 4B).
#   4. Prints the installed digests so you can record / verify them.
#
# It never asks for admin rights, never changes firewall rules, and the
# only network traffic is model downloads from the official Ollama
# registry over TLS.
param(
    [string]$Bundle = "starter"
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is required. Install Docker Desktop first: https://docs.docker.com/desktop/setup/install/windows-install/"
    exit 1
}
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is installed but not running. Start Docker Desktop, then re-run .\setup.ps1"
    exit 1
}

Write-Host "==> Starting the local runtime (loopback only: 127.0.0.1:11434)"
docker compose up -d ollama

Write-Host "==> Waiting for the runtime to answer"
$ready = $false
foreach ($i in 1..30) {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3 | Out-Null
        $ready = $true; break
    } catch { Start-Sleep -Seconds 2 }
}
if (-not $ready) {
    Write-Host "Runtime did not come up. Check: docker compose logs ollama"
    exit 1
}

Write-Host "==> Pulling bundle: $Bundle"
$manifest = Get-Content "models.json" -Raw | ConvertFrom-Json
$bundles = $manifest.recommended_bundles
$ids = $bundles.$Bundle
if (-not $ids) {
    Write-Host "Unknown bundle '$Bundle'. Bundles: $($bundles.PSObject.Properties.Name -join ', ')"
    exit 1
}
foreach ($id in $ids) {
    $entry = $manifest.models | Where-Object { $_.id -eq $id }
    Write-Host "--> $($entry.display_name) ($($entry.ollama_tag))"
    docker exec local-llm-ollama ollama pull $entry.ollama_tag
    if ($LASTEXITCODE -ne 0) { Write-Host "Pull failed for $id"; exit 1 }
}

Write-Host ""
Write-Host "==> Installed models and digests (save these to verify later):"
python llm.py list

Write-Host ""
Write-Host "Done. Talk to your model:"
Write-Host '  python llm.py chat qwen3-4b "Write a haiku about local AI"'
Write-Host "Optional private chat UI (auth on, signup off, loopback only):"
Write-Host "  docker compose --profile ui up -d   then open http://127.0.0.1:3000"
Write-Host "Stop everything:  docker compose down"

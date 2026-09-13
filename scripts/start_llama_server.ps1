$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$server = Join-Path $root "third_party\llama-cpp\llama-server.exe"
$gguf = Join-Path $root "models\gguf\Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"
if (-not (Test-Path $server)) { throw "Missing $server" }
if (-not (Test-Path $gguf)) { throw "Missing $gguf — download GGUF first" }
Write-Host "Starting llama-server on 127.0.0.1:8080 ..."
Start-Process -FilePath $server -ArgumentList @(
  "-m", $gguf,
  "--host", "127.0.0.1",
  "--port", "8080",
  "-c", "2048",
  "-n", "256"
) -WorkingDirectory (Split-Path $server)
Write-Host "Health: http://127.0.0.1:8080/health"

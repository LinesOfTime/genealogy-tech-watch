#requires -Version 5.1
<#
.SYNOPSIS
  Isolated upstream integration baseline for G-MCP-01 on Windows.
  This does NOT execute T1-T7 and does NOT prove E3/E4.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\tools\run_gramps_baseline.ps1
#>
[CmdletBinding()]
param(
  [string]$Workspace = (Join-Path (Get-Location).Path "local-gramps-baseline"),
  [switch]$CleanupTestVolumes
)
$ErrorActionPreference = "Stop"
$pin = "9ce862da7543ce09ef7683330fce049b1c7ff24b"
$source = "https://github.com/Genealogy-MCP/gramps-mcp.git"
$workspaceFull = [IO.Path]::GetFullPath($Workspace)
$checkout = Join-Path $workspaceFull "gramps-mcp"
$logs = Join-Path $workspaceFull "logs"
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$record = Join-Path $logs ("baseline-" + $timestamp + ".txt")
$pinFile = Join-Path $logs ("baseline-" + $timestamp + "-metadata.json")
$started = (Get-Date).ToUniversalTime().ToString("o")
$exitCode = 1
$stackStarted = $false
$envNames = @("COMPOSE_PROJECT_NAME","GRAMPS_API_URL","GRAMPS_USERNAME","GRAMPS_PASSWORD","GRAMPS_TREE_ID","REQUIRE_INTEGRATION")
$oldEnv = @{}
foreach ($name in $envNames) { $oldEnv[$name] = [Environment]::GetEnvironmentVariable($name, "Process") }
# Upstream seed and pytest discover the stack through COMPOSE_PROJECT_NAME.
$env:COMPOSE_PROJECT_NAME = "gtw-gramps-baseline"
# Never accidentally execute tests against an inherited, potentially live Gramps instance.
foreach ($name in @("GRAMPS_API_URL","GRAMPS_USERNAME","GRAMPS_PASSWORD","GRAMPS_TREE_ID")) {
  [Environment]::SetEnvironmentVariable($name, $null, "Process")
}
$env:REQUIRE_INTEGRATION = "1"
function HasCommand($name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }
function InvokeChecked([string]$label, [string[]]$argv) {
  Write-Host "== $label =="
  $command = $argv[0]
  $arguments = @($argv[1..($argv.Count-1)])
  & $command @arguments 2>&1 | Out-File -FilePath $record -Append -Encoding utf8
  if ($LASTEXITCODE -ne 0) { throw "$label failed (exit code $LASTEXITCODE); see $record" }
}
try {
  foreach ($cmd in @("git","docker","uv")) {
    if (-not (HasCommand $cmd)) { throw "Missing prerequisite: $cmd (install and put on PATH)" }
  }
  InvokeChecked "Docker Engine" @("docker","info","--format","{{.ServerVersion}}")
  InvokeChecked "Docker Compose" @("docker","compose","version")
  InvokeChecked "uv version" @("uv","--version")
  if (-not (Test-Path $checkout)) {
    InvokeChecked "Clone upstream mirror" @("git","clone","--no-checkout",$source,$checkout)
  }
  if (-not (Test-Path (Join-Path $checkout ".git"))) {
    throw "Workspace path exists but is not a Git checkout: $checkout"
  }
  Push-Location $checkout
  try {
    InvokeChecked "Fetch pinned upstream commit" @("git","fetch","origin",$pin)
    InvokeChecked "Checkout pinned commit" @("git","checkout","--detach",$pin)
    $actual = (& git rev-parse HEAD).Trim()
    if ($actual -ne $pin) { throw "Commit mismatch: $actual" }
    if ((& git status --porcelain).Count -gt 0) { throw "Checkout contains local changes; aborting" }
    InvokeChecked "Prepare Python dependencies" @("uv","sync","--group","dev","--frozen")
    InvokeChecked "Start isolated Gramps Web test stack" @("docker","compose","-p","gtw-gramps-baseline","-f","docker-compose.test.yml","up","-d","--wait")
    $stackStarted = $true
    InvokeChecked "Seed upstream test database" @("uv","run","--no-sync","python","scripts/seed_test_db.py","--skip-if-seeded")
    InvokeChecked "Run upstream integration tests" @("uv","run","--no-sync","pytest","-m","integration","--no-cov","-q")
    $exitCode = 0
  } finally {
    Pop-Location
  }
} catch {
  "ERROR: $($_.Exception.Message)" | Tee-Object -FilePath $record -Append
  $exitCode = 1
} finally {
  @{
    compose_project = "gtw-gramps-baseline"
    require_integration = $true
    inherited_gramps_credentials_ignored = $true
    upstream_repo = $source
    upstream_commit = $pin
    started_at_utc = $started
    finished_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    outcome = $(if ($exitCode -eq 0) {"upstream_integration_tests_passed"} else {"failed_or_not_run"})
    evaluated_project = "genealogy-mcp/gramps-mcp"
    tests_are = "upstream integration suite, not independent G-MCP-01 T1-T7"
    log = $record
  } | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $pinFile
  foreach ($name in $envNames) { [Environment]::SetEnvironmentVariable($name, $oldEnv[$name], "Process") }
  Write-Host "Log: $record"
  Write-Host "Metadata: $pinFile"
  if ($CleanupTestVolumes -and $stackStarted) {
    Push-Location $checkout
    try { & docker compose -p gtw-gramps-baseline -f docker-compose.test.yml down -v 2>&1 | Out-File -FilePath $record -Append -Encoding utf8 }
    finally { Pop-Location }
    Write-Host "CAUTION: only the isolated upstream test stack volumes were removed."
  } else {
    Write-Host "Test volumes preserved. Use -CleanupTestVolumes to remove ONLY this test stack's volumes after verifying project identity."
  }
}
exit $exitCode

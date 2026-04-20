param(
  [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$appsRoot = Join-Path $repo 'mobile/apps'

if (-not (Test-Path $appsRoot)) {
  throw "Apps folder not found: $appsRoot"
}

$pnpm = Get-Command pnpm -ErrorAction SilentlyContinue
if (-not $pnpm) {
  throw 'pnpm is required. Install with: npm i -g pnpm'
}

$apps = Get-ChildItem $appsRoot -Directory | Sort-Object Name
$results = @()

foreach ($app in $apps) {
  $appPath = $app.FullName
  Write-Host "\n=== $($app.Name) ===" -ForegroundColor Cyan
  $status = 'PASS'
  $note = 'lint+typecheck ok'

  try {
    if (-not $SkipInstall) {
      pnpm --dir $appPath install --frozen-lockfile=false | Out-Host
      if ($LASTEXITCODE -ne 0) { throw "install failed with exit code $LASTEXITCODE" }
    }
    pnpm --dir $appPath run lint | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "lint failed with exit code $LASTEXITCODE" }
    pnpm --dir $appPath run typecheck | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "typecheck failed with exit code $LASTEXITCODE" }
  }
  catch {
    $status = 'FAIL'
    $note = $_.Exception.Message
  }

  $results += [PSCustomObject]@{
    app = $app.Name
    status = $status
    details = $note
  }
}

Write-Host "\n=== Mobile Matrix Summary ===" -ForegroundColor Yellow
$results | Format-Table -AutoSize

$failed = $results | Where-Object { $_.status -eq 'FAIL' }
if ($failed.Count -gt 0) {
  exit 1
}

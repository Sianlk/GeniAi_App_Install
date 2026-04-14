param(
  [string]$SourceFile = '.secrets.local.env',
  [string]$TargetFile = '.env'
)

$required = @(
  'DIGITALOCEAN_ACCESS_TOKEN',
  'DIGITALOCEAN_APP_ID',
  'OPENAI_API_KEY',
  'GITHUB_TOKEN',
  'SNYK_TOKEN',
  'STRIPE_SECRET_KEY',
  'STRIPE_WEBHOOK_SECRET'
)

$placeholder = '(?i)xxx|\.\.\.|changeme|replace_me|token_here|app-xxxx|^sk-xxx$|^ghp_xxx$|^snyk_xxx$|^dop_v1_xxx$|<|>'

function Parse-KeyValueFile([string]$path) {
  $map = @{}
  if (-not (Test-Path $path)) { return $map }
  Get-Content $path | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $idx = $_.IndexOf('=')
    if ($idx -le 0) { return }
    $k = $_.Substring(0, $idx).Trim()
    $v = $_.Substring($idx + 1).Trim()
    $map[$k] = $v
  }
  return $map
}

$sourceMap = Parse-KeyValueFile $SourceFile
$targetLines = if (Test-Path $TargetFile) { Get-Content $TargetFile } else { @() }
$updated = 0
$found = 0

foreach ($key in $required) {
  $candidate = $null

  if ($sourceMap.ContainsKey($key) -and -not [string]::IsNullOrWhiteSpace($sourceMap[$key])) {
    $candidate = $sourceMap[$key]
  }

  if ([string]::IsNullOrWhiteSpace($candidate)) {
    $candidate = [Environment]::GetEnvironmentVariable($key, 'Process')
  }
  if ([string]::IsNullOrWhiteSpace($candidate)) {
    $candidate = [Environment]::GetEnvironmentVariable($key, 'User')
  }
  if ([string]::IsNullOrWhiteSpace($candidate)) {
    $candidate = [Environment]::GetEnvironmentVariable($key, 'Machine')
  }

  if ([string]::IsNullOrWhiteSpace($candidate) -or $candidate -match $placeholder) {
    continue
  }

  $found++
  $line = "$key=$candidate"
  $matched = $false

  for ($i = 0; $i -lt $targetLines.Count; $i++) {
    if ($targetLines[$i] -match ('^' + [regex]::Escape($key) + '=')) {
      $targetLines[$i] = $line
      $matched = $true
      $updated++
      break
    }
  }

  if (-not $matched) {
    $targetLines += $line
    $updated++
  }

  [Environment]::SetEnvironmentVariable($key, $candidate, 'Process')
}

Set-Content -Path $TargetFile -Value $targetLines -NoNewline:$false
Write-Output ("Secrets imported. candidates_found={0} lines_updated={1}" -f $found, $updated)

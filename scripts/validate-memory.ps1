#Requires -Version 5.1
# Validates Tier-0 shared memory. Exit 1 on fail.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$fails = @()
foreach ($f in @('MEMORY.md','docs/agent-memory/claims/board.md','docs/agent-memory/handoffs/active','docs/agent-memory/topics')) {
  if (-not (Test-Path -LiteralPath (Join-Path $root $f))) { $fails += "missing: $f" }
}
if ((Get-Content -LiteralPath (Join-Path $root 'MEMORY.md') -Raw) -match '@\w[\w/.-]*\.md') { $fails += 'MEMORY.md must be flat (no @-imports)' }
if ($fails.Count -gt 0) { $fails | ForEach-Object { Write-Host "FAIL: $_" }; exit 1 }
Write-Host 'memory OK'

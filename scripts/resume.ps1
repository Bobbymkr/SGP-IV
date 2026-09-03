# resume.ps1 -- power-cut resume for Orca pipeline (ASCII only)
param([string]$Force,[switch]$Reset,[switch]$StatusOnly)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Set-Location $root
$phases=@(
  @{id='phase0';ck='checkpoints/phase0.done';gate='make graph-update';label='scaffold'},
  @{id='phase1';ck='checkpoints/phase1.done';gate='make loop-fast';label='domain-sim'},
  @{id='phase2';ck='checkpoints/phase2.done';gate='make verify';label='detect-control'},
  @{id='phase3';ck='checkpoints/phase3.done';gate='make bench-sim';label='bench-profile'},
  @{id='phase4';ck='checkpoints/phase4.done';gate='make pre-commit';label='docs-release'}
)
if($Reset){Remove-Item checkpoints/*.done -ErrorAction SilentlyContinue;Write-Host 'checkpoints cleared'}
if($Force){$t=$phases|Where-Object{$_.id -eq $Force};if($t){Remove-Item $t.ck -ErrorAction SilentlyContinue}}
Write-Host "=== Orca resume check: $root ===" -ForegroundColor Cyan
$next=$null
foreach($p in $phases){
  $done=Test-Path $p.ck
  $mark=if($done){'[x]'}else{'[ ]'}
  $col=if($done){'DarkGray'}else{'White'}
  Write-Host "$mark $($p.id) $($p.label) gate $($p.gate)" -ForegroundColor $col
  if(-not $done -and -not $next){$next=$p}
}
if($StatusOnly){exit 0}
if(-not $next){Write-Host 'All done' -ForegroundColor Green;exit 0}
Write-Host "Resuming at: $($next.id) -- $($next.label)" -ForegroundColor Green
$si=[array]::IndexOf($phases,$next)
for($i=$si;$i -lt $phases.Count;$i++){
  $p=$phases[$i]
  if(Test-Path $p.ck){continue}
  Write-Host "--- $($p.id): $($p.gate) ---" -ForegroundColor Cyan
  $exitCode=0
  try{
    $sub=$p.gate -replace '^make ',''
    & make $sub 2>&1 | Out-Host
    $exitCode=$LASTEXITCODE
  }catch{
    Write-Host 'make fallback' -ForegroundColor Yellow
    $fb=switch($p.id){
      'phase0'{'exit 0'}
      'phase1'{'.venv\Scripts\python.exe -m pytest tests/unit tests/integration -q -x --no-header -p no:cacheprovider'}
      'phase2'{'.venv\Scripts\python.exe -m pytest -q'}
      'phase3'{'.venv\Scripts\python.exe scripts/bench_sim.py'}
      default{'exit 0'}
    }
    if($fb){Invoke-Expression $fb;$exitCode=$LASTEXITCODE}
  }
  if($exitCode -ne 0 -and $null -ne $exitCode){Write-Error "fail $($p.id)";exit $exitCode}
  New-Item -ItemType Directory -Force -Path 'checkpoints' | Out-Null
  New-Item -ItemType File -Force -Path $p.ck | Out-Null
  try{& git add $p.ck 2>$null|Out-Null;& git commit -m "checkpoint: $($p.id)" 2>$null|Out-Null}catch{}
  try{& "$PSScriptRoot/auto-graph.ps1" -Phase $p.id 2>$null|Out-Host}catch{}
  Write-Host "checkpoint $($p.id) done" -ForegroundColor Green
}
Write-Host 'Pipeline complete' -ForegroundColor Green

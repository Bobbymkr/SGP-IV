# auto-graph.ps1 -- hands-off graph engineering + vault mirror (ASCII)
param([string]$Phase='manual')
$root=Split-Path -Parent $PSScriptRoot
Set-Location $root
try{
  if(Get-Command graphify -ErrorAction SilentlyContinue){graphify update . 2>&1|Out-Null}
  elseif(Test-Path "$root\.opencode\plugins\graphify.js"){npx --yes graphify update . 2>&1|Out-Null}
}catch{}
$date=Get-Date -Format 'yyyy-MM-dd'
$vaultDay="vault/$date.md"
New-Item -ItemType Directory -Force -Path 'vault'|Out-Null
$line="- $Phase at $(Get-Date -Format 'HH:mm:ss')"
if(-not (Test-Path $vaultDay)){
  $h="# $date -- $Phase"
  $b="- checkpoint: $Phase"
  $m1="- graph: graphify-out/graph.json"
  $cps=''
  try{$cps=(Get-ChildItem checkpoints/*.done -ErrorAction SilentlyContinue|ForEach-Object{$_.Name}|Join-String -Separator ', ')}catch{$cps=''}
  Set-Content -Path $vaultDay -Value "$h`n`n$b`n$m1`n- checkpoints: $cps`n"
}else{
  Add-Content -Path $vaultDay -Value $line
}
try{
  if(Get-Command graph-mem -ErrorAction SilentlyContinue){
    $obs="checkpoint $Phase at $(Get-Date -Format o)"
    graph-mem add-observation --text $obs 2>$null|Out-Null
  }
}catch{}
try{& git add vault/ graphify-out/ 2>$null|Out-Null}catch{}
Write-Host "auto-graph: $Phase -> vault/$date.md" -ForegroundColor DarkGray

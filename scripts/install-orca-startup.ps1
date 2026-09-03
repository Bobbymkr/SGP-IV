# install-orca-startup.ps1 -- auto-resume Orca on Windows login (power-cut safe)
param([switch]$Uninstall)
$project="C:\Users\Admin\OneDrive\Desktop\IDEA\Adaptive-Traffic-Signal-Timer"
$startup=[Environment]::GetFolderPath("Startup")
$lnkPath=Join-Path $startup "Orca-ATST.lnk"
$orcaExe="C:\Users\Admin\AppData\Local\Programs\Orca\resources\bin\orca.exe"
if(-not (Test-Path $orcaExe)){$orcaExe=(Get-Command orca -ErrorAction SilentlyContinue).Source}
if($Uninstall){Remove-Item $lnkPath -ErrorAction SilentlyContinue;Write-Host "removed $lnkPath" -ForegroundColor Yellow;exit 0}
if(-not $orcaExe){Write-Error "orca not found";exit 1}
$WshShell=New-Object -ComObject WScript.Shell
$lnk=$WshShell.CreateShortcut($lnkPath)
$lnk.TargetPath="powershell.exe"
$lnk.Arguments="-NoProfile -WindowStyle Hidden -Command ""Start-Sleep 5; & '$orcaExe' open '$project' --restore; Start-Sleep 8; & '$project\scripts\resume.ps1'"""
$lnk.WorkingDirectory=$project
$lnk.Description="Orca ATST autobuild resume after power cut"
$lnk.Save()
Write-Host "installed $lnkPath" -ForegroundColor Green
Write-Host "  -> $orcaExe open $project --restore + resume.ps1" -ForegroundColor Gray

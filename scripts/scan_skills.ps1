#requires -Version 5.1
<#
.SYNOPSIS
  Deep scan of agent skills with NVIDIA SkillSpector: batching, summary, gate.

.DESCRIPTION
  skillspector scan accepts ONE input path; --recursive only sees immediate
  subdirectories; large collections hit its aggregate fail-closed ceiling
  (exit 2, findings omitted). This script enumerates every directory containing
  a SKILL.md under each root (any depth; symlink/junction targets skipped to
  avoid duplicates), scans each skill individually, aggregates a summary and
  applies the gate.

  Modes:
    scan (default)       Gate: exit 1 if any non-suppressed issue severity is
                         in -FailSeverities (default CRITICAL/HIGH), or on
                         parse failure (see -FailOnIncomplete).
    -GenerateBaseline    Same pass, no gating; afterwards writes -Baseline
                         (JSON) with fingerprints of every current finding =
                         the "accepted findings" snapshot. Commit the file;
                         future scans then fail only on NEW findings.
    -ReportOnly          Print summary, never gate (exit 0).

  Suppressed findings (--baseline) are dropped by skillspector BEFORE scoring,
  so risk_score/severity reflect only non-suppressed findings.

  Requires: skillspector on PATH:
    uv tool install git+https://github.com/NVIDIA/SkillSpector.git
  Run from the repository root.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/scan_skills.ps1
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/scan_skills.ps1 -GenerateBaseline
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/scan_skills.ps1 -Paths "$HOME/.agents/skills" -ReportOnly
#>
param(
  [string[]]$Paths = @('.agents/skills', '.claude/skills'),
  [string]$Baseline = '.skillspector-baseline.json',
  [string[]]$FailSeverities = @('CRITICAL', 'HIGH'),
  [switch]$GenerateBaseline,
  [switch]$ReportOnly,
  [switch]$FailOnIncomplete,
  [string]$Skillspector = 'skillspector',
  [string]$Reason = 'Accepted finding (auto-generated baseline)'
)

$ErrorActionPreference = 'Stop'

# powershell -File may deliver 'a,b' as a single string; normalize.
if ($Paths.Count -eq 1 -and $Paths[0] -match ',') { $Paths = $Paths[0] -split ',' }
$Paths = @($Paths | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($FailSeverities.Count -eq 1 -and $FailSeverities[0] -match ',') {
  $FailSeverities = $FailSeverities[0] -split ','
}
$FailSeverities = @($FailSeverities | ForEach-Object { $_.Trim().ToUpper() } | Where-Object { $_ })

# Silence per-invocation "Skipping analyzer ..." WARNING spam (ERROR keeps real errors).
$env:SKILLSPECTOR_LOG_LEVEL = 'ERROR'

if (-not (Get-Command $Skillspector -ErrorAction SilentlyContinue)) {
  Write-Output 'GATE: ERROR - skillspector not found on PATH.'
  Write-Output 'Install: uv tool install git+https://github.com/NVIDIA/SkillSpector.git'
  exit 2
}

# ---- enumerate skill dirs (any depth; skip reparse points to avoid dupes) ----
$skillDirs = New-Object System.Collections.Generic.List[string]
foreach ($root in $Paths) {
  if (-not (Test-Path $root)) { Write-Warning "path not found: $root"; continue }
  $full = (Resolve-Path $root).Path
  if (Test-Path (Join-Path $full 'SKILL.md')) { $skillDirs.Add($full); continue }
  $dirs = Get-ChildItem -Path $full -Recurse -Directory -ErrorAction SilentlyContinue |
    Where-Object {
      (-not ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) -and
      (Test-Path (Join-Path $_.FullName 'SKILL.md'))
    }
  foreach ($d in $dirs) { $skillDirs.Add($d.FullName) }
}
$skillDirs = @($skillDirs | Sort-Object -Unique)
if ($skillDirs.Count -eq 0) { Write-Output 'No skills found to scan.'; exit 0 }

$useBaseline = (-not $GenerateBaseline) -and (Test-Path $Baseline)
Write-Output ("Scanning {0} skill(s) under: {1}" -f $skillDirs.Count, ($Paths -join ', '))
if ($useBaseline) { Write-Output ("Baseline: {0}" -f $Baseline) }

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('ss-scan-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

# ---- per-skill scan ----
$rows = New-Object System.Collections.Generic.List[object]
$mergedFps = New-Object System.Collections.Generic.List[object]
$mergedSeen = @{}
$infraFails = 0
$idx = 0
foreach ($dir in $skillDirs) {
  $idx++
  $name = Split-Path $dir -Leaf
  if ($GenerateBaseline) {
    # The official generator computes its own suppression hashes (they differ
    # from issue.match_fingerprint), so baseline mode runs `skillspector
    # baseline` per skill and merges the per-skill JSON files.
    $bfile = Join-Path $tempRoot ("b{0}.json" -f $idx)
    & $Skillspector baseline $dir -o $bfile --no-llm --reason $Reason | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $bfile)) {
      $infraFails++
      Write-Output ("  [{0}/{1}] {2} - baseline generation FAILED (exit {3})" -f $idx, $skillDirs.Count, $name, $LASTEXITCODE)
      continue
    }
    $b = $null
    try { $b = Get-Content $bfile -Raw -ErrorAction Stop | ConvertFrom-Json } catch { $b = $null }
    $added = 0
    if ($b) {
      foreach ($f in @(@($b.fingerprints) | Where-Object { $_ })) {
        $key = ('' + $f.hash) + '|' + ('' + $f.rule_id) + '|' + ('' + $f.file)
        if ($mergedSeen.ContainsKey($key)) { continue }
        $mergedSeen[$key] = $true
        $mergedFps.Add([pscustomobject]@{ hash = [string]$f.hash; rule_id = [string]$f.rule_id; file = [string]$f.file; reason = [string]$f.reason })
        $added++
      }
    }
    Write-Output ("  [{0}/{1}] {2}: baseline (+{3} fingerprint(s))" -f $idx, $skillDirs.Count, $name, $added)
    continue
  }
  $out = Join-Path $tempRoot ("r{0}.json" -f $idx)
  if ($useBaseline) {
    & $Skillspector scan $dir --no-llm --baseline $Baseline --format json --output $out | Out-Null
  } else {
    & $Skillspector scan $dir --no-llm --format json --output $out | Out-Null
  }
  $code = $LASTEXITCODE

  $parsed = $null
  try { $parsed = Get-Content $out -Raw -ErrorAction Stop | ConvertFrom-Json } catch { $parsed = $null }

  $entries = @()
  if ($parsed -and $parsed.PSObject.Properties['skills'] -and $parsed.skills) {
    $entries = @($parsed.skills | Where-Object { $_ })
  }
  elseif ($parsed -and ($parsed.PSObject.Properties['risk_assessment'] -or $parsed.PSObject.Properties['risk_score'])) {
    $entries = @($parsed)
  }

  if (-not $entries) {
    $infraFails++
    $rows.Add([pscustomobject]@{ Name = $name; Dir = $dir; Score = '-'; Sev = 'PARSE_FAIL'; Max = '-'; Ok = $false; Exe = '-'; Counts = '-'; Suppressed = 0; Issues = @() })
    Write-Output ("  [{0}/{1}] {2} - NO OUTPUT (exit {3})" -f $idx, $skillDirs.Count, $name, $code)
    continue
  }
  foreach ($e in $entries) {
    # Normalize across output shapes: multi-skill entries carry top-level
    # name/risk_score/risk_severity; single-skill reports nest them under
    # skill.name and risk_assessment.score/severity.
    $ra = $e.risk_assessment
    $sName = if ($e.skill -and $e.skill.name) { $e.skill.name } elseif ($e.name) { $e.name } else { $name }
    $sScore = if ($ra -and $null -ne $ra.score) { $ra.score } elseif ($e.PSObject.Properties['risk_score']) { $e.risk_score } else { '-' }
    $sSev = if ($ra -and $ra.severity) { $ra.severity } elseif ($e.PSObject.Properties['risk_severity']) { $e.risk_severity } else { '-' }
    $issues = @(@($e.issues) | Where-Object { $_ })
    $counts = $issues | Group-Object severity | ForEach-Object { '{0}:{1}' -f $_.Name, $_.Count }
    $rows.Add([pscustomobject]@{
      Name = $sName; Dir = $dir
      Score = $sScore; Sev = $sSev
      Max = if ($ra) { $ra.max_issue_severity } else { '-' }
      Ok = [bool]$e.execution_successful
      Exe = [bool]$e.metadata.has_executable_scripts
      Counts = ($counts -join ',')
      Suppressed = $e.suppressed_count
      Issues = $issues
    })
    Write-Output ("  [{0}/{1}] {2}: {3}/100 ({4})" -f $idx, $skillDirs.Count, $sName, $sScore, $sSev)
  }
}

# ---- summary + gate ----
Write-Output ''
Write-Output ("{0,-32} {1,5} {2,-9} {3,-7} {4,-3} {5,-3} {6,-26} {7,4}" -f 'skill', 'score', 'severity', 'max', 'ok', 'exe', 'issues(non-suppr)', 'sup')
$breaches = New-Object System.Collections.Generic.List[object]
foreach ($r in ($rows | Sort-Object Name)) {
  Write-Output ("{0,-32} {1,5} {2,-9} {3,-7} {4,-3} {5,-3} {6,-26} {7,4}" -f `
    $r.Name, $r.Score, $r.Sev, $r.Max, $(if ($r.Ok) { 'Y' } else { 'N' }), $(if ($r.Exe) { 'Y' } else { 'N' }), $r.Counts, $r.Suppressed)
  if ($ReportOnly -or $GenerateBaseline) { continue }
  foreach ($i in $r.Issues) {
    $s = ('' + $i.severity).ToUpper()
    if ($FailSeverities -contains $s) {
      $breaches.Add([pscustomobject]@{ Skill = $r.Name; Id = $i.id; Sev = $s; What = [string]$i.finding; Where = ('' + $i.location.file + ':' + $i.location.line) })
    }
  }
  if ($r.Sev -eq 'PARSE_FAIL') {
    $breaches.Add([pscustomobject]@{ Skill = $r.Name; Id = 'NO_OUTPUT'; Sev = 'HIGH'; What = 'scan produced no parsable output (fail-closed)'; Where = $r.Dir })
  }
  if ($FailOnIncomplete -and -not $r.Ok) {
    $breaches.Add([pscustomobject]@{ Skill = $r.Name; Id = 'INCOMPLETE'; Sev = 'HIGH'; What = 'analysis incomplete/failed'; Where = $r.Dir })
  }
}

# ---- baseline write (merged official per-skill baselines) ----
if ($GenerateBaseline) {
  $vout = (& $Skillspector --version) -join ' '
  $sv = if ($vout -match '(\d+\.\d+\.\d+)') { $Matches[1] } else { 'unknown' }
  # NB: PS 5.1 throws "Argument types do not match" when @($list) is used
  # inside an [ordered]@{} literal - build via indexer with a plain object[].
  $baselineObj = New-Object System.Collections.Specialized.OrderedDictionary
  $baselineObj['version'] = 2
  $baselineObj['scanner_version'] = $sv
  $baselineObj['rules'] = @()
  $baselineObj['fingerprints'] = @($mergedFps.ToArray())
  $baselineObj | ConvertTo-Json -Depth 6 | Set-Content -Path $Baseline -Encoding UTF8
  Write-Output ("Baseline written: {0} ({1} fingerprint(s))" -f $Baseline, $mergedFps.Count)
}

Write-Output ("(per-skill JSON reports: {0})" -f $tempRoot)

if ($GenerateBaseline -or $ReportOnly) { exit 0 }
if ($infraFails -gt 0) { Write-Output ("INFRA: {0} skill(s) failed to produce output." -f $infraFails) }
if ($breaches.Count -gt 0) {
  Write-Output ''
  Write-Output ('GATE: FAIL - {0} non-suppressed finding(s) at/above {1}' -f $breaches.Count, ($FailSeverities -join '/'))
  foreach ($b in $breaches) {
    Write-Output ("  [{0}] {1} {2}: {3} ({4})" -f $b.Sev, $b.Skill, $b.Id, $b.What, $b.Where)
  }
  Write-Output 'To accept reviewed findings, refresh: powershell -File scripts/scan_skills.ps1 -GenerateBaseline'
  exit 1
}
Write-Output 'GATE: PASS'
exit 0

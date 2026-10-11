[CmdletBinding()]
param(
    [string]$SkillPath = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$expected = [ordered]@{
    'core-anchors.json' = 48
    'verified-lexicon.json' = 132
    'expansion-lexicon.json' = 288
}
$allIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$failures = [System.Collections.Generic.List[string]]::new()
$total = 0

foreach ($item in $expected.GetEnumerator()) {
    $path = Join-Path $SkillPath (Join-Path 'references' $item.Key)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $failures.Add("Missing lexicon: $($item.Key)")
        continue
    }
    $doc = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    $count = @($doc.entries).Count
    if ($count -ne $item.Value) {
        $failures.Add("$($item.Key) expected $($item.Value) entries but found $count")
    }
    foreach ($entry in @($doc.entries)) {
        if ([string]::IsNullOrWhiteSpace($entry.id) -or [string]::IsNullOrWhiteSpace($entry.zh) -or [string]::IsNullOrWhiteSpace($entry.en)) {
            $failures.Add("Incomplete entry in $($item.Key)")
            continue
        }
        if (-not $allIds.Add([string]$entry.id)) {
            $failures.Add("Duplicate entry id: $($entry.id)")
        }
    }
    $total += $count
}

$presetPath = Join-Path $SkillPath 'references\scene-presets.json'
if (-not (Test-Path -LiteralPath $presetPath -PathType Leaf)) {
    $failures.Add('Missing scene-presets.json')
} else {
    $presets = Get-Content -LiteralPath $presetPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (@($presets.presets).Count -lt 24) {
        $failures.Add('Scene preset library must contain at least 24 presets')
    }
}

if ($total -ne 468) {
    $failures.Add("Expected 468 total lexicon entries but found $total")
}

if ($failures.Count -gt 0) {
    Write-Output 'STATUS=FAIL'
    $failures | ForEach-Object { Write-Output "ERROR=$_" }
    exit 1
}

Write-Output 'STATUS=PASS'
Write-Output "LEXICON_TOTAL=$total"
Write-Output "UNIQUE_IDS=$($allIds.Count)"
Write-Output "SCENE_PRESETS=$(@($presets.presets).Count)"
exit 0

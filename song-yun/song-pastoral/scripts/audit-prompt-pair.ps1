[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$MidjourneyPromptPath,

    [Parameter(Mandatory = $true)]
    [string]$ImageGenPromptPath
)

$ErrorActionPreference = 'Stop'
$failures = [System.Collections.Generic.List[string]]::new()

foreach ($path in @($MidjourneyPromptPath, $ImageGenPromptPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $failures.Add("Missing file: $path")
    }
}

if ($failures.Count -eq 0) {
    $mj = (Get-Content -LiteralPath $MidjourneyPromptPath -Raw -Encoding UTF8).Trim()
    $ig = (Get-Content -LiteralPath $ImageGenPromptPath -Raw -Encoding UTF8).Trim()

    if ($mj -notmatch '(?s)--v 8\.2$') {
        $failures.Add('Midjourney prompt must end exactly with --v 8.2')
    }
    if ($mj -notmatch '--ar\s+\d+:\d+') {
        $failures.Add('Midjourney prompt is missing an aspect-ratio parameter')
    }
    if ($mj -match '(?i)\b(masterpiece|best quality|8k|ultra[- ]?detailed)\b') {
        $failures.Add('Midjourney prompt contains generic quality filler')
    }
    if ($mj -notmatch '(?i)(rice-white|moss-green|whitewashed|weathered timber|Song-style)') {
        $failures.Add('Midjourney prompt does not expose a recognizable Song-pastoral anchor')
    }
    if ($ig -match '--(?:ar|s|v|no|raw|seed|sref)\b') {
        $failures.Add('ImageGen prompt contains Midjourney syntax')
    }
    # Keep the script ASCII-safe for Windows PowerShell 5.1, which may parse
    # UTF-8-without-BOM source using the active ANSI code page.
    $imageGenStyleAnchors = @(
        (-join @([char]0x7C73, [char]0x767D)),
        (-join @([char]0x82D4, [char]0x7EFF)),
        (-join @([char]0x9EDB, [char]0x7EFF)),
        (-join @([char]0x767D, [char]0x7C89, [char]0x5899)),
        (-join @([char]0x5B8B, [char]0x5F0F)),
        (-join @([char]0x5B8B, [char]0x97F5))
    )
    $hasImageGenStyleAnchor = $false
    foreach ($anchor in $imageGenStyleAnchors) {
        if ($ig.Contains($anchor)) {
            $hasImageGenStyleAnchor = $true
            break
        }
    }
    if (-not $hasImageGenStyleAnchor) {
        $failures.Add('ImageGen prompt does not expose a recognizable Song-pastoral anchor')
    }
    if ([string]::IsNullOrWhiteSpace($mj) -or [string]::IsNullOrWhiteSpace($ig)) {
        $failures.Add('One or both prompt files are empty')
    }
}

if ($failures.Count -gt 0) {
    Write-Output 'STATUS=FAIL'
    $failures | ForEach-Object { Write-Output "ERROR=$_" }
    exit 1
}

Write-Output 'STATUS=PASS'
Write-Output 'MJ_VERSION_END=PASS'
Write-Output 'MJ_PARAMETER_BOUNDARY=PASS'
Write-Output 'IMAGEGEN_SYNTAX_BOUNDARY=PASS'
Write-Output 'STYLE_ANCHOR_CHECK=PASS'
exit 0

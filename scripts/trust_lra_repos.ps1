<#
.SYNOPSIS
Trust local lra-* Git repositories for Git's safe.directory check.

.DESCRIPTION
Adds each Git repository matching lra-* under F:\repos to the current user's
global Git safe.directory list. This is useful when commands run under a
sandbox or alternate Windows account but the repositories are owned by your
normal account.

Use -DryRun or PowerShell's built-in -WhatIf to preview changes.
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string] $Root = "F:\repos",
    [string] $Pattern = "lra-*",
    [switch] $DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Convert-ToGitPath {
    param([Parameter(Mandatory = $true)][string] $Path)
    return $Path.Replace("\", "/")
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git was not found on PATH."
}

$resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
$existingSafeDirectories = @(
    git config --global --get-all safe.directory 2>$null
) | ForEach-Object { $_.Trim() } | Where-Object { $_ }

$repos = Get-ChildItem -LiteralPath $resolvedRoot -Directory -Filter $Pattern |
    Sort-Object -Property FullName

if (-not $repos) {
    Write-Host "No directories matching '$Pattern' found under $resolvedRoot."
    exit 0
}

$added = 0
$alreadyTrusted = 0
$skipped = 0

foreach ($repo in $repos) {
    $gitMarker = Join-Path -Path $repo.FullName -ChildPath ".git"

    if (-not (Test-Path -LiteralPath $gitMarker)) {
        Write-Host "Skipping non-Git directory: $($repo.FullName)"
        $skipped++
        continue
    }

    $safePath = Convert-ToGitPath -Path $repo.FullName

    if ($existingSafeDirectories -contains $safePath) {
        Write-Host "Already trusted: $safePath"
        $alreadyTrusted++
        continue
    }

    if ($DryRun) {
        Write-Host "Would trust: $safePath"
        continue
    }

    if ($PSCmdlet.ShouldProcess($safePath, "git config --global --add safe.directory")) {
        git config --global --add safe.directory $safePath
        Write-Host "Trusted: $safePath"
        $existingSafeDirectories += $safePath
        $added++
    }
}

Write-Host ""
Write-Host "Summary:"
Write-Host "  Added:           $added"
Write-Host "  Already trusted: $alreadyTrusted"
Write-Host "  Skipped:         $skipped"

if ($DryRun) {
    Write-Host ""
    Write-Host "Dry run only. Re-run without -DryRun to update global Git config."
}

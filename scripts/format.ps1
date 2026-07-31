$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$dirs = @("include", "src", "apps", "tests")

$files = @()
foreach ($d in $dirs) {
    $p = Join-Path $root $d
    if (Test-Path $p) {
        $files += Get-ChildItem -Path $p -Recurse -Include *.hpp,*.cpp,*.h,*.c
    }
}

if ($files.Count -eq 0) {
    Write-Host "No source files found."
    exit 0
}

Write-Host "Formatting $($files.Count) files..."
clang-format -i $files.FullName
Write-Host "Done."

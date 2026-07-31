# Author's local convenience wrapper — paths are machine-specific (VS 18 BuildTools).
# The canonical, portable build is the CMake preset flow in the README:
#   cmake --preset msvc-release && cmake --build --preset msvc-release && ctest --preset msvc-release
param([switch]$Test)
$devshell = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\Launch-VsDevShell.ps1"
& $devshell -Arch amd64 -SkipAutomaticLocation 2>$null | Out-Null
$cmdir = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake"
$env:PATH = "$cmdir\CMake\bin;$cmdir\Ninja;$env:PATH"
Set-Location "$PSScriptRoot\.."
cmake --build --preset msvc-release 2>&1 | Select-Object -Last 1
if ($LASTEXITCODE -ne 0) { exit 1 }
if ($Test) { ctest --preset msvc-release 2>&1 | Select-String "tests passed|tests failed" }
.\build\msvc-release\telemetry_runner.exe | Select-String "schedule|Lap time"

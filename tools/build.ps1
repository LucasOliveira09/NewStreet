param([ValidateSet('All', 'Probe', 'Runtime', 'Boot')][string]$Target = 'All')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$locked = Get-Content -LiteralPath 'toolchain.lock.json' -Raw | ConvertFrom-Json
$actualRevision = git -C vendor/ps3recomp rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $actualRevision -ne $locked.ps3recomp.commit) {
    throw 'ps3recomp checkout differs from toolchain.lock.json.'
}
$vsWhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$vsPath = & $vsWhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vsPath) { throw 'Visual Studio C++ tools were not found.' }
# https://learn.microsoft.com/en-us/visualstudio/ide/reference/command-prompt-powershell
& (Join-Path $vsPath 'Common7\Tools\Launch-VsDevShell.ps1') -Arch amd64 -HostArch amd64 -SkipAutomaticLocation -NoLogo
$llvmBin = Join-Path $projectRoot 'private\toolchain\clang+llvm-23.1.4-x86_64-pc-windows-msvc\bin'
$cmakeRoot = Join-Path $vsPath 'Common7\IDE\CommonExtensions\Microsoft\CMake'
$cmake = Join-Path $cmakeRoot 'CMake\bin\cmake.exe'
$ctest = Join-Path $cmakeRoot 'CMake\bin\ctest.exe'
$python = Join-Path $projectRoot 'private\python-env\Scripts\python.exe'
if (-not (Test-Path -LiteralPath "$llvmBin\clang-cl.exe")) { throw 'Portable LLVM 23.1.4 is missing.' }
$env:PATH = "$llvmBin;$cmakeRoot\Ninja;$env:PATH"

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit code $LASTEXITCODE" }
}

Invoke-Checked $python @('tools/apply_patches.py')

if ($Target -in @('All', 'Runtime')) {
    Invoke-Checked $cmake @('-S','vendor/ps3recomp','-B','private/build/runtime-clang','-G','Ninja',
        '-DCMAKE_C_COMPILER=clang-cl','-DCMAKE_CXX_COMPILER=clang-cl',
        '-DCMAKE_BUILD_TYPE=Release','-DPS3RECOMP_BUILD_TESTS=ON')
    Invoke-Checked $cmake @('--build','private/build/runtime-clang','--parallel','3')
    Invoke-Checked $ctest @('--test-dir','private/build/runtime-clang','--output-on-failure',
        '--timeout','30','--parallel','2')
}
if ($Target -in @('All', 'Probe')) {
    Invoke-Checked $python @('tools/lift_probe.py','private/FIFAZF.elf')
    Invoke-Checked $cmake @('-S','.','-B','private/build/probe','-G','Ninja',
        '-DCMAKE_C_COMPILER=clang-cl','-DCMAKE_CXX_COMPILER=clang-cl','-DCMAKE_BUILD_TYPE=Release')
    Invoke-Checked $cmake @('--build','private/build/probe','--parallel','2')
    Invoke-Checked $python @('-m','unittest','discover','-s','tests','-p','test_native_probe.py')
}
if ($Target -in @('All', 'Boot')) {
    Invoke-Checked $python @('vendor/ps3recomp/tools/ppu_lifter.py','private/EBOOT.elf',
        '--functions','private/analysis/eboot/EBOOT.functions.json',
        '--hle-stubs','private/analysis/eboot/EBOOT.imports.json',
        '--jobs','2','--single-file','-o','private/generated/eboot')
    Invoke-Checked $cmake @('-S','.','-B','private/build/boot','-G','Ninja',
        '-DCMAKE_C_COMPILER=clang-cl','-DCMAKE_CXX_COMPILER=clang-cl','-DCMAKE_BUILD_TYPE=RelWithDebInfo',
        '-DFIFA_BUILD_BOOT=ON',"-DPython3_EXECUTABLE=$python")
    Invoke-Checked $cmake @('--build','private/build/boot','--target','fifa_boot','--parallel','2')
    Invoke-Checked $python @('-m','unittest','discover','-s','tests','-p','test_boot_diagnostics.py')
}

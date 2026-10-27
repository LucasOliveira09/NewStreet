$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$bootExe = Join-Path $projectRoot 'private\build\boot\fifa_boot.exe'
$gameExe = Join-Path $projectRoot 'private\build\fifazf_full\fifa_boot.exe'
$bootElf = Join-Path $projectRoot 'private\EBOOT.elf'
$gameElf = Join-Path $projectRoot 'private\FIFAZF.elf'
$disc = Join-Path $projectRoot 'private\disc'
$profile = Join-Path $projectRoot 'private\userdata_interactive'
foreach ($requiredPath in @($bootExe, $gameExe, $bootElf, $gameElf, $disc)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) { throw "Entrada ausente: $requiredPath" }
}
$active = Get-Process fifa_boot -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -eq $bootExe -or $_.Path -eq $gameExe }
if ($active) { throw 'O FIFA nativo ja esta aberto. Feche a janela antes de iniciar outra sessao.' }
if (-not (Test-Path -LiteralPath $profile)) {
    $baseline = Join-Path $projectRoot 'private\userdata'
    if (-not (Test-Path -LiteralPath $baseline)) { throw 'Perfil de referencia ausente.' }
    Copy-Item -LiteralPath $baseline -Destination $profile -Recurse
}
$logDir = Join-Path $projectRoot ('private\analysis\interactive-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fffffff'))
New-Item -ItemType Directory -Path $logDir | Out-Null
$launchEnvironment = @{
    FIFA_NEXT_EXE = $gameExe
    FIFA_NEXT_ELF = $gameElf
    PS3_HDD0_ROOT = (Join-Path $profile 'dev_hdd0')
    PS3_HDD1_ROOT = (Join-Path $profile 'dev_hdd1')
    PS3_HLE_TRACE = '200'
    PS3_VERBOSE = '0'
}
# Keep diagnostic overrides out of interactive sessions; restore the calling shell.
foreach ($key in @('PAD_FILE','PAD_SCRIPT','PAD_AUTOPRESS','PAD_NO_KEYBOARD',
    'PAD_ALWAYS_CHANGE','FP_IDCOLOR','FP_TEX','FP_TEX_FP','FP_FORCE','FP_SHOW',
    'FP_OFF','FP_KILL','FP_PICK','FP_DUMP','VP_BYPASS','VP_DUMP','DEPTH_OFF',
    'RSX_CAP','RSX_CAP_DIR','CELLMARK_DUMP','AUDIO_WAV','FIFA_WATCHDOG_AFTER_MS',
    'SPU_PCSAMPLE','SPU_PCSAMPLE_DUMP_AFTER')) { $launchEnvironment[$key] = $null }
$previousEnvironment = @{}
try {
    foreach ($key in $launchEnvironment.Keys) {
        $previousEnvironment[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
        [Environment]::SetEnvironmentVariable($key, $launchEnvironment[$key], 'Process')
    }
    $arguments = '"{0}" "{1}"' -f $bootElf, $disc
    $process = Start-Process -FilePath $bootExe -ArgumentList $arguments -WorkingDirectory $projectRoot `
        -WindowStyle Normal -PassThru -RedirectStandardOutput (Join-Path $logDir 'stdout.log') `
        -RedirectStandardError (Join-Path $logDir 'stderr.log')
} finally {
    foreach ($key in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($key, $previousEnvironment[$key], 'Process')
    }
}
Write-Host "FIFA nativo iniciado (PID $($process.Id))."
Write-Host 'Enter = Start | Z = confirmar | X = voltar | Setas = navegar'
Write-Host "Perfil: $profile"
Write-Host "Logs: $logDir"
$process.WaitForExit()
$process.Refresh()
$exitCode = $process.ExitCode
if ($null -eq $exitCode) { throw "O processo nativo foi encerrado sem codigo de saida. Consulte $logDir" }
if ($exitCode -ne 0) { throw "O processo nativo encerrou com codigo $exitCode. Consulte $logDir" }

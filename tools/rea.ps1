$projectRoot = Split-Path -Parent $PSScriptRoot
$node = Join-Path $projectRoot 'private\toolchain\node-v24.22.1-win-x64\node.exe'
$rea = Join-Path $projectRoot 'private\rea-cli\node_modules\rea-agents\scripts\rea.mjs'
& $node $rea @args
exit $LASTEXITCODE

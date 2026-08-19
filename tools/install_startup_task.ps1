$ErrorActionPreference = "Stop"

$TaskName = "UZWATERMU Telegram Bot"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$Python = (py -3.14 -c "import sys; print(sys.executable)").Trim()
if (-not $Python) {
    throw "Python 3.14 topilmadi."
}

$Action = New-ScheduledTaskAction `
    -Execute $Python `
    -Argument "-m tools.bot_supervisor" `
    -WorkingDirectory $ProjectRoot

$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $CurrentUser
$Principal = New-ScheduledTaskPrincipal `
    -UserId $CurrentUser `
    -LogonType Interactive `
    -RunLevel Limited

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -StartWhenAvailable

$Task = New-ScheduledTask `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description "UZWATERMU Telegram bot supervisor"

Register-ScheduledTask `
    -TaskName $TaskName `
    -InputObject $Task `
    -Force | Out-Null

Write-Output "TASK_INSTALLED=$TaskName"
Write-Output "TASK_USER=$CurrentUser"
Write-Output "PROJECT=$ProjectRoot"

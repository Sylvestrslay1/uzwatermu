$ErrorActionPreference = "Stop"
$TaskName = "UZWATERMU Telegram Bot"

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "TASK_REMOVED=$TaskName"
} else {
    Write-Output "TASK_NOT_FOUND=$TaskName"
}

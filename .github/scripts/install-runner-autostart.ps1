# Starts the configured self-hosted runner (C:\actions-runner) at the logon of the current Windows user,
# in the user's desktop session: IDA Districts runs with a GUI (-G1) and needs a desktop, which a
# Windows service does not have (the simulations fail there). Removes a runner service if there is one.
# Run in an ADMINISTRATOR PowerShell, logged in as the user that owns the IDA license and pytest.
$ErrorActionPreference = 'Stop'
$dir  = 'C:\actions-runner'
$task = 'GitHub Actions runner (IDA-Districts)'
$user = "$env:USERDOMAIN\$env:USERNAME"

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Please run this script in an administrator PowerShell.'
}
if (-not (Test-Path "$dir\.runner")) {
    throw "No configured runner in ${dir}: run config.cmd first (.github/RUNNER_SETUP.md, step 3)."
}

foreach ($svc in Get-Service 'actions.runner.*' -ErrorAction SilentlyContinue) {
    Stop-Service $svc.Name -Force
    sc.exe delete $svc.Name | Out-Null
    Write-Host "service removed: $($svc.Name)"
}
Remove-Item "$dir\.service" -ErrorAction SilentlyContinue

$action    = New-ScheduledTaskAction -Execute "$dir\run.cmd" -WorkingDirectory $dir
$trigger   = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
# no time limit (the runner runs for the whole session); restarted if it ends with an error
$settings  = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $task -Action $action -Trigger $trigger -Principal $principal `
    -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName $task
Write-Host "task '$task' registered and started (runner window on the desktop of $user)"

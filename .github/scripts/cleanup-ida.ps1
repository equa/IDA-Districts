# Ends the IDA Districts processes which were started after -Since (the start of the CI job).
# The plugin starts an ida-districts.exe for each simulation and does not end it; processes started
# before the job (e.g. an IDA Districts opened by the user of the runner machine) are kept.
param(
    [Parameter(Mandatory = $true)][string]$Since
)

$start = [datetime]::Parse($Since)
$processes = Get-CimInstance Win32_Process -Filter "Name='ida-districts.exe'" |
    Where-Object { $_.CreationDate -ge $start }
foreach ($p in $processes) {
    try {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
        Write-Output "stopped ida-districts.exe $($p.ProcessId) (started $($p.CreationDate))"
    }
    catch {
        Write-Output "could not stop ida-districts.exe $($p.ProcessId): $_"
    }
}
if (-not $processes) { Write-Output "no IDA Districts processes of this job" }
exit 0

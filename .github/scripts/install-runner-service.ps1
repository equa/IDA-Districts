# Re-registers the self-hosted runner PETER (C:\actions-runner) as a Windows service
# under the current Windows user, so it has the IDA license and the user's pytest.
# Run in an ADMINISTRATOR PowerShell, logged in as the user the runner should run as.
# Asks for that user's Windows password (hidden input, only passed to config.cmd).
$ErrorActionPreference = 'Stop'
$repo = 'equa/IDA-Districts'
$dir  = 'C:\actions-runner'
$account = "$env:USERDOMAIN\$env:USERNAME"

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Please run this script in an administrator PowerShell.'
}
if (Get-Process Runner.Listener -ErrorAction SilentlyContinue) {
    throw 'The runner is running (run.cmd). Close its window (Ctrl+C) first.'
}
Set-Location $dir

$secure = Read-Host "Windows password of $account" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
if (-not $password) {
    throw 'Empty password: a service needs an account with a password (a PIN/Windows Hello is not enough).'
}
Add-Type -AssemblyName System.DirectoryServices.AccountManagement
$ctx = New-Object System.DirectoryServices.AccountManagement.PrincipalContext('Machine')
if (-not $ctx.ValidateCredentials($env:USERNAME, $password)) {
    throw "Windows rejected the password of $account (for a Microsoft account: its online password)."
}

# tokens stay in variables, they are never printed
if (Test-Path .runner) {
    $removeToken = gh api -X POST "repos/$repo/actions/runners/remove-token" --jq .token
    .\config.cmd remove --token $removeToken
    if ($LASTEXITCODE) { throw 'config.cmd remove failed' }
}
$regToken = gh api -X POST "repos/$repo/actions/runners/registration-token" --jq .token
.\config.cmd --unattended --url "https://github.com/$repo" --token $regToken `
    --name PETER --work _work --replace --labels districts `
    --runasservice --windowslogonaccount $account --windowslogonpassword $password
$code = $LASTEXITCODE
$password = $null
if ($code) { throw 'config.cmd failed' }

Get-Service 'actions.runner.*' | Format-Table Name, Status, StartType -AutoSize

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$python = "C:\Users\acer\AppData\Local\Programs\Python\Python312\python.exe"
$envFile = Join-Path $scriptDir ".env"

if (!(Test-Path $envFile)) {
    Copy-Item (Join-Path $scriptDir ".env.example") $envFile -Force
}

$helpRequested = $false
foreach ($arg in $args) {
    if ($arg -eq "--help" -or $arg -eq "-h") {
        $helpRequested = $true
        break
    }
}

if (-not $helpRequested) {
    $token = $env:GITHUB_TOKEN

    if ([string]::IsNullOrWhiteSpace($token) -and (Test-Path $envFile)) {
        foreach ($line in Get-Content $envFile) {
            if ($line -match '^\s*GITHUB_TOKEN\s*=\s*(.*)$') {
                $token = $matches[1].Trim()
                break
            }
        }
    }

    if ([string]::IsNullOrWhiteSpace($token) -or $token -like "*your_github_personal_access_token_here*") {
        Write-Host "GitHub token is missing or still set to the placeholder value." -ForegroundColor Yellow
        Write-Host "Set it for this PowerShell session with:" -ForegroundColor Yellow
        Write-Host "  `$env:GITHUB_TOKEN = 'ghp_your_token_here'" -ForegroundColor Cyan
        Write-Host "Or edit the file and replace GITHUB_TOKEN in: $envFile" -ForegroundColor Cyan
        Write-Host "Then run this script again." -ForegroundColor Yellow
        exit 1
    }
}

& $python -m api_client.cli @args
exit $LASTEXITCODE

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

$ProxyEnvNames = @(
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy"
)
foreach ($Name in $ProxyEnvNames) {
    Remove-Item -LiteralPath "Env:$Name" -ErrorAction SilentlyContinue
}

$Python = (py -3.14 -c "import sys; print(sys.executable)" 2>$null).Trim()
if (-not $Python) {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $Python) { exit 1 }
}

# Supervisor to'xtasa, exit code 0 bilan chiqsa ham qayta ishga tushiradi.
# Faqat SIGTERM (to'g'ri yopilish, code=0) va ikkinchi nusxa (code=3) holatida to'xtaydi.
while ($true) {
    & $Python -m tools.bot_supervisor
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -eq 0 -or $ExitCode -eq 3) {
        # 0 = SIGTERM orqali to'g'ri yopildi, 3 = boshqa nusxa ishlayapti
        exit $ExitCode
    }
    Start-Sleep -Seconds 15
}

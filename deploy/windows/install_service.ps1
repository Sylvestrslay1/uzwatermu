# NSSM orqali Windows servisi sifatida o'rnatish (https://nssm.cc).
# Administrator PowerShell'da, loyiha ildizidan ishga tushiring.
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
nssm install UzwatermuBot $Python "-m uzwatermu run"
nssm set UzwatermuBot AppDirectory $ProjectRoot
nssm set UzwatermuBot AppRestartDelay 10000
nssm set UzwatermuBot Start SERVICE_AUTO_START
# .env va var\ papkasiga faqat joriy foydalanuvchi va SYSTEM kira olsin:
icacls (Join-Path $ProjectRoot ".env") /inheritance:r /grant:r "$env:USERNAME:R" "SYSTEM:R"
Write-Output "O'rnatildi. Ishga tushirish: nssm start UzwatermuBot"

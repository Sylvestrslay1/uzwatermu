$ErrorActionPreference = "Stop"

$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
$CurrentIdentity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$AclBackup = Join-Path $ProjectRoot "logs\project_acl_before_hardening.xml"

New-Item -ItemType Directory -Force (Split-Path -Parent $AclBackup) | Out-Null
Get-Acl -LiteralPath $ProjectRoot | Export-Clixml -LiteralPath $AclBackup

$acl = Get-Acl -LiteralPath $ProjectRoot
$acl.SetAccessRuleProtection($true, $false)
foreach ($rule in @($acl.Access)) {
    [void]$acl.RemoveAccessRuleAll($rule)
}

$inheritance = [System.Security.AccessControl.InheritanceFlags]"ContainerInherit, ObjectInherit"
$propagation = [System.Security.AccessControl.PropagationFlags]::None
$allow = [System.Security.AccessControl.AccessControlType]::Allow
$full = [System.Security.AccessControl.FileSystemRights]::FullControl

foreach ($identity in @(
    $CurrentIdentity,
    "NT AUTHORITY\SYSTEM",
    "BUILTIN\Administrators"
)) {
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        $identity,
        $full,
        $inheritance,
        $propagation,
        $allow
    )
    $acl.AddAccessRule($rule)
}

Set-Acl -LiteralPath $ProjectRoot -AclObject $acl

Write-Output "ACL_HARDENED=$ProjectRoot"
Write-Output "ALLOWED_USER=$CurrentIdentity"
Write-Output "ACL_BACKUP=$AclBackup"

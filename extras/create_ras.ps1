# Переменные
$SrvUser = ".\USR1CV8"
$SrvPwd = "***"
$SrvDesc = "1C:Enterprise 8.3 Remote Administration Server"
$AgentName = "localhost"
$CtrlPort = "1540"
$RASPort = "1545"
$PlatformVersion = "8.3.27.2214"

$SrvName = "1C:Enterprise 8.3 RAS $AgentName`:$CtrlPort"

$SrvBin = "`"C:\Program Files\1cv8\$PlatformVersion\bin\ras.exe`" cluster --service --port=$RASPort $AgentName`:$CtrlPort"

$service = Get-Service -Name $SrvName -ErrorAction SilentlyContinue
if ($service) {
    if ($service.Status -eq 'Running') {
        Write-Host "Stopping service `"$SrvName`"..." -ForegroundColor Yellow
        Stop-Service -Name $SrvName -Force
        # Ждем полной остановки (до 30 секунд)
        $service.WaitForStatus('Stopped', '00:00:30')
    }
}

$service = Get-Service -Name $SrvName -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "Deleting service `"$SrvName`"..." -ForegroundColor Yellow
    & sc.exe delete $SrvName | Out-Null
    Start-Sleep -Seconds 5
}

Write-Host "Creating service `"$SrvName`"..." -ForegroundColor Cyan
$SecurePwd = ConvertTo-SecureString $SrvPwd -AsPlainText -Force
$Credential = New-Object System.Management.Automation.PSCredential ($SrvUser, $SecurePwd)

try {
    New-Service -Name $SrvName `
                -BinaryPathName $SrvBin `
                -StartupType Automatic `
                -Credential $Credential `
                -Description $SrvDesc `
                -ErrorAction Stop
    Write-Host "Service created successfully." -ForegroundColor Green
} catch {
    Write-Error "Failed to create service: $_"
    exit 1
}

Write-Host "Starting service `"$SrvName`"..." -ForegroundColor Cyan
Start-Service -Name $SrvName

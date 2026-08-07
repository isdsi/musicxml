# verify_portable.ps1
# 무설치 포터블 배포판이 외부 Fluidsynth/FFmpeg 런타임 의존성 없이 정상 구동되는지 검증합니다.

$ScriptDir = $PSScriptRoot
$ProjectRoot = Split-Path $ScriptDir -Parent
$SandboxDir = Join-Path $ProjectRoot "portable_test_sandbox"
$ZipPath = Join-Path $ProjectRoot "musicxml-player-win64-portable.zip"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  포터블 배포판 의존성 격리 테스트 (Sandbox Verification)" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

if (-not (Test-Path $ZipPath)) {
    Write-Host "[오류] 검증할 포터블 ZIP 파일이 존재하지 않습니다: $ZipPath" -ForegroundColor Red
    exit 1
}

# 1. 샌드박스 생성 및 압축 해제
if (Test-Path $SandboxDir) { Remove-Item -Recurse -Force $SandboxDir }
New-Item -ItemType Directory -Path $SandboxDir -Force | Out-Null
Write-Host "[1/4] 임시 샌드박스로 ZIP 파일 압축 해제 중..." -ForegroundColor Gray
Expand-Archive -Path $ZipPath -DestinationPath $SandboxDir -Force

# 2. 환경변수 초격리 설정
# 기존 Chocolatey, FFmpeg, Fluidsynth 및 파이썬 관련 환경을 PATH에서 완벽하게 박멸
$OriginalPath = $env:PATH
$env:PATH = "C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0\"

Write-Host "[2/4] 환경변수 PATH 초격리 완료 (기본 Windows 경로 외 모두 차단)" -ForegroundColor Gray
Write-Host "  격리된 PATH: $env:PATH" -ForegroundColor DarkGray

# 3. 플레이어 기동 테스트
Write-Host "[3/4] musicxml_player.exe 프로세스 백그라운드 기동 (5초 모니터링)..." -ForegroundColor Gray
$TargetExe = Join-Path $SandboxDir "musicxml_player.exe"

$proc = Start-Process -FilePath $TargetExe -PassThru -ErrorAction SilentlyContinue

# 기동 대기 및 상태 관찰
Start-Sleep -Seconds 5

$isAlive = $false
if ($proc -and -not $proc.HasExited) {
    $isAlive = $true
    Write-Host ""
    Write-Host "[성공] 플레이어가 외부 의존성(FFmpeg/Fluidsynth) 없이 정상적으로 구동 상태를 유지하고 있습니다!" -ForegroundColor Green
    # 구동 검증 완료 후 프로세스 안전 강제 종료
    Stop-Process -Id $proc.Id -Force
} else {
    Write-Host ""
    Write-Host "[실패] 플레이어 실행 파일이 의존성 부재 등의 사유로 즉시 강제 종료되었습니다." -ForegroundColor Red
}

# 4. 자원 원복 및 청소
$env:PATH = $OriginalPath
if (Test-Path $SandboxDir) {
    # 프로세스 완전 종료 처리를 위해 약간 대기 후 삭제
    Start-Sleep -Seconds 1
    Remove-Item -Recurse -Force $SandboxDir -ErrorAction SilentlyContinue
}
Write-Host "[4/4] 격리 테스트 샌드박스 청소 및 PATH 환경 변수 복원 완료." -ForegroundColor Gray
Write-Host "======================================================" -ForegroundColor Cyan

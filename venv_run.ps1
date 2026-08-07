# venv_run.ps1
# .venv 가상환경을 활성화하여 현재 셸에 진입합니다.
#
# 사용법:
#   .\venv_run.ps1
#
# 가상환경을 빠져나오려면: deactivate

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ActivatePs1 = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $ActivatePs1)) {
    Write-Host "[오류] 가상환경이 없습니다: $ActivatePs1" -ForegroundColor Red
    Write-Host "       먼저 .\venv_install.ps1 을 실행하세요." -ForegroundColor Yellow
    exit 1
}

Write-Host "[정보] 가상환경 활성화: $ActivatePs1" -ForegroundColor Cyan
. $ActivatePs1

Write-Host "[완료] .venv 가 활성화되었습니다. 빠져나오려면 'deactivate' 를 입력하세요." -ForegroundColor Green

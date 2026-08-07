# setup.ps1
# 이 프로젝트를 실행하기 위한 모든 환경을 단일 스크립트로 설정합니다:
# 1. Chocolatey 설치
# 2. FluidSynth 설치
# 3. FFmpeg (ffmpeg-full) 설치
# 4. Python 가상환경 생성 및 requirements.txt 의존성 설치
#
# 주의: Chocolatey 패키지 설치를 위해 관리자 권한이 필요합니다.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# 1. 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "이 스크립트는 Chocolatey, FluidSynth, FFmpeg 설치를 위해 관리자 권한이 필요합니다."
    Write-Host "PowerShell을 '관리자로 실행'한 뒤 다시 실행해 주세요." -ForegroundColor Yellow
    Write-Host "또는 아래 명령어로 관리자 권한으로 재실행할 수 있습니다:" -ForegroundColor Cyan
    Write-Host 'Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs' -ForegroundColor Cyan
    exit 1
}

$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
$VenvDir     = Join-Path $ScriptDir ".venv"
$ReqFile     = Join-Path $ScriptDir "requirements.txt"

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host ">>> $msg" -ForegroundColor Cyan
}

function Write-Ok([string]$msg) {
    Write-Host "    [OK] $msg" -ForegroundColor Green
}

function Write-Warn([string]$msg) {
    Write-Host "    [주의] $msg" -ForegroundColor Yellow
}

function Write-Fail([string]$msg) {
    Write-Host "    [오류] $msg" -ForegroundColor Red
}

function Download-FileWithProgress([string]$url, [string]$dest) {
    try {
        # BITS 전송을 시도하여 프로그레스 바를 보여줍니다.
        Import-Module BitsTransfer -ErrorAction SilentlyContinue
        Start-BitsTransfer -Source $url -Destination $dest -ErrorAction Stop
    }
    catch {
        # BITS 전송에 실패하거나 사용할 수 없는 경우 WebClient로 다운로드합니다.
        Write-Warn "Start-BitsTransfer를 사용할 수 없어 WebClient 백업 방식을 사용합니다."
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($url, $dest)
    }
}

# 2. Chocolatey 설치 확인 및 설치
Write-Step "Chocolatey 패키지 매니저 확인"
$chocoPath = Get-Command choco -ErrorAction SilentlyContinue
if (-not $chocoPath) {
    Write-Host "Chocolatey가 발견되지 않았습니다. Chocolatey 설치를 시작합니다..." -ForegroundColor Cyan
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        # 환경 변수 리프레시
        $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
            throw "Chocolatey 설치 후 환경 변수 로드에 실패했습니다. 새 PowerShell 창을 열고 다시 시도해 주세요."
        }
        Write-Ok "Chocolatey 설치 완료!"
    }
    catch {
        Write-Fail "Chocolatey 설치 중 오류가 발생했습니다: $_"
        Write-Host "직접 https://chocolatey.org/install 에서 Chocolatey를 설치한 후 다시 시도해 주세요." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Ok "Chocolatey가 이미 설치되어 있습니다."
}

# 3. FluidSynth 설치 확인 및 설치
Write-Step "FluidSynth 확인 및 설치"
$fluidPath = Get-Command fluidsynth -ErrorAction SilentlyContinue
if ($fluidPath) {
    Write-Ok "FluidSynth가 이미 설치되어 있습니다: $($fluidPath.Source)"
} else {
    Write-Host "FluidSynth가 발견되지 않았습니다. Chocolatey를 통해 설치합니다..." -ForegroundColor Cyan
    try {
        choco install fluidsynth -y
        $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        Write-Ok "FluidSynth 설치 완료!"
    }
    catch {
        Write-Fail "FluidSynth 설치 실패: $_"
        exit 1
    }
}

# 4. FFmpeg 설치 확인 및 설치
Write-Step "FFmpeg 확인 및 설치"
$ffmpegPath = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpegPath) {
    Write-Ok "FFmpeg가 이미 설치되어 있습니다: $($ffmpegPath.Source)"
} else {
    Write-Host "FFmpeg가 발견되지 않았습니다. Chocolatey를 통해 ffmpeg-full을 설치합니다..." -ForegroundColor Cyan
    try {
        choco install ffmpeg-full -y
        $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        Write-Ok "FFmpeg 설치 완료!"
    }
    catch {
        Write-Fail "FFmpeg 설치 실패: $_"
        exit 1
    }
}

# 5. SoundFont 파일 다운로드
Write-Step "SoundFont (FluidR3_GM.sf2) 확인 및 다운로드"
$Sf2Url = "https://raw.githubusercontent.com/urish/cinto/refs/heads/master/media/FluidR3%20GM.sf2"
$Sf2Path = Join-Path $ScriptDir "FluidR3_GM.sf2"

if (Test-Path $Sf2Path) {
    $size = (Get-Item $Sf2Path).Length
    if ($size -gt 10MB) {
        Write-Ok "FluidR3_GM.sf2 사운드폰트가 이미 존재합니다. (크기: $([math]::Round($size / 1MB, 1)) MB)"
    } else {
        Write-Warn "기존 사운드폰트 파일 크기가 유효하지 않아 다시 다운로드합니다."
        Remove-Item $Sf2Path -Force
        Write-Host "FluidR3_GM.sf2 다운로드 중 (약 141MB, 네트워크 환경에 따라 수 분 소요)..." -ForegroundColor Cyan
        Download-FileWithProgress -url $Sf2Url -dest $Sf2Path
        Write-Ok "사운드폰트 다운로드 완료!"
    }
} else {
    Write-Host "FluidR3_GM.sf2 다운로드 중 (약 141MB, 네트워크 환경에 따라 수 분 소요)..." -ForegroundColor Cyan
    try {
        Download-FileWithProgress -url $Sf2Url -dest $Sf2Path
        Write-Ok "사운드폰트 다운로드 완료!"
    }
    catch {
        Write-Fail "사운드폰트 다운로드 중 오류 발생: $_"
        Write-Fail "직접 다음 URL에서 다운로드하여 프로젝트 폴더에 넣어주세요:"
        Write-Fail "  $Sf2Url"
        exit 1
    }
}

# 6. Python 확인
Write-Step "Python 확인"
$PythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+\.\d+)") {
            $PythonCmd = $cmd
            Write-Ok "$cmd $ver"
            break
        }
    } catch { }
}

if (-not $PythonCmd) {
    Write-Fail "Python 을 찾을 수 없습니다. https://www.python.org/downloads/ 에서 설치하세요."
    exit 1
}

# 7. 가상환경(.venv) 생성
Write-Step "가상환경 생성: $VenvDir"
if (Test-Path $VenvDir) {
    Write-Warn ".venv 폴더가 이미 존재합니다. 재사용합니다."
} else {
    & $PythonCmd -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "가상환경 생성 실패"
        exit 1
    }
    Write-Ok "가상환경 생성 완료"
}

# 8. 가상환경 내 pip / python 경로 결정
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip    = Join-Path $VenvDir "Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Fail "가상환경 python.exe 를 찾을 수 없습니다: $VenvPython"
    exit 1
}

# 9. pip 최신화
Write-Step "pip 업그레이드"
& $VenvPython -m pip install --upgrade pip | Out-Null
Write-Ok "pip 업그레이드 완료"

# 10. requirements.txt 패키지 설치
Write-Step "패키지 설치 (requirements.txt)"
if (-not (Test-Path $ReqFile)) {
    Write-Fail "requirements.txt 파일이 없습니다: $ReqFile"
    exit 1
}

& $VenvPip install -r $ReqFile
if ($LASTEXITCODE -ne 0) {
    Write-Fail "패키지 설치 중 오류가 발생했습니다."
    exit 1
}
Write-Ok "모든 패키지 설치 완료"

# 11. 설치 확인
Write-Step "최종 연동 테스트"
$Packages = @("music21", "fluidsynth", "pydub")
foreach ($pkg in $Packages) {
    # 파이썬 내부에서 예외 처리를 수행하여 stderr 출력으로 인한 파워쉘 NativeCommandError 예방
    $result = & $VenvPython -c "
try:
    import $pkg
    try:
        print($pkg.__version__)
    except AttributeError:
        print('OK')
except Exception as e:
    print('FAIL: ' + str(e))
"
    if ($result -notlike "FAIL:*") {
        $version = $result.Trim()
        Write-Ok "$pkg 라이브러리 연동 성공 ($version)"
    } else {
        $errMsg = $result.Replace("FAIL:", "").Trim()
        Write-Warn "$pkg 임포트 실패 (사유: $errMsg)"
    }
}

# 12. 완료 안내
Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  모든 개발 환경 설정 및 설치 완료!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  가상환경 활성화 방법:" -ForegroundColor White
Write-Host "    .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "  스크립트 실행 예시 (가상환경 활성화 상태에서):" -ForegroundColor White
Write-Host "    python midi_to_musicxml.py song.mid" -ForegroundColor Yellow
Write-Host "    python musicxml_to_ogg.py song.xml" -ForegroundColor Yellow
Write-Host ""

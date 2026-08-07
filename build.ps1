# build.ps1
# 이 프로젝트의 파이썬 스크립트들을 단일 EXE 파일로 빌드합니다.
#
# 사용법:
#   .\build.ps1 [-Target] <target_name>
#
# 타겟 목록:
#   all               : 4개 유틸리티 모두 빌드 (기본값)
#   midi_to_musicxml  : MIDI ➔ MusicXML 변환기 빌드
#   musicxml_to_midi  : MusicXML ➔ MIDI 변환기 빌드
#   midi_to_ogg       : MIDI ➔ OGG 변환기 빌드 (music21 미사용으로 빠름)
#   musicxml_to_ogg   : MusicXML ➔ OGG 변환기 빌드 (시간이 수 분 소요됨)

Param(
    [ValidateSet("all", "midi_to_musicxml", "musicxml_to_midi", "midi_to_ogg", "musicxml_to_ogg")]
    [string]$Target = "all"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 1. 실행 환경 확인 (가상환경 및 파이썬 확인)
$VenvDir = Join-Path $ScriptDir ".venv"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"
$VenvPyinstaller = Join-Path $VenvDir "Scripts\pyinstaller.exe"

$PyinstallerCmd = "pyinstaller"

if (Test-Path $VenvPyinstaller) {
    # 가상환경 내의 PyInstaller 사용
    $PyinstallerCmd = $VenvPyinstaller
    Write-Host "[정보] 가상환경 내 PyInstaller를 활용합니다: $PyinstallerCmd" -ForegroundColor Cyan
} else {
    # 가상환경이 없거나 활성화되지 않은 경우
    if (Test-Path $VenvPip) {
        Write-Host "[설치] 가상환경 내 PyInstaller가 없습니다. 설치를 진행합니다..." -ForegroundColor Cyan
        & $VenvPip install --quiet pyinstaller
        if (Test-Path $VenvPyinstaller) {
            $PyinstallerCmd = $VenvPyinstaller
        } else {
            Write-Warning "가상환경 내 PyInstaller 설치를 확인하지 못했습니다. 시스템 글로벌 pyinstaller 사용을 시도합니다."
        }
    } else {
        # 가상환경 자체도 없는 경우 글로벌 pyinstaller 검색
        $globalPyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
        if (-not $globalPyinstaller) {
            Write-Host "[오류] 가상환경 또는 시스템에 PyInstaller가 설치되어 있지 않습니다." -ForegroundColor Red
            Write-Host "       먼저 .\setup.ps1 을 실행하여 의존성 설정을 완료해 주세요." -ForegroundColor Yellow
            exit 1
        }
        Write-Host "[정보] 시스템 글로벌 PyInstaller를 사용합니다: $($globalPyinstaller.Source)" -ForegroundColor Cyan
    }
}

# 2. 빌드 헬퍼 함수 정의
function Build-Target([string]$name, [string]$script, [bool]$useMusic21) {
    Write-Host ""
    Write-Host "======================================================" -ForegroundColor Cyan
    Write-Host "  빌드 시작: $name.exe" -ForegroundColor Cyan
    Write-Host "======================================================" -ForegroundColor Cyan
    
    $args = @(
        "--clean",
        "--onefile",
        "--name", $name,
        "--distpath", ".",
        "--workpath", "./build",
        "--specpath", ".",
        "--noconfirm"
    )
    
    if ($useMusic21) {
        # music21 라이브러리 리소스 수집 및 누락되는 임포트 강제 추가
        $args += @(
            "--collect-all", "music21",
            "--hidden-import", "music21.converter.subConverters",
            "--hidden-import", "music21.midi",
            "--hidden-import", "music21.midi.translate",
            "--hidden-import", "music21.stream",
            "--hidden-import", "music21.stream.base"
        )
    }
    
    $args += $script
    
    Write-Host "[실행] $PyinstallerCmd $args" -ForegroundColor Gray
    
    # pyinstaller 구동
    & $PyinstallerCmd $args
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path ".\$name.exe")) {
        $size = [math]::Round((Get-Item ".\$name.exe").Length / 1MB, 1)
        Write-Host ""
        Write-Host "[성공] 빌드 완료!" -ForegroundColor Green
        Write-Host "  위치 : .\$name.exe" -ForegroundColor Green
        Write-Host "  크기 : ${size} MB" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[오류] 빌드 도중 에러가 발생했거나 파일이 생성되지 않았습니다." -ForegroundColor Red
        exit 1
    }
}

# 3. 타겟 분류 및 빌드 수행
Write-Host "[정보] 빌드 타겟 지정: $Target" -ForegroundColor Green

if ($Target -eq "all" -or $Target -eq "midi_to_musicxml") {
    Build-Target -name "midi_to_musicxml" -script "midi_to_musicxml.py" -useMusic21 $true
}

if ($Target -eq "all" -or $Target -eq "musicxml_to_midi") {
    Build-Target -name "musicxml_to_midi" -script "musicxml_to_midi.py" -useMusic21 $true
}

if ($Target -eq "all" -or $Target -eq "midi_to_ogg") {
    Build-Target -name "midi_to_ogg" -script "midi_to_ogg.py" -useMusic21 $false
}

if ($Target -eq "all" -or $Target -eq "musicxml_to_ogg") {
    Build-Target -name "musicxml_to_ogg" -script "musicxml_to_ogg.py" -useMusic21 $true
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  지정된 타겟($Target)의 모든 빌드가 종료되었습니다." -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""

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
#   mml_to_midi       : MML ➔ MIDI 변환기 빌드
#   midi_to_mml       : MIDI ➔ MML 변환기 빌드
#   midi_to_ogg       : MIDI ➔ OGG 변환기 빌드 (music21 미사용으로 빠름)
#   musicxml_to_ogg   : MusicXML ➔ OGG 변환기 빌드 (시간이 수 분 소요됨)

Param(
    [ValidateSet("all", "midi_to_musicxml", "musicxml_to_midi", "mml_to_midi", "midi_to_mml", "midi_to_ogg", "musicxml_to_ogg", "musicxml_player")]
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
function Build-Target([string]$name, [string]$script, [bool]$useMusic21, [bool]$noconsole = $false) {
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
    
    if ($noconsole) {
        $args += "--noconsole"
    }
    
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

if ($Target -eq "all" -or $Target -eq "mml_to_midi") {
    Build-Target -name "mml_to_midi" -script "mml_to_midi.py" -useMusic21 $true
}

if ($Target -eq "all" -or $Target -eq "midi_to_mml") {
    Build-Target -name "midi_to_mml" -script "midi_to_mml.py" -useMusic21 $true
}

if ($Target -eq "all" -or $Target -eq "midi_to_ogg") {
    Build-Target -name "midi_to_ogg" -script "midi_to_ogg.py" -useMusic21 $false
}

if ($Target -eq "all" -or $Target -eq "musicxml_to_ogg") {
    Build-Target -name "musicxml_to_ogg" -script "musicxml_to_ogg.py" -useMusic21 $true
}

if ($Target -eq "all" -or $Target -eq "musicxml_player") {
    Build-Target -name "musicxml_player" -script "musicxml_player.py" -useMusic21 $true -noconsole $true
    
    # -----------------------------------------------------------------------
    # 무설치 포터블 배포 패키지 (ZIP) 자동 빌드 및 수집 프로세스
    # -----------------------------------------------------------------------
    Write-Host ""
    Write-Host "[패키징] 무설치 포터블 배포판(Portable Edition) ZIP 패키징을 시작합니다..." -ForegroundColor Cyan
    
    $TempDir = Join-Path $ScriptDir "musicxml_player_portable"
    $BinDir = Join-Path $TempDir "bin"
    $ZipPath = Join-Path $ScriptDir "musicxml-player-win64-portable.zip"
    
    # 기존 임시 폴더 및 ZIP이 존재한다면 제거 초기화
    if (Test-Path $TempDir) { Remove-Item -Recurse -Force $TempDir }
    if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
    
    # 폴더 구조 생성
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    
    # 1. 빌드 완료된 플레이어 EXE 복사
    if (Test-Path ".\musicxml_player.exe") {
        Copy-Item -Path ".\musicxml_player.exe" -Destination $TempDir -Force
        Write-Host "  [복사] musicxml_player.exe ➔ $TempDir" -ForegroundColor Gray
    }
    
    # 2. 필수 SoundFont 파일 복사
    if (Test-Path ".\FluidR3_GM.sf2") {
        Copy-Item -Path ".\FluidR3_GM.sf2" -Destination $TempDir -Force
        Write-Host "  [복사] FluidR3_GM.sf2 ➔ $TempDir" -ForegroundColor Gray
    }
    
    # 3. Fluidsynth CLI 및 모든 연관 DLL 동적 복사
    $FluidCmd = Get-Command fluidsynth -ErrorAction SilentlyContinue
    if ($FluidCmd) {
        $FluidDir = Split-Path $FluidCmd.Source -Parent
        if (Test-Path $FluidDir) {
            Copy-Item -Path (Join-Path $FluidDir "fluidsynth.exe") -Destination $BinDir -Force
            Copy-Item -Path (Join-Path $FluidDir "*.dll") -Destination $BinDir -Force
            Write-Host "  [복사] Fluidsynth 연동 모듈 및 DLL 복사 완료" -ForegroundColor Gray
        }
    } else {
        Write-Warning "시스템 PATH에서 fluidsynth를 찾지 못했습니다. 외부 라이브러리 팩 복사가 생략되었습니다."
    }
    
    # 4. FFmpeg 및 FFprobe CLI 바이너리 동적 복사 (내보내기 필수)
    $FfmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($FfmpegCmd) {
        $FfmpegDir = Split-Path $FfmpegCmd.Source -Parent
        if (Test-Path $FfmpegDir) {
            if (Test-Path (Join-Path $FfmpegDir "ffmpeg.exe")) {
                Copy-Item -Path (Join-Path $FfmpegDir "ffmpeg.exe") -Destination $BinDir -Force
            }
            if (Test-Path (Join-Path $FfmpegDir "ffprobe.exe")) {
                Copy-Item -Path (Join-Path $FfmpegDir "ffprobe.exe") -Destination $BinDir -Force
            }
            if (Test-Path (Join-Path $FfmpegDir "*.dll")) {
                Copy-Item -Path (Join-Path $FfmpegDir "*.dll") -Destination $BinDir -Force
            }
            Write-Host "  [복사] FFmpeg/FFprobe 음원 인코더 복사 완료" -ForegroundColor Gray
        }
    } else {
        Write-Warning "시스템 PATH에서 ffmpeg를 찾지 못했습니다. 음원 내보내기 팩 복사가 생략되었습니다."
    }
    
    # 5. ZIP 압축 아카이브 빌드 수행
    Write-Host "[압축] 배포판 압축 파일 생성 중: $ZipPath" -ForegroundColor Cyan
    Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipPath -Force
    
    # 생성 완료 후 임시 디렉터리 자원 청소
    Remove-Item -Recurse -Force $TempDir
    
    if (Test-Path $ZipPath) {
        $ZipSize = [math]::Round((Get-Item $ZipPath).Length / 1MB, 1)
        Write-Host ""
        Write-Host "[성공] 무설치 포터블 배포판 ZIP 패키지 생성 완료!" -ForegroundColor Green
        Write-Host "  위치 : $ZipPath" -ForegroundColor Green
        Write-Host "  크기 : ${ZipSize} MB" -ForegroundColor Green
        Write-Host ""
    }
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  지정된 타겟($Target)의 모든 빌드가 종료되었습니다." -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""

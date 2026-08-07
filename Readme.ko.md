# MusicXML & MIDI & OGG 변환 및 렌더링 도구 사용 설명서

이 프로젝트는 MIDI, MusicXML, OGG 등 음악 파일의 파싱, 상호 변환 및 오디오 렌더링을 위한 유틸리티 모음입니다. [music21](https://web.mit.edu/music21/) 라이브러리를 통해 악보 정보를 변환하고, [FluidSynth](https://www.fluidsynth.org/)를 통해 고품질의 OGG 음원으로 렌더링할 수 있습니다.

---

## 📂 프로젝트 구조 및 스크립트 요약

이 프로젝트는 다음과 같은 핵심 파이썬 스크립트와 가상환경 설정 및 빌드를 위한 PowerShell 스크립트로 구성되어 있습니다.

### 핵심 스크립트

| 스크립트 파일 | 변환 흐름 | 의존 라이브러리 | 외부 의존성 |
| :--- | :--- | :--- | :--- |
| [`midi_to_musicxml.py`](./midi_to_musicxml.py) | MIDI / 악보 ➔ MusicXML (`.xml`, `.mxl`) | `music21` | 없음 |
| [`musicxml_to_midi.py`](./musicxml_to_midi.py) | MusicXML / 악보 ➔ MIDI (`.mid`) | `music21` | 없음 |
| [`midi_to_ogg.py`](./midi_to_ogg.py) | MIDI ➔ OGG 오디오 (`.ogg`) | `pyfluidsynth`, `pydub` | FluidSynth, FFmpeg, SoundFont |
| [`musicxml_to_ogg.py`](./musicxml_to_ogg.py) | MusicXML ➔ OGG 오디오 (`.ogg`) | `music21`, `pyfluidsynth`, `pydub` | FluidSynth, FFmpeg, SoundFont |

### 가상환경 및 환경 구성 스크립트 (Windows PowerShell)

*   [`setup.ps1`](./setup.ps1): 외부 바이너리(FluidSynth, FFmpeg-full) 설치부터 Python 가상환경 구축 및 의존성 패키지 설치까지 **한 번에 자동으로 수행**하는 통합 설치 스크립트입니다. (관리자 권한 필요)
*   [`venv_run.ps1`](./venv_run.ps1): 현재 PowerShell 세션에서 생성된 `.venv` 가상환경을 활성화합니다. (종료 시 `deactivate` 입력)

---

## 🛠️ 환경 설정 및 설치 방법 (윈도우 기준)

### 통합 설치 실행 (권장)
Chocolatey, FluidSynth, FFmpeg-full 설치 및 Python 가상환경 생성과 파이썬 의존 라이브러리 설치까지 한 번에 완료해 주는 통합 스크립트입니다.

1. PowerShell을 **관리자 권한**으로 실행합니다.
2. 프로젝트 루트 디렉터리로 이동하여 아래 명령어를 실행합니다:
   ```powershell
   .\setup.ps1
   ```
   > **참고**: 스크립트 실행 정책 제한으로 실행이 안 되는 경우 다음 명령어로 우회하여 실행합니다:  
   > `powershell -ExecutionPolicy Bypass -File .\setup.ps1`

이 스크립트가 성공적으로 완료되면 Chocolatey, FluidSynth, FFmpeg가 설치되고 시스템 `PATH`에 등록되며, 프로젝트 폴더 안에 `.venv` 폴더가 생성되어 모든 파이썬 의존성 패키지 설치 및 연동 테스트까지 마칩니다.

### SoundFont 파일 배치
MIDI 음원을 오디오 파일로 합성하기 위해서는 사운드폰트(`.sf2`) 파일이 필수적입니다.
*   [`setup.ps1`](./setup.ps1) 스크립트를 실행하면 고품질 GM 사운드폰트인 [`FluidR3_GM.sf2`](./FluidR3_GM.sf2) 파일이 인터넷을 통해 자동으로 다운로드되어 프로젝트 루트 폴더에 배치됩니다.
*   스크립트나 빌드된 EXE 파일을 다른 디렉터리에서 실행할 경우, 해당 실행 경로에 [`FluidR3_GM.sf2`](./FluidR3_GM.sf2) 파일을 같이 배치하거나 실행 시 `--sf2` 옵션으로 경로를 별도 지정해야 합니다.

### 🎵 예제 샘플 파일 출처
변환 테스트용 예제 파일인 `minuet_in_g_major_back.xml`은 오픈소스 MuseTrainer 라이브러리의 [Minuet_in_G_Major_Bach.mxl](https://musetrainer.github.io/library/scores/Minuet_in_G_Major_Bach.mxl)을 원본으로 사용합니다. (퍼블릭 도메인 저작물)

---

## 🚀 프로젝트 사용법

사용 전에 반드시 가상환경을 활성화해야 합니다:
```powershell
.\venv_run.ps1
```

### 1. MIDI ↔ MusicXML 상호 변환

#### A. MIDI (또는 ABC, Kern 악보) ➔ MusicXML 변환
[`midi_to_musicxml.py`](./midi_to_musicxml.py)를 사용하여 다양한 형식을 MusicXML(`.xml` 또는 압축형 `.mxl`)로 변환합니다.

*   **기본 변환 (MIDI ➔ MusicXML)**:
    ```bash
    python midi_to_musicxml.py song.mid
    ```
    ➔ 입력 파일과 같은 폴더에 `song.xml`이 생성됩니다.
*   **출력 경로 지정**:
    ```bash
    python midi_to_musicxml.py song.mid output/song.xml
    ```
*   **압축 MusicXML(`.mxl`) 저장 (파일 크기 절약)**:
    ```bash
    python midi_to_musicxml.py song.mid -c
    # 또는
    python midi_to_musicxml.py song.mid output/song.mxl
    ```
*   **ABC 표기법 / Kern 형식 변환**:
    ```bash
    python midi_to_musicxml.py score.abc converted.xml
    python midi_to_musicxml.py score.krn output.mxl
    ```
*   **디렉터리 내 파일 일괄 변환 (Batch)**:
    ```bash
    python midi_to_musicxml.py --batch midi_files/ --output-dir xml_files/ --ext .mid .midi
    ```

#### B. MusicXML ➔ MIDI 변환
[`musicxml_to_midi.py`](./musicxml_to_midi.py)를 사용하여 MusicXML 파일을 MIDI 파일로 변환합니다.

*   **기본 변환**:
    ```bash
    python musicxml_to_midi.py song.xml
    ```
    ➔ 입력 파일과 같은 폴더에 `song.mid`가 생성됩니다.
*   **출력 경로 지정**:
    ```bash
    python musicxml_to_midi.py song.xml output/song.mid
    ```
*   **디렉터리 내 일괄 변환**:
    ```bash
    python musicxml_to_midi.py --batch xml_files/ --output-dir midi_files/
    ```

---

### 2. OGG 오디오 파일 변환 (렌더링)

이 변환 단계는 내부적으로 FluidSynth CLI를 호출하여 MIDI 데이터를 사운드폰트 기반으로 합성한 후 OGG 파일로 저장합니다.

#### A. MIDI ➔ OGG 변환
[`midi_to_ogg.py`](./midi_to_ogg.py)를 사용합니다.

*   **기본 변환**:
    ```bash
    python midi_to_ogg.py song.mid
    ```
    ➔ `FluidR3_GM.sf2`를 사용하여 변환된 `song.ogg` 파일이 생성됩니다.
*   **사운드폰트 파일 및 볼륨 게인 지정**:
    ```bash
    python midi_to_ogg.py song.mid out.ogg --sf2 path/to/soundfont.sf2 --gain 1.2
    ```
    *   `--gain`: 전체 마스터 볼륨 배율 (0.0 ~ 10.0, 기본값: `0.8`)
    *   `--sample-rate`: 샘플레이트 Hz 설정 (기본값: `44100`)

#### B. MusicXML ➔ OGG 변환
[`musicxml_to_ogg.py`](./musicxml_to_ogg.py)를 사용합니다. 내부적으로 MusicXML을 임시 MIDI로 1차 변환한 뒤, 이를 다시 FluidSynth를 통해 OGG 파일로 변환합니다.

*   **기본 변환**:
    ```bash
    python musicxml_to_ogg.py song.xml
    ```
    ➔ `song.ogg`가 생성되며, 중간에 생성된 임시 `song.mid` 파일은 자동 삭제됩니다.
*   **중간 변환된 임시 MIDI 파일 보존**:
    ```bash
    python musicxml_to_ogg.py song.xml --keep-mid
    ```
    ➔ OGG 파일과 함께 `song.mid` 파일도 보존됩니다.
*   **사운드폰트 및 상세 옵션 지정**:
    ```bash
    python musicxml_to_ogg.py song.xml out.ogg --sf2 FluidR3_GM.sf2 --gain 1.0 --sample-rate 48000
    ```

---

## 📦 EXE 파일 빌드 방법 (단일 실행 파일 제작)

파이썬 환경이 없는 환경에서도 변환 도구를 실행할 수 있도록 PyInstaller를 통해 단일 EXE 바이너리로 빌드할 수 있습니다. 

### 빌드 준비 사항
1.  **가상환경 활성화**: EXE 빌드 스크립트는 가상환경 내의 PyInstaller 패키지를 활용합니다. 반드시 가상환경이 켜진 세션에서 진행하세요.
    ```powershell
    .\venv_run.ps1
    ```
2.  가상환경 내에 PyInstaller가 없는 경우 스크립트 실행 과정에서 자동으로 `pip install pyinstaller`를 수행하므로 인터넷 연결이 필요합니다.

### 빌드 실행 방법
프로젝트에 포함된 통합 빌드 스크립트인 [`build.ps1`](./build.ps1)을 통해 타겟별로 혹은 일괄적으로 빌드할 수 있습니다.

```powershell
# 1. 전체 변환 도구 빌드 (4개 전체 일괄 빌드)
.\build.ps1 -Target all

# 2. 특정 변환 도구 개별 빌드
.\build.ps1 -Target midi_to_musicxml
.\build.ps1 -Target musicxml_to_midi
.\build.ps1 -Target midi_to_ogg
.\build.ps1 -Target musicxml_to_ogg
```

> **참고**: 가상환경을 미리 활성화하지 않았더라도 스크립트가 내부적으로 `.venv` 환경의 PyInstaller를 자동 감지하여 독립된 패키지로 빌드를 안전하게 수행합니다.

### 빌드 작동 상세 (내부 옵션)
빌드 스크립트 내부에서는 `pyinstaller` 명령에 다음 옵션을 결합하여 빌드를 수행합니다:
*   `--onefile`: 단일 실행 파일(`.exe`) 형태로 패키징합니다.
*   `--clean`: 빌드 전에 PyInstaller 캐시를 청소합니다.
*   `--collect-all music21`: `music21` 라이브러리의 복잡한 메타데이터 및 종속 리소스 파일을 실행 파일 내부에 완전하게 병합합니다. (변환 오류 방지 필수 옵션)
*   `--hidden-import`: 동적 임포트되는 내부 모듈(`music21.midi`, `music21.stream` 등)을 누락 없이 포함하도록 강제합니다.

### 빌드 결과물 위치
빌드가 성공적으로 끝나면 빌드 로그 하단에 녹색 완료 메시지가 나타납니다.
*   빌드 결과 파일(EXE)은 **프로젝트 루트 폴더(현재 디렉터리)**에 직접 생성됩니다.
    *   예: `.\musicxml_to_ogg.exe`
*   중간 빌드 부산물은 `build/` 디렉터리와 `.spec` 파일에 생성되며, 빌드가 끝난 뒤 안전하게 삭제해도 무방합니다. (PyInstaller가 임시로 빈 `dist/` 폴더를 생성할 수 있으나 결과 EXE 파일은 루트 폴더에 위치하므로 안심하고 삭제하셔도 됩니다.)

---

## ⚠️ EXE 배포 및 실행 시 유의사항

1.  **SoundFont 필수 동반**:
    오디오 변환 EXE 파일(`midi_to_ogg.exe`, `musicxml_to_ogg.exe`)을 다른 환경이나 폴더로 이동시켜 배포할 경우, 반드시 **`FluidR3_GM.sf2` 사운드폰트 파일을 실행 파일과 같은 경로에 함께 배포**해야 합니다. 사운드폰트가 없으면 음원 합성을 시작하지 못하고 에러가 발생합니다.
2.  **호스트 환경의 외부 프로그램 의존성**:
    *   오디오로 렌더링하는 실행 파일들은 내부적으로 호스트 OS의 **`fluidsynth` 및 `ffmpeg` 커맨드라인 CLI 도구**를 프로세스로 호출합니다.
    *   따라서 EXE를 실행할 대상 PC에도 반드시 `fluidsynth`와 `ffmpeg`가 설치되어 있고, 환경 변수 `PATH` 상에 등록되어 있어야 에러 없이 동작합니다.
3.  **첫 실행 속도**:
    `--onefile` 옵션으로 패키징된 실행 파일은 최초 실행 시 임시 디렉터리에 압축되어 있던 라이브러리 코드를 해제하는 물리적인 시간이 약간 소요됩니다. 이는 정상적인 동작입니다.

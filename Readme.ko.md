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
| [`mml_to_midi.py`](./mml_to_midi.py) | MML (`.mml`, 3MLE 형식) ➔ MIDI (`.mid`) | `music21` | 없음 |
| [`midi_to_mml.py`](./midi_to_mml.py) | MIDI (`.mid`) ➔ MML (`.mml`, 3MLE 형식) | `music21` | 없음 |
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

### 2. MML ➔ MIDI 변환

[`mml_to_midi.py`](./mml_to_midi.py)를 사용해 3MLE 형식의 MML 텍스트 악보(`.mml`, `[Settings]` / `[ChannelN]` 섹션 구조)를 MIDI로 변환합니다. 각 `[ChannelN]` 블록은 별도의 MIDI 트랙으로 변환되며, 음길이/부점, 옥타브(`<`/`>`), 음량(`v`), 악기(`@`), 타이(`&`) 명령을 해석합니다. `[3MLE EXTENSION]` 블록(압축 메타데이터)은 사용하지 않습니다.

*   **기본 변환**:
    ```bash
    python mml_to_midi.py song.mml
    ```
    ➔ 같은 위치에 `song.mid`가 생성됩니다.
*   **출력 경로 및 템포 지정**:
    ```bash
    python mml_to_midi.py song.mml output/song.mid --bpm 108
    ```
    *   `--bpm`: MML 안에 템포(`t`) 명령이 없을 때 사용할 기본 템포 (기본값: `120`).

변환된 `.mid` 파일은 아래의 GUI 플레이어(`musicxml_player.py`)로 바로 재생하거나, [`midi_to_ogg.py`](./midi_to_ogg.py)로 오디오 파일로 렌더링할 수 있습니다.

**관련 패키지에 대해**: 이 3MLE 형식의 MML 방언(`[Settings]` / `[ChannelN]` / `[3MLE EXTENSION]` 구조)을 지원하는 범용적이고 잘 관리되는 PyPI 패키지는 따로 없습니다. 마비노기/3MLE 커뮤니티에서 쓰이는 특수한 텍스트 포맷이라 표준화되어 있지 않기 때문입니다. 그래서 [`mml_to_midi.py`](./mml_to_midi.py)와 [`midi_to_mml.py`](./midi_to_mml.py)는 이미 프로젝트가 의존하는 `music21` 위에 직접 만든 전용 파서/생성기입니다.

반대 방향인 MIDI ➔ MML 변환도 [`midi_to_mml.py`](./midi_to_mml.py)로 지원합니다:

*   **기본 변환**:
    ```bash
    python midi_to_mml.py song.mid
    ```
    ➔ 같은 위치에 `song.mml`이 생성되며, MIDI 트랙마다 `[ChannelN]` 블록 하나씩 만들어집니다. 음길이/부점, 옥타브, 음량, 악기, 타이가 MIDI 데이터로부터 재구성되고, 마디 구분(`/*M n */`) 주석도 함께 붙습니다.
*   **출력 경로 지정**:
    ```bash
    python midi_to_mml.py song.mid output/song.mml
    ```
*   **한계점**: MML 채널은 트래커 채널처럼 한 번에 한 음만 낼 수 있는 단선율입니다. 만약 한 MIDI 트랙 안에 (서로 다른 트랙이 아니라) 실제로 겹치는 두 개의 독립된 음이 있다면, 더 낮거나 짧게 겹치는 쪽을 잘라내어 재생 가능한 상태로 만듭니다. 그 외의 경우는 `mml_to_midi.py`를 통해 원본과 동일하게 왕복 변환됩니다. `[3MLE EXTENSION]` 블록(3MLE 내부 압축 체크섬)은 생성하지 않는데, 이는 `mml_to_midi.py`나 일반적인 MML 재생기로 재생하는 데는 영향이 없지만, 실제 3MLE GUI 에디터로 다시 불러올 경우 일부 3MLE 전용 기능은 인식되지 않을 수 있습니다.

---

### 3. OGG / MP3 / WAV 오디오 파일 변환 (렌더링)

이 변환 단계는 내부적으로 FluidSynth CLI를 호출하여 MIDI 데이터를 사운드폰트 기반으로 합성한 후 지정한 포맷의 오디오 파일로 저장합니다.
*   **지원 형식**: OGG, MP3, WAV (출력 파일의 확장자에 따라 자동 판정되거나 `--format` 옵션으로 수동 지정 가능, 기본값은 **OGG**)
*   **MP3 변환 참고**: MP3 출력을 사용하려면 시스템에 `pydub` 파이썬 패키지와 외부 도구인 `FFmpeg`가 설치되어 있어야 합니다. (통합 설치 스크립트 `setup.ps1`을 사용했다면 이미 완벽하게 설정되어 있습니다.)

#### A. MIDI ➔ 오디오 변환
[`midi_to_ogg.py`](./midi_to_ogg.py)를 사용합니다. (파일명은 OGG 형식이지만, MP3/WAV 출력도 완전히 지원합니다.)

*   **기본 변환 (OGG 출력)**:
    ```bash
    python midi_to_ogg.py song.mid
    ```
    ➔ `FluidR3_GM.sf2`를 사용하여 `song.ogg` 파일이 생성됩니다.
*   **WAV 또는 MP3 포맷 지정 출력**:
    ```bash
    # 출력 파일 확장자를 통한 자동 판정
    python midi_to_ogg.py song.mid song.wav
    python midi_to_ogg.py song.mid song.mp3

    # --format 옵션을 통한 명시적 변환
    python midi_to_ogg.py song.mid --format mp3
    ```
*   **상세 옵션 지정**:
    ```bash
    python midi_to_ogg.py song.mid out.mp3 --sf2 path/to/soundfont.sf2 --gain 1.2
    ```
    *   `--gain`: 전체 마스터 볼륨 배율 (0.0 ~ 10.0, 기본값: `0.8`)
    *   `--sample-rate`: 샘플레이트 Hz 설정 (기본값: `44100`)

#### B. MusicXML ➔ 오디오 변환
[`musicxml_to_ogg.py`](./musicxml_to_ogg.py)를 사용합니다. 내부적으로 MusicXML을 임시 MIDI로 1차 변환한 뒤, 이를 다시 오디오 파일로 최종 합성합니다.

*   **기본 변환 (OGG 출력)**:
    ```bash
    python musicxml_to_ogg.py song.xml
    ```
    ➔ `song.ogg`가 생성되며, 중간에 생성된 임시 `song.mid` 파일은 자동 삭제됩니다.
*   **WAV 또는 MP3 포맷 지정 출력**:
    ```bash
    # 출력 파일 확장자를 통한 자동 판정
    python musicxml_to_ogg.py song.xml song.wav
    python musicxml_to_ogg.py song.xml song.mp3

    # --format 옵션을 통한 명시적 변환
    python musicxml_to_ogg.py song.xml --format wav
    ```
*   **임시 MIDI 파일 보존 및 상세 옵션 지정**:
    ```bash
    python musicxml_to_ogg.py song.xml out.mp3 --keep-mid --sf2 FluidR3_GM.sf2 --gain 1.0 --sample-rate 48000
    ```

---

## 🖥️ PySide6 GUI 플레이어 사용법 (`musicxml_player.py`)

MusicXML, MIDI, MML 파일을 열어 사운드폰트 기반으로 감상하고, 이를 다양한 형식으로 저장(Export)할 수 있는 직관적인 GUI 데스크톱 플레이어 애플리케이션입니다.

*   **실행 방법**:
    가상환경이 활성화된 상태에서 아래 명령어를 실행합니다.
    ```bash
    python musicxml_player.py
    ```
*   **핵심 기능**:
    *   **파일 불러오기**: 메뉴 바의 `파일` -> `불러오기(Open)`를 통해 MusicXML(`.xml`, `.mxl`), MIDI(`.mid`, `.midi`), MML(`.mml`, 3MLE 형식) 파일을 불러옵니다. MML 파일은 재생 전에 [`mml_to_midi.py`](./mml_to_midi.py)를 통해 즉시 MIDI로 변환됩니다.
    *   **실시간 오디오 합성 재생**: FluidSynth 플레이어를 활용하여 즉각적인 실시간 재생, 일시정지, 정지 기능을 제어합니다.
    *   **볼륨 제어**: 하단의 볼륨 슬라이더를 조정하여 신디사이저 마스터 볼륨 게인을 실시간으로 0.0~1.0 배율로 조절합니다.
    *   **커스텀 사운드폰트 교체**: 메인 화면의 `사운드폰트 변경...` 단추를 눌러 다른 커스텀 `.sf2` 음색 파일로 동적 교체할 수 있습니다. (기본값: 프로젝트 루트 내의 `FluidR3_GM.sf2`)
    *   **다른 형식으로 저장하기(내보내기)**: 메뉴 바의 `파일` -> `저장하기(Export)`를 눌러 불러온 파일을 `MIDI`, `MusicXML`, `MML`, `OGG`, `MP3`, `WAV` 중 원하는 포맷으로 변환 저장합니다. 세 가지 악보 형식(MusicXML/MIDI/MML) 사이는 필요 시 [`midi_to_mml.py`](./midi_to_mml.py) / [`mml_to_midi.py`](./mml_to_midi.py) / [`midi_to_musicxml.py`](./midi_to_musicxml.py) / [`musicxml_to_midi.py`](./musicxml_to_midi.py)를 자동으로 거쳐 서로 변환됩니다.
    *   **채널 패널 & 피아노롤**: 파일을 불러오면 `music21`로 분석해 채널(트랙)마다 다른 색으로 구분된 피아노롤을 보여주고, 채널별 행에 현재 지정된 GM(General MIDI) 악기를 표시합니다. 채널 드롭다운에서 다른 악기를 고르면 해당 채널의 악보 전체에 악기가 적용되며, 재생 중 실시간으로 소리가 바뀌지는 않고 **다음에 Play를 누를 때부터** 반영됩니다(특정 위치로 이동/탐색하는 기능은 없고, 재생은 항상 처음부터 다시 시작됩니다). 악기를 바꾼 뒤 `파일` -> `저장하기(Export)`를 하면 어떤 포맷으로 저장하든 그 변경이 함께 반영됩니다(예: MML로 저장 시 해당 채널의 `@` 악기 번호가 바뀐 값으로 기록됨).
*   **💡 윈도우 연결 프로그램 및 자동 재생 지원 (더블클릭 실행)**:
    *   윈도우 탐색기에서 `.mxl`, `.xml`, `.mid`, `.midi`, `.mml` 파일의 연결 프로그램으로 빌드된 `musicxml_player.exe` 파일을 등록해 두면, 악보 파일을 **더블클릭하는 즉시 프로그램이 실행되며 자동으로 소리가 즉시 재생(Auto-Play)**됩니다.

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
# 1. 전체 변환 도구 및 GUI 플레이어 빌드 (일괄 빌드)
.\build.ps1 -Target all

# 2. GUI 플레이어 개별 빌드 (콘솔 창 없는 윈도우 전용 EXE)
.\build.ps1 -Target musicxml_player

# 3. 특정 변환 도구 개별 빌드
.\build.ps1 -Target midi_to_musicxml
.\build.ps1 -Target musicxml_to_midi
.\build.ps1 -Target mml_to_midi
.\build.ps1 -Target midi_to_mml
.\build.ps1 -Target midi_to_ogg
.\build.ps1 -Target musicxml_to_ogg
```

> **참고**: 가상환경을 미리 활성화하지 않았더라도 스크립트가 내부적으로 `.venv` 환경의 PyInstaller를 자동 감지하여 독립된 패키지로 빌드를 안전하게 수행합니다.

### 빌드 작동 상세 (내부 옵션)
빌드 스크립트 내부에서는 `pyinstaller` 명령에 다음 옵션을 결합하여 빌드를 수행합니다:
*   `--onefile`: 단일 실행 파일(`.exe`) 형태로 패키징합니다.
*   `--clean`: 빌드 전에 PyInstaller 캐시를 청소합니다.
*   `--noconsole` (GUI 전용): `musicxml_player` 빌드 시 적용되며, 실행 시 터미널(검은색 콘솔 창)이 뜨지 않도록 지정합니다.
*   `--collect-all music21`: `music21` 라이브러리의 복잡한 메타데이터 및 종속 리소스 파일을 실행 파일 내부에 완전하게 병합합니다. (변환 오류 방지 필수 옵션)
*   `--hidden-import`: 동적 임포트되는 내부 모듈(`music21.midi`, `music21.stream` 등)을 누락 없이 포함하도록 강제합니다.

### 빌드 결과물 위치
빌드가 성공적으로 끝나면 빌드 로그 하단에 녹색 완료 메시지가 나타납니다.
*   빌드 결과 파일(EXE)은 **프로젝트 루트 폴더(현재 디렉터리)**에 직접 생성됩니다.
    *   예: `.\musicxml_to_ogg.exe`, `.\musicxml_player.exe`
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

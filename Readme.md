# MusicXML & MIDI & OGG Conversion and Rendering Tools User Guide

This project is a collection of utilities for parsing, cross-converting, and rendering music files such as MIDI, MusicXML, and OGG. It uses the [music21](https://web.mit.edu/music21/) library to convert score sheet information and [FluidSynth](https://www.fluidsynth.org/) to render high-quality OGG audio files.

---

## 📂 Project Structure and Script Summary

This project consists of core Python scripts and helper PowerShell scripts for setting up virtual environments and building executables.

### Core Scripts

| Script File | Conversion Flow | Dependency Libraries | External Dependencies |
| :--- | :--- | :--- | :--- |
| [`midi_to_musicxml.py`](./midi_to_musicxml.py) | MIDI / Score ➔ MusicXML (`.xml`, `.mxl`) | `music21` | None |
| [`musicxml_to_midi.py`](./musicxml_to_midi.py) | MusicXML / Score ➔ MIDI (`.mid`) | `music21` | None |
| [`mml_to_midi.py`](./mml_to_midi.py) | MML (`.mml`, 3MLE-style) ➔ MIDI (`.mid`) | `music21` | None |
| [`midi_to_mml.py`](./midi_to_mml.py) | MIDI (`.mid`) ➔ MML (`.mml`, 3MLE-style) | `music21` | None |
| [`midi_to_ogg.py`](./midi_to_ogg.py) | MIDI ➔ OGG Audio (`.ogg`) | `pyfluidsynth`, `pydub` | FluidSynth, FFmpeg, SoundFont |
| [`musicxml_to_ogg.py`](./musicxml_to_ogg.py) | MusicXML ➔ OGG Audio (`.ogg`) | `music21`, `pyfluidsynth`, `pydub` | FluidSynth, FFmpeg, SoundFont |

### Environment Setup and Build Scripts (Windows PowerShell)

*   [`setup.ps1`](./setup.ps1): An integrated installation script that automatically installs external binaries (FluidSynth, FFmpeg-full via Chocolatey), creates a Python virtual environment, and installs Python package dependencies **in one step**. (Requires administrator privileges)
*   [`venv_run.ps1`](./venv_run.ps1): Activates the created `.venv` virtual environment in the current PowerShell session. (Type `deactivate` to exit)

---

## 🛠️ Environment Setup & Installation Guide (Windows)

### Integrated Installation (Recommended)
This script completes everything at once: installs Chocolatey, FluidSynth, FFmpeg-full, creates the Python virtual environment, and installs all dependency libraries.

1. Run PowerShell as **Administrator**.
2. Navigate to the project root directory and run:
   ```powershell
   .\setup.ps1
   ```
   > **Note**: If execution is blocked due to the Execution Policy, bypass it using:  
   > `powershell -ExecutionPolicy Bypass -File .\setup.ps1`

Upon successful completion, Chocolatey, FluidSynth, and FFmpeg will be installed and added to the system `PATH`. A `.venv` folder will be created inside the project directory, and all Python dependencies will be installed and verified.

### SoundFont File Placement
A SoundFont (`.sf2`) file is required to synthesize MIDI to audio files.
*   Running the [`setup.ps1`](./setup.ps1) script automatically downloads the high-quality GM SoundFont [`FluidR3_GM.sf2`](./FluidR3_GM.sf2) and places it in the project root folder.
*   If you move the script or build EXE files to another directory, you must copy [`FluidR3_GM.sf2`](./FluidR3_GM.sf2) to the same directory or specify its path using the `--sf2` option when running.

### 🎵 Sample File Credit
The test file `minuet_in_g_major_bach.xml` is sourced from the open-source MuseTrainer library: [Minuet_in_G_Major_Bach.mxl](https://musetrainer.github.io/library/scores/Minuet_in_G_Major_Bach.mxl). (Public Domain)

---

## 🚀 How to Use

Always activate the virtual environment before use:
```powershell
.\venv_run.ps1
```

### 1. MIDI ↔ MusicXML Cross-Conversion

#### A. MIDI (or ABC, Kern) ➔ MusicXML Conversion
Converts various formats into MusicXML (`.xml` or compressed `.mxl`) using [`midi_to_musicxml.py`](./midi_to_musicxml.py).

*   **Basic Conversion (MIDI ➔ MusicXML)**:
    ```bash
    python midi_to_musicxml.py song.mid
    ```
    ➔ Creates `song.xml` in the same directory.
*   **Specify Output Path**:
    ```bash
    python midi_to_musicxml.py song.mid output/song.xml
    ```
*   **Save as Compressed MusicXML (`.mxl`)**:
    ```bash
    python midi_to_musicxml.py song.mid -c
    # or
    python midi_to_musicxml.py song.mid output/song.mxl
    ```
*   **Convert ABC / Kern formats**:
    ```bash
    python midi_to_musicxml.py score.abc converted.xml
    python midi_to_musicxml.py score.krn output.mxl
    ```
*   **Batch Convert a Directory**:
    ```bash
    python midi_to_musicxml.py --batch midi_files/ --output-dir xml_files/ --ext .mid .midi
    ```

#### B. MusicXML ➔ MIDI Conversion
Converts MusicXML files to MIDI files using [`musicxml_to_midi.py`](./musicxml_to_midi.py).

*   **Basic Conversion**:
    ```bash
    python musicxml_to_midi.py song.xml
    ```
    ➔ Creates `song.mid` in the same directory.
*   **Specify Output Path**:
    ```bash
    python musicxml_to_midi.py song.xml output/song.mid
    ```
*   **Batch Convert a Directory**:
    ```bash
    python musicxml_to_midi.py --batch xml_files/ --output-dir midi_files/
    ```

---

### 2. MML ➔ MIDI Conversion

Converts 3MLE-style MML text scores (`.mml`, with `[Settings]` / `[ChannelN]` sections) into MIDI using [`mml_to_midi.py`](./mml_to_midi.py). Each `[ChannelN]` block becomes its own MIDI track; note length, octave (`<`/`>`), volume (`v`), instrument (`@`), and ties (`&`) are all interpreted. The `[3MLE EXTENSION]` block (compressed metadata) is ignored.

*   **Basic Conversion**:
    ```bash
    python mml_to_midi.py song.mml
    ```
    ➔ Creates `song.mid` in the same directory.
*   **Specify Output Path and Tempo**:
    ```bash
    python mml_to_midi.py song.mml output/song.mid --bpm 108
    ```
    *   `--bpm`: Fallback tempo used when the MML has no `t` (tempo) command (default: `120`).

Once you have a `.mid`, play it with the GUI player (`musicxml_player.py`, see below), or render it to audio with [`midi_to_ogg.py`](./midi_to_ogg.py).

**Note on packages**: there is no widely-used, well-maintained PyPI package for this specific 3MLE-style MML dialect (the `[Settings]` / `[ChannelN]` / `[3MLE EXTENSION]` structure is a niche, game-community text format, not a standardized one). [`mml_to_midi.py`](./mml_to_midi.py) and [`midi_to_mml.py`](./midi_to_mml.py) are therefore custom parsers/generators built on top of `music21`, which the project already depends on.

The reverse direction — MIDI ➔ MML — is also supported, via [`midi_to_mml.py`](./midi_to_mml.py):

*   **Basic Conversion**:
    ```bash
    python midi_to_mml.py song.mid
    ```
    ➔ Creates `song.mml` in the same directory, one `[ChannelN]` block per MIDI track, with note lengths/dots, octave, volume, instrument, and ties re-derived from the MIDI data, plus measure (`/*M n */`) comments.
*   **Specify Output Path**:
    ```bash
    python midi_to_mml.py song.mid output/song.mml
    ```
*   **Limitation**: an MML channel is monophonic (one note at a time), like a tracker channel. If a MIDI track contains real polyphony (two independent overlapping notes in the same track — as opposed to notes belonging to different tracks), the lower/shorter-overlapping note is dropped so the channel stays playable. Everything else round-trips losslessly through `mml_to_midi.py`. The `[3MLE EXTENSION]` block (a 3MLE-internal compressed checksum) is not generated; this doesn't affect playback with `mml_to_midi.py` or generic MML players, but a few 3MLE-editor-specific features may not be recognized if you re-import the file into the original 3MLE GUI tool.

---

### 3. OGG / MP3 / WAV Audio File Conversion (Rendering)

This process calls the FluidSynth CLI internally to synthesize MIDI data using a SoundFont and outputs it as an audio file.
*   **Supported Formats**: OGG, MP3, WAV (Automatically determined by the output file extension, or manually set using the `--format$옵션`. Default is **OGG**).
*   **Note for MP3 Conversion**: To output to MP3, the `pydub` package must be installed and `FFmpeg` must be in the system path. (If you ran the `setup.ps1` script, this is already configured).

#### A. MIDI ➔ Audio Conversion
Uses [`midi_to_ogg.py`](./midi_to_ogg.py). (Fully supports MP3 and WAV outputs, though the name is `midi_to_ogg.py`).

*   **Basic Conversion (OGG Output)**:
    ```bash
    python midi_to_ogg.py song.mid
    ```
    ➔ Synthesizes `song.ogg` using `FluidR3_GM.sf2`.
*   **Specify WAV or MP3 Output**:
    ```bash
    # Automatic detection via file extension
    python midi_to_ogg.py song.mid song.wav
    python midi_to_ogg.py song.mid song.mp3

    # Explicit conversion using --format option
    python midi_to_ogg.py song.mid --format mp3
    ```
*   **Specify Custom Settings**:
    ```bash
    python midi_to_ogg.py song.mid out.mp3 --sf2 path/to/soundfont.sf2 --gain 1.2
    ```
    *   `--gain`: Master volume ratio (0.0 to 10.0, default: `0.8`)
    *   `--sample-rate`: Sample rate in Hz (default: `44100`)

#### B. MusicXML ➔ Audio Conversion
Uses [`musicxml_to_ogg.py`](./musicxml_to_ogg.py). It converts MusicXML to an intermediate MIDI file, then renders it to the final audio format.

*   **Basic Conversion (OGG Output)**:
    ```bash
    python musicxml_to_ogg.py song.xml
    ```
    ➔ Creates `song.ogg`. The intermediate `song.mid` file is deleted automatically.
*   **Specify WAV or MP3 Output**:
    ```bash
    # Automatic detection via file extension
    python musicxml_to_ogg.py song.xml song.wav
    python musicxml_to_ogg.py song.xml song.mp3

    # Explicit conversion using --format option
    python musicxml_to_ogg.py song.xml --format wav
    ```
*   **Keep Intermediate MIDI & Specify Options**:
    ```bash
    python musicxml_to_ogg.py song.xml out.mp3 --keep-mid --sf2 FluidR3_GM.sf2 --gain 1.0 --sample-rate 48000
    ```

---

## 🖥️ PySide6 GUI Player (`musicxml_player.py`)

An intuitive GUI desktop player application that lets you open MusicXML, MIDI, and MML files, listen to them via SoundFont rendering, and export them into various formats.

*   **How to Run**:
    Ensure the virtual environment is active and run:
    ```bash
    python musicxml_player.py
    ```
*   **Key Features**:
    *   **Open File**: Use `File -> Open...` on the menu bar to open MusicXML (`.xml`, `.mxl`), MIDI (`.mid`, `.midi`), or MML (`.mml`, 3MLE-style) files. MML files are converted to MIDI on the fly via [`mml_to_midi.py`](./mml_to_midi.py) before playback.
    *   **Real-time Synthesis**: Play, pause, or stop playback instantly using FluidSynth.
    *   **Volume Control**: Adjust the volume slider to dynamically change the synthesizer gain (0.0 to 1.0).
    *   **Dynamic SoundFont Selection**: Click `Change SoundFont...` on the screen to load another `.sf2` sound file. (Default: `FluidR3_GM.sf2` in the root folder)
    *   **Export File**: Select `File -> Export As...` to save the loaded file as `MIDI`, `MusicXML`, `MML`, `OGG`, `MP3`, or `WAV` — converting between any of the three score formats (via [`midi_to_mml.py`](./midi_to_mml.py) / [`mml_to_midi.py`](./mml_to_midi.py) / [`midi_to_musicxml.py`](./midi_to_musicxml.py) / [`musicxml_to_midi.py`](./musicxml_to_midi.py) as needed) as well as rendering to audio.
    *   **Channel Panel & Piano Roll**: every loaded file is analyzed with `music21` and shown as a color-coded piano roll (one color per channel/track), with a per-channel row listing its current General MIDI instrument. Picking a different instrument from a channel's dropdown updates that channel for the *whole* piece; the change takes effect the next time you press Play (no live mid-playback switching, and playback always restarts from the beginning — there's no seek/scrub). Once you change an instrument, `File -> Export As...` also reflects it in whatever format you save to (e.g. the MML channel's `@` instrument number is updated).
*   **💡 File Association & Auto-Play Support**:
    *   You can set the built `musicxml_player.exe` as the default program for `.mxl`, `.xml`, `.mid`, `.midi`, and `.mml` files in Windows Explorer. When you **double-click any score file, the player will start and automatically play the audio immediately (Auto-Play)**.

---

## 📦 Building Standalone Executables (EXE)

You can build standalone EXE files using PyInstaller so that the tools can be executed on systems without Python installed.

### Build Prerequisites
1.  **Activate Virtual Environment**: The build script utilizes PyInstaller inside the virtual environment. Always execute inside the activated virtual environment session:
    ```powershell
    .\venv_run.ps1
    ```
2.  If PyInstaller is not installed in the virtual environment, the build script will automatically run `pip install pyinstaller` (requires internet connection).

### How to Build
You can build targets individually or all at once using [`build.ps1`](./build.ps1).

```powershell
# 1. Build all conversion utilities and the GUI player
.\build.ps1 -Target all

# 2. Build the GUI player only (windowed EXE without console window)
.\build.ps1 -Target musicxml_player

# 3. Build a specific utility only
.\build.ps1 -Target midi_to_musicxml
.\build.ps1 -Target musicxml_to_midi
.\build.ps1 -Target mml_to_midi
.\build.ps1 -Target midi_to_mml
.\build.ps1 -Target midi_to_ogg
.\build.ps1 -Target musicxml_to_ogg
```

> **Note**: Even if you did not manually activate the virtual environment beforehand, the script will detect the `.venv` PyInstaller and perform a clean standalone build.

### Build Details (Internal PyInstaller Options)
The build script automatically applies these flags:
*   `--onefile`: Packages the application into a single standalone `.exe` file.
*   `--clean`: Clears PyInstaller cache before building.
*   `--noconsole` (GUI only): Hides the console terminal when launching the GUI.
*   `--collect-all music21`: Gathers and packages all `music21` configuration files and assets inside the executable. (Required to prevent runtime errors)
*   `--hidden-import`: Ensures dynamically imported modules (e.g., `music21.midi`) are fully included.

### Output Location
Upon completion, a success message will appear in green in the terminal.
*   The final EXE files are generated directly in the **project root folder**.
    *   Example: `.\musicxml_to_ogg.exe`, `.\musicxml_player.exe`
*   Intermediate build artifacts inside `build/` and `.spec` files can be safely deleted.

---

## ⚠️ Notes on Deploying & Executing EXE Files

1.  **SoundFont File Required**:
    If you distribute the audio-rendering executables (`midi_to_ogg.exe`, `musicxml_to_ogg.exe`, `musicxml_player.exe`) to other folders or PCs, **you must include the `FluidR3_GM.sf2` file in the same directory**. Otherwise, synthesis will fail.
2.  **External Program Dependencies**:
    *   The audio-rendering utilities invoke the host system's **`fluidsynth` and `ffmpeg` command-line tools**.
    *   Therefore, the target PC must have `fluidsynth` and `ffmpeg` installed and registered in the system `PATH` env.
3.  **Initial Startup Time**:
    Standalone executables packaged with `--onefile` extract libraries to a temporary directory on their first execution. This might take a few seconds and is normal behavior.

"""
musicxml_to_ogg.py
-------------------
MusicXML 파일을 OGG 오디오 파일로 변환합니다.

변환 파이프라인:
    MusicXML ─[music21]→ MIDI ─[fluidsynth CLI]→ OGG

실행 위치: MusicXml/ 디렉터리 안에서 실행하세요.

사용법:
    python musicxml_to_ogg.py <input.xml> [output.ogg] [--sf2 <soundfont.sf2>] [--gain <0.0~10.0>]

예시:
    python musicxml_to_ogg.py Minuet_in_G.xml
    python musicxml_to_ogg.py Minuet_in_G.xml out.ogg --sf2 FluidR3_GM.sf2 --gain 1.0
"""

import argparse
import subprocess
import sys
from pathlib import Path

try:
    from music21 import converter
except ImportError:
    print("오류: music21 패키지가 설치되지 않았습니다.")
    print("  pip install music21")
    sys.exit(1)

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

DEFAULT_SF2 = "FluidR3_GM.sf2"
DEFAULT_GAIN = 0.8
DEFAULT_SAMPLE_RATE = 44100


def musicxml_to_ogg(
    xml_path: str,
    output: str = None,
    sf2_path: str = DEFAULT_SF2,
    gain: float = DEFAULT_GAIN,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    keep_mid: bool = False,
    format: str = None,
) -> Path:
    """
    MusicXML 파일을 OGG, MP3 또는 WAV 오디오 파일로 변환합니다.

    Parameters
    ----------
    xml_path   : 입력 MusicXML 파일 경로 (.xml / .mxl)
    output     : 출력 파일 경로 (생략 시 입력과 같은 이름으로 포맷에 맞춰 자동 생성)
    sf2_path   : SoundFont 파일 경로 (기본: FluidR3_GM.sf2)
    gain       : FluidSynth 마스터 볼륨 게인 0.0~10.0 (기본: 0.8)
    sample_rate: 샘플레이트 Hz (기본: 44100)
    keep_mid   : True 이면 임시 MIDI 파일을 삭제하지 않음
    format     : 출력 포맷 ('ogg', 'mp3', 'wav'. 생략 시 출력 파일 확장자에 따름)

    Returns
    -------
    Path : 생성된 오디오 파일 경로
    """
    xml = Path(xml_path)
    if not xml.exists():
        print(f"오류: 파일을 찾을 수 없습니다 — {xml}")
        sys.exit(1)

    sf2 = Path(sf2_path)
    if not sf2.exists():
        # relative path 이고 존재하지 않는 경우 후보 경로들 탐색
        if not sf2.is_absolute():
            # 1. 실행 및 스크립트/EXE 파일 경로 기준 설정
            if getattr(sys, 'frozen', False):
                script_dir = Path(sys.executable).parent
            else:
                script_dir = Path(__file__).parent
            
            candidates = [
                Path.cwd() / sf2.name,                                # 실행 경로 (CWD) 기준
                script_dir / sf2.name,                                # 스크립트/EXE 디렉터리 기준
                script_dir / "MusicXml" / sf2.name,                   # 하위 MusicXml 폴더 기준
                script_dir.parent / "MusicXml" / sf2.name,            # 상위의 MusicXml 폴더 기준
                Path(sys.argv[0]).parent / sf2.name                   # 실행 인자의 부모 디렉터리 기준
            ]

            for cand in candidates:
                if cand.exists():
                    sf2 = cand
                    break

    if not sf2.exists():
        print(f"오류: SoundFont 파일을 찾을 수 없습니다 — {sf2_path}")
        print("  FluidR3_GM.sf2 를 실행 경로, 스크립트(또는 EXE) 경로, 또는 MusicXml/ 폴더에 넣거나")
        print("  --sf2 옵션으로 올바른 경로를 지정하세요.")
        sys.exit(1)

    # 출력 포맷 결정
    out_format = "ogg"
    if format:
        out_format = format.lower()
    elif output:
        suffix = Path(output).suffix.lower()
        if suffix == ".mp3":
            out_format = "mp3"
        elif suffix == ".wav":
            out_format = "wav"
        elif suffix in (".ogg", ".oga"):
            out_format = "ogg"

    mid = xml.with_suffix(".mid")
    out_file = Path(output) if output else xml.with_suffix("." + out_format)

    # ── 1단계: MusicXML → MIDI ──────────────────────────────────────────────
    print(f"[1/2] MusicXML → MIDI : {xml} → {mid}")
    score = converter.parse(str(xml))
    score.write("midi", fp=str(mid))
    print(f"      MIDI 저장 완료: {mid}")

    # ── 2단계: MIDI → 오디오 렌더링 ──────────────────────────────────────────
    if out_format == "mp3":
        if AudioSegment is None:
            print("오류: mp3 변환에 필요한 pydub 라이브러리가 설치되어 있지 않습니다.")
            print("  pip install pydub audioop-lts")
            sys.exit(1)
            
        temp_wav = xml.with_suffix(".wav")
        print(f"[2/2] MIDI → WAV (임시): {mid} → {temp_wav}")
        cmd = [
            "fluidsynth",
            "-n",
            "-i",
            "-q",
            "-F", str(temp_wav),
            "-T", "wav",
            "-r", str(sample_rate),
            "-g", str(gain),
            str(sf2),
            str(mid),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("fluidsynth 오류:")
            print(result.stderr)
            sys.exit(1)

        print(f"      WAV → MP3 변환  : {temp_wav} → {out_file}")
        try:
            sound = AudioSegment.from_wav(str(temp_wav))
            sound.export(str(out_file), format="mp3", bitrate="192k")
        except Exception as e:
            print(f"MP3 인코딩 오류 (FFmpeg가 시스템에 올바르게 설치되어 있는지 확인해 주세요): {e}")
            sys.exit(1)
        finally:
            temp_wav.unlink(missing_ok=True)
            
    elif out_format == "wav":
        print(f"[2/2] MIDI → WAV      : {mid} → {out_file}")
        cmd = [
            "fluidsynth",
            "-n",
            "-i",
            "-q",
            "-F", str(out_file),
            "-T", "wav",
            "-r", str(sample_rate),
            "-g", str(gain),
            str(sf2),
            str(mid),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("fluidsynth 오류:")
            print(result.stderr)
            sys.exit(1)
            
    else:
        print(f"[2/2] MIDI → OGG      : {mid} → {out_file}")
        cmd = [
            "fluidsynth",
            "-n",               # MIDI 입력 드라이버 생성 안 함
            "-i",               # 셸 인터랙티브 모드 비활성화
            "-q",               # 시작 메시지 억제
            "-F", str(out_file),     # 출력 파일
            "-T", "oga",        # 파일 타입: OGG
            "-r", str(sample_rate),
            "-g", str(gain),
            str(sf2),           # SoundFont
            str(mid),           # 입력 MIDI
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("fluidsynth 오류:")
            print(result.stderr)
            sys.exit(1)

    if not keep_mid:
        mid.unlink(missing_ok=True)

    print(f"      완료: {out_file}")
    return out_file


def main():
    parser = argparse.ArgumentParser(
        description="MusicXML → OGG/MP3/WAV 변환 (music21 + fluidsynth CLI + pydub)"
    )
    parser.add_argument("input", help="입력 MusicXML 파일 (.xml / .mxl)")
    parser.add_argument("output", nargs="?", default=None, help="출력 파일 경로 (기본: 입력과 같은 이름으로 포맷에 따라 생성)")
    parser.add_argument("--sf2", default=DEFAULT_SF2, help=f"SoundFont 파일 경로 (기본: {DEFAULT_SF2})")
    parser.add_argument("--gain", type=float, default=DEFAULT_GAIN, help=f"볼륨 게인 0.0~10.0 (기본: {DEFAULT_GAIN})")
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE, help=f"샘플레이트 Hz (기본: {DEFAULT_SAMPLE_RATE})")
    parser.add_argument("--keep-mid", action="store_true", help="임시 MIDI 파일을 삭제하지 않고 보존")
    parser.add_argument("--format", choices=["ogg", "mp3", "wav"], default=None, help="출력 오디오 포맷 (기본: ogg, 출력 파일 확장자에 따라 자동 결정)")

    args = parser.parse_args()

    musicxml_to_ogg(
        xml_path=args.input,
        output=args.output,
        sf2_path=args.sf2,
        gain=args.gain,
        sample_rate=args.sample_rate,
        keep_mid=args.keep_mid,
        format=args.format,
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
midi_to_ogg.py
--------------
MIDI 파일을 OGG 오디오 파일로 변환합니다.

변환 파이프라인:
    MIDI ─[fluidsynth CLI]→ OGG

실행 위치: MusicXml/ 디렉터리 안에서 실행하세요.

사용법:
    python midi_to_ogg.py <input.mid> [output.ogg] [--sf2 <soundfont.sf2>] [--gain <0.0~10.0>]

예시:
    python midi_to_ogg.py Minuet_in_G.mid
    python midi_to_ogg.py Minuet_in_G.mid out.ogg --sf2 FluidR3_GM.sf2 --gain 1.0
"""

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_SF2 = "FluidR3_GM.sf2"
DEFAULT_GAIN = 0.8
DEFAULT_SAMPLE_RATE = 44100


def midi_to_ogg(
    midi_path: str,
    output: str = None,
    sf2_path: str = DEFAULT_SF2,
    gain: float = DEFAULT_GAIN,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> Path:
    """
    MIDI 파일을 OGG 오디오 파일로 변환합니다.

    Parameters
    ----------
    midi_path  : 입력 MIDI 파일 경로 (.mid / .midi)
    output     : 출력 OGG 파일 경로 (생략 시 입력과 같은 이름 .ogg)
    sf2_path   : SoundFont 파일 경로 (기본: FluidR3_GM.sf2)
    gain       : FluidSynth 마스터 볼륨 게인 0.0~10.0 (기본: 0.8)
    sample_rate: 샘플레이트 Hz (기본: 44100)

    Returns
    -------
    Path : 생성된 OGG 파일 경로
    """
    midi = Path(midi_path)
    if not midi.exists():
        print(f"오류: 파일을 찾을 수 없습니다 — {midi}")
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

    ogg = Path(output) if output else midi.with_suffix(".ogg")

    # ── MIDI → OGG (fluidsynth CLI) ──────────────────────────────────
    print(f"MIDI → OGG     : {midi} → {ogg}")
    cmd = [
        "fluidsynth",
        "-n",               # MIDI 입력 드라이버 생성 안 함
        "-i",               # 셸 인터랙티브 모드 비활성화
        "-q",               # 시작 메시지 억제
        "-F", str(ogg),     # 출력 파일
        "-T", "oga",        # 파일 타입: OGG
        "-r", str(sample_rate),
        "-g", str(gain),
        str(sf2),           # SoundFont
        str(midi),          # 입력 MIDI
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("fluidsynth 오류:")
        print(result.stderr)
        sys.exit(1)

    print(f"      완료: {ogg}")
    return ogg


def main():
    parser = argparse.ArgumentParser(
        description="MIDI → OGG 변환 (fluidsynth CLI)"
    )
    parser.add_argument("input", help="입력 MIDI 파일 (.mid / .midi)")
    parser.add_argument("output", nargs="?", default=None, help="출력 OGG 파일 경로 (기본: 입력과 같은 이름)")
    parser.add_argument("--sf2", default=DEFAULT_SF2, help=f"SoundFont 파일 경로 (기본: {DEFAULT_SF2})")
    parser.add_argument("--gain", type=float, default=DEFAULT_GAIN, help=f"볼륨 게인 0.0~10.0 (기본: {DEFAULT_GAIN})")
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE, help=f"샘플레이트 Hz (기본: {DEFAULT_SAMPLE_RATE})")

    args = parser.parse_args()

    midi_to_ogg(
        midi_path=args.input,
        output=args.output,
        sf2_path=args.sf2,
        gain=args.gain,
        sample_rate=args.sample_rate,
    )


if __name__ == "__main__":
    main()

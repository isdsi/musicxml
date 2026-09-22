#!/usr/bin/env python3
"""
mml_to_midi.py
==============
3MLE(마비노기 스타일) MML 텍스트 악보(.mml)를 파싱하여 MIDI(.mid) 파일로 변환합니다.

지원 포맷 개요:
    [Settings]                  : Title / Source / Memo / Encoding 메타데이터
    [ChannelN]                  : 채널별 MML 명령 스트림 (N = 1..9)
    [3MLE EXTENSION]            : 3MLE 전용 압축 확장 데이터 (본 변환기는 사용하지 않음)

지원 MML 명령:
    a-g(+/#/-)?N?.*  음표 (샵/플랫, 길이, 부점)
    r N? .*          쉼표
    < / >            옥타브 -1 / +1
    oN               옥타브 절대 지정
    lN               기본 음길이 지정
    vN               음량 지정 (0-15 스케일 또는 0-127 스케일 모두 허용)
    @N               악기(GM 프로그램 번호) 지정
    &                타이(다음 음표/쉼표까지 길이 연장)
    tN               템포 지정 (BPM)

의존성:
    pip install music21
"""

import argparse
import re
import sys
from pathlib import Path


def check_music21():
    """music21 설치 여부를 확인합니다."""
    try:
        import music21
        return music21
    except ImportError:
        print("[오류] music21 모듈이 설치되어 있지 않습니다.")
        print("  설치 방법: pip install music21")
        sys.exit(1)


# 채널 텍스트에서 명령 하나씩 순서대로 추출하는 정규식
_TOKEN_RE = re.compile(
    r"(?P<note>[a-gA-G][+#-]?\d*\.*)"
    r"|(?P<rest>[rR]\d*\.*)"
    r"|(?P<oct_down><)"
    r"|(?P<oct_up>>)"
    r"|(?P<set_oct>[oO]\d+)"
    r"|(?P<set_len>[lL]\d+\.*)"
    r"|(?P<volume>[vV]\d+)"
    r"|(?P<instrument>@\d+)"
    r"|(?P<tie>&)"
    r"|(?P<tempo>[tT]\d+)"
)

_STEP_TO_SEMITONE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def _strip_comments(text: str) -> str:
    """/* ... */ 블록 주석과 // 라인 주석을 제거합니다."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def _note_length_to_quarterlength(number: str, dots: str, default_length: int) -> float:
    """MML 길이 표기(분음표 분모 + 부점)를 music21 quarterLength(4분음표=1.0)로 변환합니다."""
    denom = int(number) if number else default_length
    if denom <= 0:
        denom = 4
    base = 4.0 / denom
    total = base
    add = base
    for _ in range(len(dots)):
        add /= 2.0
        total += add
    return total


def _velocity_from_volume(value: int) -> int:
    """v 명령 값(0-15 또는 0-127 스케일 모두 허용)을 MIDI 벨로시티(0-127)로 변환합니다."""
    if value <= 15:
        return max(1, min(127, round(value / 15 * 127)))
    return max(1, min(127, value))


def parse_mml_channel(text: str, m21):
    """
    채널 하나의 MML 명령 문자열을 파싱하여 music21 Part를 생성합니다.

    Returns:
        (part, tempo_bpm_or_None)
    """
    part = m21.stream.Part()

    octave = 4
    default_length = 4
    velocity = 100
    program = 0
    merge_next = False
    tempo_found = None

    inst = m21.instrument.Instrument()
    inst.midiProgram = program
    part.insert(0, inst)

    for match in _TOKEN_RE.finditer(text):
        kind = match.lastgroup
        value = match.group()

        if kind == "note":
            step = value[0].lower()
            rest = value[1:]
            accidental = ""
            if rest[:1] in ("+", "#", "-"):
                accidental = "#" if rest[0] in "+#" else "-"
                rest = rest[1:]
            digits = re.match(r"\d*", rest).group()
            dots = rest[len(digits):]
            qlen = _note_length_to_quarterlength(digits, dots, default_length)

            if merge_next and len(part.elements) > 0:
                part[-1].duration.quarterLength += qlen
                merge_next = False
            else:
                pitch_name = f"{step.upper()}{accidental}{octave}"
                n = m21.note.Note(pitch_name, quarterLength=qlen)
                n.volume.velocity = velocity
                part.append(n)

        elif kind == "rest":
            digits = re.match(r"\d*", value[1:]).group()
            dots = value[1 + len(digits):]
            qlen = _note_length_to_quarterlength(digits, dots, default_length)

            if merge_next and len(part.elements) > 0:
                part[-1].duration.quarterLength += qlen
                merge_next = False
            else:
                r = m21.note.Rest(quarterLength=qlen)
                part.append(r)

        elif kind == "oct_down":
            octave -= 1
        elif kind == "oct_up":
            octave += 1
        elif kind == "set_oct":
            octave = int(value[1:])
        elif kind == "set_len":
            digits = re.match(r"\d+", value[1:]).group()
            default_length = int(digits)
        elif kind == "volume":
            velocity = _velocity_from_volume(int(value[1:]))
        elif kind == "instrument":
            program = int(value[1:])
            new_inst = m21.instrument.Instrument()
            new_inst.midiProgram = program
            part.insert(part.highestTime, new_inst)
        elif kind == "tie":
            merge_next = True
        elif kind == "tempo":
            tempo_found = int(value[1:])

    return part, tempo_found


def mml_to_midi(input_path: str, output_path: str = None, bpm: int = 120) -> str:
    """
    MML(.mml) 파일을 MIDI(.mid) 파일로 변환합니다.

    Args:
        input_path: 입력 MML 파일 경로
        output_path: 출력 파일 경로 (기본값: 입력 파일과 같은 위치에 .mid 확장자)
        bpm: MML 안에 템포(t) 명령이 없을 때 사용할 기본 템포 (분당 4분음표 수)

    Returns:
        저장된 출력 파일의 절대 경로
    """
    m21 = check_music21()

    input_path = Path(input_path).resolve()
    if not input_path.exists():
        print(f"[오류] 파일을 찾을 수 없습니다: {input_path}")
        sys.exit(1)

    if output_path is None:
        output_path = input_path.with_suffix(".mid")
    else:
        output_path = Path(output_path).resolve()

    print(f"[정보] 입력 파일: {input_path}")
    print(f"[정보] 출력 파일: {output_path}")
    print("[정보] MML 파싱 중...")

    raw_bytes = input_path.read_bytes()
    try:
        raw_text = raw_bytes.decode("cp949")
    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("utf-8", errors="replace")

    section_re = re.compile(r"\[([^\]]+)\]([\s\S]*?)(?=\n\[[^\]]+\]|\Z)")
    channels = {}
    title = source = memo = ""

    for name, body in section_re.findall(raw_text):
        name = name.strip()
        m = re.match(r"^Channel(\d+)$", name)
        if m:
            channels[int(m.group(1))] = _strip_comments(body)
        elif name == "Settings":
            for line in body.splitlines():
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip().lower(), val.strip()
                if key == "title":
                    title = val
                elif key == "source":
                    source = val
                elif key == "memo":
                    memo = val

    if not channels:
        print("[오류] 파일에서 [ChannelN] 섹션을 찾지 못했습니다. 올바른 MML 파일인지 확인하세요.")
        sys.exit(1)

    if title:
        print(f"[정보] 제목: {title}")
    if source:
        print(f"[정보] 출처: {source}")
    if memo:
        print(f"[정보] 메모: {memo}")

    score = m21.stream.Score()
    found_tempo = None

    for ch_num in sorted(channels):
        part, tempo_found = parse_mml_channel(channels[ch_num], m21)
        if len(part.notesAndRests) == 0:
            continue
        if tempo_found and found_tempo is None:
            found_tempo = tempo_found
        part.partName = f"Channel{ch_num}"
        score.insert(0, part)

    if len(score.parts) == 0:
        print("[오류] 재생 가능한 음표를 찾지 못했습니다.")
        sys.exit(1)

    effective_bpm = found_tempo or bpm
    score.insert(0, m21.tempo.MetronomeMark(number=effective_bpm))
    print(f"[정보] 템포: {effective_bpm} BPM"
          + (" (MML 내 지정값)" if found_tempo else " (기본값)"))
    print(f"[정보] 채널 {len(score.parts)}개 변환됨")

    print("[정보] MIDI 변환 및 저장 중...")
    score.write("midi", fp=str(output_path))

    print(f"[완료] 저장됨: {output_path}")
    return str(output_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="mml_to_midi",
        description="3MLE 스타일 MML(.mml) → MIDI(.mid) 변환 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # MML → MIDI
  python mml_to_midi.py song.mml

  # 출력 경로 지정
  python mml_to_midi.py song.mml output/song.mid

  # 템포 지정 (MML 안에 t 명령이 없을 때 사용됨)
  python mml_to_midi.py song.mml --bpm 108
        """,
    )
    parser.add_argument("input", help="입력 MML 파일 경로 (.mml)")
    parser.add_argument("output", nargs="?", help="출력 파일 경로 (생략 시 입력 파일과 같은 위치에 .mid 저장)")
    parser.add_argument("--bpm", type=int, default=120, help="기본 템포 (BPM, 기본값: 120)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    mml_to_midi(args.input, args.output, bpm=args.bpm)


if __name__ == "__main__":
    main()

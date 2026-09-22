#!/usr/bin/env python3
"""
midi_to_mml.py
==============
music21을 이용하여 MIDI(.mid) 파일을 3MLE 스타일 MML 텍스트(.mml) 파일로 변환합니다.
[mml_to_midi.py](./mml_to_midi.py)의 역방향 변환 스크립트이며, 두 스크립트는 서로 왕복(round-trip)
호환되도록 같은 문법 규칙(길이/부점/옥타브/음량/악기/타이)을 사용합니다.

주의:
    - 3MLE 채널 하나는 원래 단선율 트래커 채널이므로, 한 트랙 안에 동시에 여러 음이 있으면 단선율로
      단순화합니다. 화음(Chord)은 가장 높은 음만 남기고, 서로 다른 성부가 겹쳐서 생긴 겹침은 더 길게
      지속되는 음을 우선 살리고 짧게 겹치는 쪽을 잘라냅니다.
    - [3MLE EXTENSION] 압축 메타데이터 블록은 생성하지 않습니다. 이 블록은 3MLE 자체 기능(체크섬 등)을
      위한 것으로, 본 프로젝트의 mml_to_midi.py를 포함한 일반적인 MML 재생에는 필요하지 않습니다.
      단, 실제 3MLE 에디터로 다시 불러올 때 일부 확장 기능은 인식되지 않을 수 있습니다.

사용법:
    python midi_to_mml.py <입력.mid> [출력.mml]

의존성:
    pip install music21
"""

import argparse
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


UNITS_PER_QUARTER = 16  # 64분음표 1개 = 1 unit


def _build_length_table():
    """(denom, dot여부) 조합으로 만들 수 있는 (unit길이, mml표기) 표를 길이 내림차순으로 생성합니다."""
    table = []
    for denom in (1, 2, 4, 8, 16, 32, 64):
        base_units = 64 // denom  # 온음표(whole note) = 64 units
        table.append((base_units, str(denom)))
        dotted_units = base_units * 3 // 2
        if base_units % 2 == 0:  # 홀수 unit(64분음표의 부점 등)은 표현 불가하므로 제외
            table.append((dotted_units, f"{denom}."))
    table.sort(key=lambda t: -t[0])
    return table


_LENGTH_TABLE = _build_length_table()


def _decompose_units(units: int):
    """정수 unit 길이를 표준 음표 길이 토큰들의 합으로 그리디 분해합니다."""
    tokens = []
    remaining = units
    for u, s in _LENGTH_TABLE:
        while remaining >= u:
            tokens.append(s)
            remaining -= u
    return tokens


def _pitch_to_mml(p) -> str:
    """music21 Pitch 객체를 'c', 'c+', 'c-' 형태의 MML 음이름(옥타브 제외)으로 변환합니다."""
    step = p.step.lower()
    alter = p.accidental.alter if p.accidental else 0
    if alter > 0:
        return step + "+" * int(round(alter))
    if alter < 0:
        return step + "-" * int(round(-alter))
    return step


def _velocity_to_v(velocity: int) -> int:
    """MIDI 벨로시티(0-127)를 3MLE 스타일 음량 스케일(0-15)로 변환합니다."""
    return max(0, min(15, round((velocity or 100) / 127 * 15)))


def _collect_events(part, m21):
    """
    Part를 순회하여 (offset_units, duration_units, pitch_or_None, velocity) 리스트를 생성합니다.
    화음은 최고음만 남기고, 빈 구간은 쉼표로 채워 연속(gap 없는) 이벤트 스트림으로 만듭니다.
    """
    flat = part.flatten().notesAndRests.stream()
    raw = []
    for el in flat:
        offset_units = round(el.offset * UNITS_PER_QUARTER)
        dur_units = round(el.duration.quarterLength * UNITS_PER_QUARTER)
        if dur_units <= 0:
            continue
        if isinstance(el, m21.chord.Chord):
            pitch = max(el.pitches, key=lambda p: p.midi)
            velocity = el.volume.velocity
        elif isinstance(el, m21.note.Note):
            pitch = el.pitch
            velocity = el.volume.velocity
        else:  # Rest
            pitch = None
            velocity = None
        raw.append((offset_units, dur_units, pitch, velocity))

    # 같은 시작 시각에 여러 음이 겹치면(화음이 아닌 서로 다른 성부의 겹침 등) 더 오래
    # 지속되는(=주선율일 가능성이 높은) 음을 우선 살리고, 짧게 겹치는 음은 잘라내
    # 단선율로 만듭니다.
    raw.sort(key=lambda t: (t[0], -t[1]))

    events = []
    cursor = 0
    for offset_units, dur_units, pitch, velocity in raw:
        if offset_units > cursor:
            events.append((cursor, offset_units - cursor, None, None))
        elif offset_units < cursor:
            # 겹치는 구간은 잘라내어 단선율로 만듦
            overlap = cursor - offset_units
            dur_units -= overlap
            offset_units = cursor
            if dur_units <= 0:
                continue
        events.append((offset_units, dur_units, pitch, velocity))
        cursor = offset_units + dur_units

    return events, cursor


def _part_to_channel_lines(part, m21, measure_units: int, extra_prefix: str = ""):
    """Part 하나를 [ChannelN] 본문 텍스트(측정마디 주석 포함)로 변환합니다."""
    events, total_units = _collect_events(part, m21)
    if total_units <= 0:
        return None

    n_measures = (total_units + measure_units - 1) // measure_units
    measure_lines = [""] * max(n_measures, 1)

    octave = 4
    velocity_bucket = -1

    try:
        program = part.getInstrument(returnDefault=True).midiProgram
    except Exception:
        program = None
    if program is None:
        program = 0

    def emit(measure_idx, text):
        measure_lines[measure_idx] += text

    # 악기 지정(및 필요 시 템포)은 채널 시작에 한 번만 기록
    measure_lines[0] += f"{extra_prefix}@{program}"

    for offset_units, dur_units, pitch, velocity in events:
        remaining = dur_units
        current = offset_units
        is_first_chunk = True

        if pitch is not None:
            target_octave = pitch.octave
            vbucket = _velocity_to_v(velocity)
        else:
            target_octave = None
            vbucket = None

        while remaining > 0:
            measure_idx = current // measure_units
            measure_end = (measure_idx + 1) * measure_units
            chunk = min(remaining, measure_end - current)
            tokens = _decompose_units(chunk)

            prefix = ""
            if is_first_chunk and pitch is not None:
                if target_octave > octave:
                    prefix += ">" * (target_octave - octave)
                elif target_octave < octave:
                    prefix += "<" * (octave - target_octave)
                octave = target_octave
                if vbucket != velocity_bucket:
                    prefix += f"v{vbucket}"
                    velocity_bucket = vbucket

            body = ""
            letter = _pitch_to_mml(pitch) if pitch is not None else "r"
            for i, tok in enumerate(tokens):
                body += f"{letter}{tok}"
                is_last_overall = (remaining - chunk <= 0) and (i == len(tokens) - 1)
                if not is_last_overall:
                    body += "&"

            emit(measure_idx, prefix + body)

            current += chunk
            remaining -= chunk
            is_first_chunk = False

    empty_measure = "&".join(f"r{tok}" for tok in _decompose_units(measure_units))

    lines = []
    for i, content in enumerate(measure_lines):
        lines.append(f"/*M {i:<3}*/  {content if content else empty_measure}")
    return "\n".join(lines)


def midi_to_mml(input_path: str, output_path: str = None) -> str:
    """
    MIDI(.mid) 파일을 3MLE 스타일 MML(.mml) 파일로 변환합니다.

    Args:
        input_path: 입력 MIDI 파일 경로
        output_path: 출력 파일 경로 (기본값: 입력 파일과 같은 위치에 .mml 확장자)

    Returns:
        저장된 출력 파일의 절대 경로
    """
    m21 = check_music21()

    input_path = Path(input_path).resolve()
    if not input_path.exists():
        print(f"[오류] 파일을 찾을 수 없습니다: {input_path}")
        sys.exit(1)

    if output_path is None:
        output_path = input_path.with_suffix(".mml")
    else:
        output_path = Path(output_path).resolve()

    print(f"[정보] 입력 파일: {input_path}")
    print(f"[정보] 출력 파일: {output_path}")
    print("[정보] MIDI 파싱 중...")

    score = m21.converter.parse(str(input_path))

    ts_list = score.flatten().getElementsByClass(m21.meter.TimeSignature)
    ts = ts_list[0] if len(ts_list) else None
    measure_ql = ts.barDuration.quarterLength if ts else 4.0
    measure_units = round(measure_ql * UNITS_PER_QUARTER)

    mm_list = score.flatten().getElementsByClass(m21.tempo.MetronomeMark)
    bpm = round(mm_list[0].number) if len(mm_list) and mm_list[0].number else 120

    title = ""
    try:
        if score.metadata and score.metadata.title:
            title = score.metadata.title
    except Exception:
        pass

    print(f"[정보] 마디 길이: {measure_ql} quarterLength, 템포: {bpm} BPM")

    parts = score.parts if len(score.parts) else [score]

    lines = []
    lines.append("[Settings]")
    lines.append("Encoding=UTF-8")
    lines.append(f"Title={title}")
    lines.append("Source=")
    lines.append("Memo=Generated by midi_to_mml.py")

    ch_index = 0
    for part in parts:
        extra_prefix = f"t{bpm}" if ch_index == 0 else ""
        body = _part_to_channel_lines(part, m21, measure_units, extra_prefix=extra_prefix)
        if body is None:
            continue
        ch_index += 1
        lines.append(f"[Channel{ch_index}]")
        lines.append("//#using_extension")
        lines.append(f"//#using_channel = {ch_index}")
        lines.append("")
        lines.append("")
        lines.append(body)

    if ch_index == 0:
        print("[오류] 변환할 음표가 있는 트랙(파트)을 찾지 못했습니다.")
        sys.exit(1)

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[정보] 채널 {ch_index}개 생성됨")
    print(f"[완료] 저장됨: {output_path}")
    return str(output_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="midi_to_mml",
        description="music21을 이용한 MIDI(.mid) → MML(.mml, 3MLE 스타일) 변환 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # MIDI → MML
  python midi_to_mml.py song.mid

  # 출력 경로 지정
  python midi_to_mml.py song.mid output/song.mml

  # 왕복 검증 (round-trip)
  python midi_to_mml.py song.mid song.mml
  python mml_to_midi.py song.mml song_roundtrip.mid
        """,
    )
    parser.add_argument("input", help="입력 MIDI 파일 경로 (.mid, .midi)")
    parser.add_argument("output", nargs="?", help="출력 파일 경로 (생략 시 입력 파일과 같은 위치에 .mml 저장)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    midi_to_mml(args.input, args.output)


if __name__ == "__main__":
    main()

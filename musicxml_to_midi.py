#!/usr/bin/env python3
"""
musicxml_to_midi.py
===================
music21을 이용하여 MusicXML(.xml / .mxl) 파일을 MIDI(.mid) 파일로 변환하는 스크립트입니다.

사용법:
    python musicxml_to_midi.py <입력파일> [출력파일] [옵션]

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


def musicxml_to_midi(input_path: str, output_path: str = None) -> str:
    """
    MusicXML 파일을 MIDI로 변환합니다.

    Args:
        input_path: 입력 MusicXML 파일 경로 (.xml / .mxl / .musicxml)
        output_path: 출력 파일 경로 (기본값: 입력 파일과 같은 위치에 .mid 확장자)

    Returns:
        저장된 출력 파일의 절대 경로
    """
    m21 = check_music21()

    input_path = Path(input_path).resolve()
    if not input_path.exists():
        print(f"[오류] 파일을 찾을 수 없습니다: {input_path}")
        sys.exit(1)

    suffix = input_path.suffix.lower()
    if suffix not in (".xml", ".mxl", ".musicxml"):
        print(f"[경고] 입력 파일 확장자가 MusicXML 형식이 아닙니다: {suffix}")

    # 출력 경로 결정
    if output_path is None:
        output_path = input_path.with_suffix(".mid")
    else:
        output_path = Path(output_path).resolve()

    print(f"[정보] 입력 파일: {input_path}")
    print(f"[정보] 출력 파일: {output_path}")
    print("[정보] MusicXML 파싱 중...")

    score = m21.converter.parse(str(input_path))

    print("[정보] MIDI 변환 및 저장 중...")
    score.write("midi", fp=str(output_path))

    print(f"[완료] 저장됨: {output_path}")
    return str(output_path)


def convert_music(input_path: str, output_path: str = None) -> str:
    """
    music21이 지원하는 모든 악보 형식을 MIDI로 변환합니다.

    지원 입력 형식: .xml, .mxl, .musicxml, .krn (Kern), .abc, .mei 등

    Args:
        input_path: 입력 악보 파일 경로
        output_path: 출력 파일 경로

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
        # 입출력 경로가 동일하면 _converted 접미사 추가
        if output_path == input_path:
            output_path = input_path.with_stem(input_path.stem + "_converted").with_suffix(".mid")
    else:
        output_path = Path(output_path).resolve()

    print(f"[정보] 입력 파일: {input_path}")
    print(f"[정보] 출력 파일: {output_path}")
    print("[정보] 악보 파싱 중...")

    score = m21.converter.parse(str(input_path))

    print("[정보] MIDI 변환 및 저장 중...")
    score.write("midi", fp=str(output_path))

    print(f"[완료] 저장됨: {output_path}")
    return str(output_path)


def batch_convert(
    input_dir: str,
    output_dir: str = None,
    extensions: list = None,
):
    """
    디렉터리 내 모든 악보 파일을 MIDI로 일괄 변환합니다.

    Args:
        input_dir:  입력 디렉터리 경로
        output_dir: 출력 디렉터리 경로 (기본값: 입력 디렉터리)
        extensions: 처리할 확장자 목록 (기본값: ['.xml', '.mxl', '.musicxml'])
    """
    if extensions is None:
        extensions = [".xml", ".mxl", ".musicxml"]

    input_dir = Path(input_dir).resolve()
    output_dir = Path(output_dir).resolve() if output_dir else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    files = [f for f in input_dir.iterdir()
             if f.is_file() and f.suffix.lower() in extensions]

    if not files:
        print(f"[경고] 변환할 파일이 없습니다: {input_dir} (확장자: {extensions})")
        return

    print(f"[정보] {len(files)}개 파일 변환 시작...")
    success, failed = 0, 0

    for f in files:
        out = output_dir / f.with_suffix(".mid").name
        try:
            convert_music(str(f), str(out))
            success += 1
        except Exception as e:
            print(f"[오류] {f.name}: {e}")
            failed += 1

    print(f"\n[결과] 성공: {success}, 실패: {failed} / 전체: {len(files)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="musicxml_to_midi",
        description="music21을 이용한 MusicXML / 악보 → MIDI 변환 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # MusicXML → MIDI
  python musicxml_to_midi.py song.xml

  # 출력 경로 지정
  python musicxml_to_midi.py song.xml output/song.mid

  # ABC 악보 → MIDI
  python musicxml_to_midi.py score.abc converted.mid

  # 디렉터리 일괄 변환
  python musicxml_to_midi.py --batch xml_files/ --output-dir midi_files/

  # ABC/Kern 포함 일괄 변환
  python musicxml_to_midi.py --batch scores/ --ext .abc .krn --output-dir out/
        """,
    )

    parser.add_argument(
        "input", nargs="?",
        help="입력 파일 경로 (.xml, .mxl, .musicxml, .abc, .krn 등)",
    )
    parser.add_argument(
        "output", nargs="?",
        help="출력 파일 경로 (생략 시 입력 파일과 같은 위치에 .mid 저장)",
    )
    parser.add_argument(
        "--batch", metavar="DIR",
        help="디렉터리 내 모든 파일을 일괄 변환",
    )
    parser.add_argument(
        "--output-dir", metavar="DIR",
        help="일괄 변환 시 출력 디렉터리 (기본값: 입력 디렉터리)",
    )
    parser.add_argument(
        "--ext", nargs="+", default=[".xml", ".mxl", ".musicxml"], metavar="EXT",
        help="일괄 변환 시 처리할 확장자 (기본값: .xml .mxl .musicxml)",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.batch:
        batch_convert(
            input_dir=args.batch,
            output_dir=args.output_dir,
            extensions=args.ext,
        )
    elif args.input:
        convert_music(
            input_path=args.input,
            output_path=args.output,
        )
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()

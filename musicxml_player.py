# -*- coding: utf-8 -*-
"""
musicxml_player.py
------------------
PySide6와 FluidSynth를 이용한 MusicXML & MIDI 신디사이저 플레이어입니다.

기능:
- MusicXML (.xml, .mxl), MIDI (.mid, .midi), MML (.mml, 3MLE 형식) 파일 불러오기 및 재생
- FluidR3_GM.sf2 및 사용자 커스텀 사운드폰트(.sf2) 연동
- 재생, 일시정지, 중단, 실시간 볼륨(마스터 게인) 조절
- 로드된 파일을 MIDI, MusicXML, MML, OGG, MP3, WAV로 저장(Export) 지원
- 채널(트랙)별 색상 구분 피아노롤 시각화 및 채널별 악기(GM 프로그램) 변경
"""

import sys
import os
import tempfile
from pathlib import Path

# PySide6 GUI 임포트
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QFileDialog, QMessageBox, QFrame,
    QComboBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont, QAction, QPainter, QColor, QPen

# 악보 분석(채널/음표) 임포트
import music21 as m21

# 무설치 포터블 패키징을 위한 내부 bin/ 바이너리 폴더 PATH 최우선적 연동
base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
bin_path = os.path.join(base_dir, "bin")
if os.path.exists(bin_path):
    os.environ["PATH"] = bin_path + os.path.pathsep + os.environ["PATH"]
    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(bin_path)
        except Exception:
            pass

# Fluidsynth 바인딩 임포트
try:
    import fluidsynth
except ImportError:
    print("[오류] fluidsynth 패키지가 가상환경에 설치되어 있지 않습니다.")
    print("  설치 방법: pip install pyfluidsynth")
    sys.exit(1)

# 코어 변환 모듈 임포트
try:
    from midi_to_musicxml import convert_music as midi_to_mxml_convert
    from musicxml_to_midi import convert_music as mxml_to_midi_convert
    from musicxml_to_ogg import musicxml_to_ogg
    from midi_to_ogg import midi_to_ogg
    from mml_to_midi import mml_to_midi as mml_to_midi_convert
    from midi_to_mml import midi_to_mml as midi_to_mml_convert, get_part_program
except ImportError as e:
    print(f"[경고] 일부 변환 모듈을 로드하지 못했습니다: {e}")
    print("  변환 내보내기 기능이 제한될 수 있습니다.")


# General MIDI Level 1 표준 악기명 (프로그램 번호 0-127)
GM_INSTRUMENT_NAMES = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
    "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavinet",
    "Celesta", "Glockenspiel", "Music Box", "Vibraphone",
    "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
    "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ",
    "Reed Organ", "Accordion", "Harmonica", "Tango Accordion",
    "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)", "Electric Guitar (clean)",
    "Electric Guitar (muted)", "Overdriven Guitar", "Distortion Guitar", "Guitar Harmonics",
    "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass",
    "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2",
    "Violin", "Viola", "Cello", "Contrabass",
    "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp", "Timpani",
    "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2",
    "Choir Aahs", "Voice Oohs", "Synth Voice", "Orchestra Hit",
    "Trumpet", "Trombone", "Tuba", "Muted Trumpet",
    "French Horn", "Brass Section", "Synth Brass 1", "Synth Brass 2",
    "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax",
    "Oboe", "English Horn", "Bassoon", "Clarinet",
    "Piccolo", "Flute", "Recorder", "Pan Flute",
    "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina",
    "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)",
    "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass+lead)",
    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)",
    "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",
    "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)",
    "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)",
    "Sitar", "Banjo", "Shamisen", "Koto",
    "Kalimba", "Bag Pipe", "Fiddle", "Shanai",
    "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock",
    "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal",
    "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet",
    "Telephone Ring", "Helicopter", "Applause", "Gunshot",
]

# 채널별 피아노롤 색상 팔레트 (순환 사용)
CHANNEL_COLORS = [
    QColor("#f472b6"), QColor("#4ade80"), QColor("#60a5fa"), QColor("#22d3ee"),
    QColor("#fbbf24"), QColor("#a78bfa"), QColor("#fb923c"), QColor("#facc15"),
    QColor("#34d399"),
]


class PianoRollWidget(QWidget):
    """채널별로 색상을 구분해 음표를 그려주는 읽기전용 피아노롤 위젯."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.channels = []      # [{"notes": [(offset_ql, dur_ql, pitch_midi), ...], "color": QColor}, ...]
        self.total_ql = 4.0
        self.playhead_ql = 0.0
        self.min_pitch = 48
        self.max_pitch = 84
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, channels, total_ql):
        """채널별 음표 목록과 전체 길이(quarterLength)를 갱신하고 다시 그립니다."""
        self.channels = channels
        self.total_ql = max(total_ql, 0.001)

        all_pitches = [p for ch in self.channels for (_, _, p) in ch["notes"]]
        if all_pitches:
            self.min_pitch = min(all_pitches) - 2
            self.max_pitch = max(all_pitches) + 2
        else:
            self.min_pitch, self.max_pitch = 48, 84

        self.playhead_ql = 0.0
        self.update()

    def set_playhead(self, ql):
        self.playhead_ql = max(0.0, min(ql, self.total_ql))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#0f0f11"))

        w = max(self.width(), 1)
        h = max(self.height(), 1)
        pitch_range = max(self.max_pitch - self.min_pitch, 1)
        row_h = h / pitch_range

        def x_for(ql):
            return (ql / self.total_ql) * w

        def y_for(pitch):
            return h - (pitch - self.min_pitch) / pitch_range * h

        # 옥타브(C음) 기준 가로 안내선
        painter.setPen(QPen(QColor("#27272a"), 1))
        for pitch in range(self.min_pitch, self.max_pitch + 1):
            if pitch % 12 == 0:  # C 음
                y = int(y_for(pitch))
                painter.drawLine(0, y, w, y)

        # 채널별 음표 사각형
        for ch in self.channels:
            painter.setBrush(ch["color"])
            painter.setPen(Qt.NoPen)
            for offset_ql, dur_ql, pitch in ch["notes"]:
                x = x_for(offset_ql)
                bar_w = max(x_for(offset_ql + dur_ql) - x, 2)
                y = y_for(pitch)
                painter.drawRect(int(x), int(y - row_h * 0.4), int(bar_w) - 1, max(int(row_h * 0.8), 2))

        # 재생 위치(플레이헤드)
        if self.total_ql > 0:
            painter.setPen(QPen(QColor("#ef4444"), 2))
            px = int(x_for(self.playhead_ql))
            painter.drawLine(px, 0, px, h)


class MusicXMLPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("MusicXML & MIDI Synthesizer Player")
        self.resize(900, 700)

        # 상태 변수 초기화
        self.current_file = None      # 사용자 로드 파일 경로 (xml/mxl/mid/midi/mml)
        self.current_midi_file = None # 실제 재생용 MIDI 파일 경로 (MusicXML/MML인 경우 임시 변환 파일)
        self.temp_midi_obj = None     # 임시 MIDI 파일 리소스 관리를 위한 객체
        self.current_sf2 = "FluidR3_GM.sf2"
        self.is_playing = False
        self.is_paused = False
        self.play_time_seconds = 0

        # 채널/피아노롤 분석 상태
        self.loaded_score = None      # 현재 재생용 MIDI를 music21로 분석한 Score (악기 변경용)
        self.tempo_bpm = 120
        self.total_ql = 4.0
        self.channel_rows = []        # [(QLabel, QComboBox), ...] 채널 패널 위젯 목록
        self.instrument_modified = False  # 채널 패널에서 악기를 바꿔 원본과 달라졌는지 여부 (Export 시 반영용)
        
        # Fluidsynth 엔진 인스턴스 변수
        self.fs_synth = None
        self.fs_player = None
        self.fs_adriver = None
        self.sf_id = None
        
        # 신디사이저 엔진 초기화
        self.init_synth()
        
        # UI 레이아웃 빌드
        self.init_ui()
        
        # 1초 타이머 설정 (재생 시간 표시용)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_playback_time)
        
        # 앱 종료 이벤트 감지하여 리소스 해제
        QApplication.instance().aboutToQuit.connect(self.cleanup_resources)

        # 윈도우 연결 프로그램 및 명령행 인자 기동 처리 (자동 연주)
        if len(sys.argv) > 1:
            startup_file = sys.argv[1]
            if os.path.exists(startup_file) and Path(startup_file).suffix.lower() in (".xml", ".mxl", ".mid", ".midi", ".mml"):
                # GUI 창이 완전히 뜬 후 안정적으로 파일을 로드하고 연주를 기동
                QTimer.singleShot(100, lambda: self.load_file(startup_file))
                QTimer.singleShot(600, self.on_play_clicked)

    def init_synth(self):
        """Fluidsynth 신디사이저 오디오 드라이버와 객체를 기동합니다."""
        try:
            # 기본 게인 0.8 지정하여 Synth 생성
            self.fs_synth = fluidsynth.Synth(gain=0.8)
            
            # [핵심 우회] winmidi 입력 장치 에러를 방지하기 위해 오직 오디오 출력 드라이버만 직접 생성하여 연동
            self.fs_adriver = fluidsynth.new_fluid_audio_driver(self.fs_synth.settings, self.fs_synth.synth)
            
            # 기본 사운드폰트 로드 시도
            if not self.load_soundfont(self.current_sf2):
                QMessageBox.warning(
                    self, "SoundFont Missing",
                    "Default SoundFont (FluidR3_GM.sf2) could not be found.\n"
                    "Please click the 'Change SoundFont...' button on the right to specify a valid .sf2 SoundFont file."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Synthesizer Startup Failed",
                f"Cannot initialize FluidSynth audio output.\nPlease make sure FluidSynth binary/library is correctly installed on your system.\nError: {e}"
            )

    def load_soundfont(self, sf2_path):
        """Loads the specified SoundFont (.sf2) file into the synthesizer."""
        if not self.fs_synth:
            return False
            
        path = Path(sf2_path)
        # 로드 성공 여부 탐색
        if not path.exists():
            # 프로젝트 루트 경로 재탐색
            cand = Path(__file__).parent / path.name
            if cand.exists():
                path = cand
                
        if path.exists():
            try:
                # 기존 사운드폰트 언로드
                if self.sf_id is not None:
                    # pyfluidsynth 버전에 따라 sfunload가 지원되지 않을 수 있으므로 예외 처리
                    try:
                        self.fs_synth.sfunload(self.sf_id)
                    except:
                        pass
                
                self.sf_id = self.fs_synth.sfload(str(path))
                self.fs_synth.program_select(0, self.sf_id, 0, 0)
                self.current_sf2 = str(path)
                return True
            except Exception as e:
                QMessageBox.warning(self, "SoundFont Load Failed", f"An error occurred while loading the SoundFont:\n{e}")
        else:
            # 최초 실행 시 경고창 억제 (사용자가 변경하도록 유도)
            print(f"[Warning] SoundFont file not found: {sf2_path}")
        return False

    def init_ui(self):
        """Defines the PySide6 Rich Aesthetics dark view layout."""
        # 메인 윈도우 스타일시트 적용
        self.setStyleSheet("""
            QMainWindow {
                background-color: #18181b;
            }
            QLabel {
                color: #e4e4e7;
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
            }
            QFrame#card {
                background-color: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 12px;
            }
            QPushButton {
                background-color: #3f3f46;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #52525b;
            }
            QPushButton:pressed {
                background-color: #0284c7;
            }
            QPushButton#playBtn {
                background-color: #0284c7;
            }
            QPushButton#playBtn:hover {
                background-color: #0369a1;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #52525b;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #38bdf8;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #38bdf8;
                border: 1px solid #0284c7;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            
            /* QMessageBox 다크 테마 일관화 및 메시지 텍스트 가독성 확보 */
            QMessageBox {
                background-color: #27272a;
            }
            QMessageBox QLabel {
                color: #f4f4f5;
                font-size: 13px;
            }
            QMessageBox QPushButton {
                background-color: #3f3f46;
                color: #ffffff;
                border: 1px solid #52525b;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                min-width: 70px;
            }
            QMessageBox QPushButton:hover {
                background-color: #52525b;
            }
        """)

        # 메뉴 바 빌드
        self.build_menu()

        # 메인 센트럴 위젯 구성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 1. 미디어 카드 위젯 (파일명 및 상태 정보)
        media_card = QFrame()
        media_card.setObjectName("card")
        card_layout = QVBoxLayout(media_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_title = QLabel("Please select a file to play.")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f4f4f5;")
        self.lbl_meta = QLabel("Supported Formats: MusicXML (.xml, .mxl), MIDI (.mid, .midi), MML (.mml)")
        self.lbl_meta.setStyleSheet("font-size: 13px; color: #a1a1aa;")
        
        card_layout.addWidget(self.lbl_title)
        card_layout.addWidget(self.lbl_meta)
        main_layout.addWidget(media_card)

        # 2. 사운드폰트 로드 설정 제어 영역
        sf2_layout = QHBoxLayout()
        self.lbl_sf2_name = QLabel(f"SoundFont: {Path(self.current_sf2).name}")
        self.lbl_sf2_name.setStyleSheet("font-size: 13px; font-weight: bold; color: #38bdf8;")
        btn_change_sf2 = QPushButton("Change SoundFont...")
        btn_change_sf2.setStyleSheet("padding: 6px 12px; font-size: 11px;")
        btn_change_sf2.clicked.connect(self.on_change_soundfont)
        
        sf2_layout.addWidget(self.lbl_sf2_name)
        sf2_layout.addStretch()
        sf2_layout.addWidget(btn_change_sf2)
        main_layout.addLayout(sf2_layout)

        # 3. 채널별 악기 패널 (채널마다 이름 + 악기 선택 콤보박스)
        channels_card = QFrame()
        channels_card.setObjectName("card")
        channels_card_layout = QVBoxLayout(channels_card)
        channels_card_layout.setContentsMargins(15, 12, 15, 12)

        lbl_channels_title = QLabel("Channels & Instruments")
        lbl_channels_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #a1a1aa;")
        channels_card_layout.addWidget(lbl_channels_title)

        self.channels_scroll = QScrollArea()
        self.channels_scroll.setWidgetResizable(True)
        self.channels_scroll.setFixedHeight(120)
        self.channels_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.channels_container = QWidget()
        self.channels_layout = QVBoxLayout(self.channels_container)
        self.channels_layout.setContentsMargins(0, 4, 0, 0)
        self.channels_layout.setSpacing(4)
        self.channels_layout.addStretch()
        self.channels_scroll.setWidget(self.channels_container)

        channels_card_layout.addWidget(self.channels_scroll)
        main_layout.addWidget(channels_card)

        # 4. 피아노롤 (채널별 색상 구분 음표 시각화)
        pianoroll_card = QFrame()
        pianoroll_card.setObjectName("card")
        pianoroll_card_layout = QVBoxLayout(pianoroll_card)
        pianoroll_card_layout.setContentsMargins(15, 12, 15, 12)

        lbl_pianoroll_title = QLabel("Piano Roll")
        lbl_pianoroll_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #a1a1aa;")
        pianoroll_card_layout.addWidget(lbl_pianoroll_title)

        self.piano_roll = PianoRollWidget()
        pianoroll_card_layout.addWidget(self.piano_roll)

        main_layout.addWidget(pianoroll_card, stretch=1)

        # 5. 진행 상황 타임라인 표시 및 진행 슬라이더
        progress_layout = QHBoxLayout()
        self.lbl_current_time = QLabel("00:00")
        self.lbl_current_time.setStyleSheet("font-size: 12px; color: #a1a1aa;")
        
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setRange(0, 100)
        self.timeline_slider.setValue(0)
        # 틱 시퀀싱 연동에 따른 세그멘테이션 폴트를 막기 위해 읽기 전용(비활성) 처리
        self.timeline_slider.setEnabled(False) 
        
        self.lbl_total_time = QLabel("--:--")
        self.lbl_total_time.setStyleSheet("font-size: 12px; color: #a1a1aa;")
        
        progress_layout.addWidget(self.lbl_current_time)
        progress_layout.addWidget(self.timeline_slider)
        progress_layout.addWidget(self.lbl_total_time)
        main_layout.addLayout(progress_layout)

        # 6. 플레이어 메인 컨트롤러 버튼 영역
        control_layout = QHBoxLayout()
        
        self.btn_play = QPushButton("Play")
        self.btn_play.setObjectName("playBtn")
        self.btn_play.clicked.connect(self.on_play_clicked)
        
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.clicked.connect(self.on_pause_clicked)
        self.btn_pause.setEnabled(False)
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.on_stop_clicked)
        self.btn_stop.setEnabled(False)
        
        # 볼륨 조절 슬라이더
        lbl_volume = QLabel("Volume ")
        lbl_volume.setStyleSheet("font-size: 13px; margin-left: 15px;")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80) # 기본 80% (Gain 0.8 배율)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)

        control_layout.addWidget(self.btn_play)
        control_layout.addWidget(self.btn_pause)
        control_layout.addWidget(self.btn_stop)
        control_layout.addWidget(lbl_volume)
        control_layout.addWidget(self.volume_slider)
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)

    def build_menu(self):
        """메인 파일/도움말 풀다운 메뉴바를 빌드합니다."""
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #27272a;
                color: #e4e4e7;
            }
            QMenuBar::item:selected {
                background-color: #3f3f46;
            }
            QMenu {
                background-color: #27272a;
                color: #e4e4e7;
                border: 1px solid #3f3f46;
            }
            QMenu::item:selected {
                background-color: #0284c7;
            }
        """)

        # 1. 파일 메뉴
        file_menu = menu_bar.addMenu("File(&F)")
        
        action_open = QAction("Open(&O)...", self)
        action_open.triggered.connect(self.on_open_file)
        file_menu.addAction(action_open)
        
        self.action_export = QAction("Export As(&E)...", self)
        self.action_export.setEnabled(False) # 파일 로드 전 비활성화
        self.action_export.triggered.connect(self.on_export_file)
        file_menu.addAction(self.action_export)
        
        file_menu.addSeparator()
        
        action_exit = QAction("Exit(&X)", self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        # 2. 도움말 메뉴
        help_menu = menu_bar.addMenu("Help(&H)")
        action_about = QAction("About(&A)", self)
        action_about.triggered.connect(self.show_about_dialog)
        help_menu.addAction(action_about)

    # -----------------------------------------------------------------------
    # 내부 이벤트 제어 핸들러
    # -----------------------------------------------------------------------

    def on_open_file(self):
        """다이얼로그를 통해 악보 및 MIDI 파일을 로드합니다."""
        file_filter = "Score, MIDI and MML Files (*.xml *.mxl *.mid *.midi *.mml)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Music File", "", file_filter
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        """지정된 파일 경로로부터 악보 및 MIDI 파일을 로드합니다."""
        # 리소스 정리 선행
        self.on_stop_clicked()
        self.cleanup_temp_midi()

        self.current_file = file_path
        self.instrument_modified = False
        path_obj = Path(file_path)
        suffix = path_obj.suffix.lower()

        # UI 라벨 갱신
        self.lbl_title.setText(path_obj.name)
        self.lbl_meta.setText(f"File Path: {file_path}")

        # MusicXML / MML 변환 우회
        if suffix in (".xml", ".mxl", ".mml"):
            self.lbl_title.setText(f"[Converting...] {path_obj.name}")
            QApplication.processEvents() # UI 반영 대기

            try:
                # 임시 midi 파일 작성 경로 획득
                self.temp_midi_obj = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
                self.temp_midi_obj.close() # 쓰기 잠금 해제
                temp_path = self.temp_midi_obj.name

                # 형식에 맞는 변환 모듈 호출하여 임시 변환
                if suffix == ".mml":
                    mml_to_midi_convert(file_path, temp_path)
                else:
                    mxml_to_midi_convert(file_path, temp_path)
                self.current_midi_file = temp_path
                self.lbl_title.setText(path_obj.name)
            except Exception as e:
                kind = "MML" if suffix == ".mml" else "MusicXML"
                QMessageBox.critical(self, "Conversion Failed", f"An error occurred while parsing {kind}:\n{e}")
                self.current_file = None
                self.current_midi_file = None
                self.lbl_title.setText("Please select a file to play.")
                return
        else:
            # MIDI 다이렉트 바인딩
            self.current_midi_file = file_path

        # 내보내기 및 제어 버튼 상태 복원
        self.action_export.setEnabled(True)
        self.btn_play.setEnabled(True)
        
        # 타임라인 라벨 리셋
        self.lbl_current_time.setText("00:00")
        self.lbl_total_time.setText("Ready")
        self.timeline_slider.setValue(0)

        # 채널/피아노롤 분석 갱신 (실패해도 재생 자체는 계속 가능해야 하므로 별도 예외 처리)
        self.refresh_channels_and_roll()

    def on_export_file(self):
        """로드된 악보 리소스를 사용자가 원하는 포맷으로 변환 저장합니다."""
        if not self.current_file:
            return

        file_filter = (
            "MIDI Files (*.mid);;"
            "MusicXML Scores (*.xml);;"
            "Compressed MusicXML (*.mxl);;"
            "MML Text (*.mml);;"
            "OGG Audio (*.ogg);;"
            "MP3 Audio (*.mp3);;"
            "WAV Audio (*.wav)"
        )
        
        save_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export File As", "", file_filter
        )
        
        if not save_path:
            return

        ext = Path(save_path).suffix.lower()
        src_path = self.current_file
        src_ext = Path(src_path).suffix.lower()

        # 채널 패널에서 악기를 바꿨다면, 원본이 아니라 그 변경이 반영된 현재 재생용 MIDI를
        # 모든 내보내기의 기준으로 사용합니다 (그래야 새 악기가 실제로 저장됨).
        effective_midi = self.current_midi_file if self.instrument_modified else None

        # 진행 표시 알림 대기
        self.lbl_total_time.setText("Exporting...")
        QApplication.processEvents()

        temp_bridge_midi = None  # xml/mml 상호 변환 시 거쳐가는 임시 MIDI 파일

        def bridge_to_midi():
            """src_path(xml/mxl/mml)를 임시 MIDI 파일로 변환하고 그 경로를 돌려줍니다."""
            nonlocal temp_bridge_midi
            tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
            tmp.close()
            temp_bridge_midi = tmp.name
            if src_ext == ".mml":
                mml_to_midi_convert(src_path, temp_bridge_midi)
            else:
                mxml_to_midi_convert(src_path, temp_bridge_midi)
            return temp_bridge_midi

        try:
            import shutil

            # 1. MIDI 내보내기
            if ext in (".mid", ".midi"):
                if effective_midi:
                    shutil.copy(effective_midi, save_path)
                elif src_ext in (".xml", ".mxl"):
                    mxml_to_midi_convert(src_path, save_path)
                elif src_ext == ".mml":
                    mml_to_midi_convert(src_path, save_path)
                else:
                    # MIDI -> MIDI 단순 복사
                    shutil.copy(src_path, save_path)

            # 2. MusicXML 내보내기
            elif ext in (".xml", ".mxl"):
                if effective_midi:
                    midi_to_mxml_convert(effective_midi, save_path)
                elif src_ext in (".mid", ".midi"):
                    midi_to_mxml_convert(src_path, save_path)
                elif src_ext == ".mml":
                    midi_to_mxml_convert(bridge_to_midi(), save_path)
                else:
                    # MusicXML 재포장 복사
                    shutil.copy(src_path, save_path)

            # 3. MML 내보내기
            elif ext == ".mml":
                if effective_midi:
                    midi_to_mml_convert(effective_midi, save_path)
                elif src_ext in (".mid", ".midi"):
                    midi_to_mml_convert(src_path, save_path)
                elif src_ext in (".xml", ".mxl"):
                    midi_to_mml_convert(bridge_to_midi(), save_path)
                else:
                    # MML -> MML 단순 복사
                    shutil.copy(src_path, save_path)

            # 4. OGG / MP3 / WAV 렌더링 내보내기
            elif ext in (".ogg", ".mp3", ".wav"):
                fmt_param = ext.replace(".", "")
                if effective_midi:
                    midi_to_ogg(
                        midi_path=effective_midi,
                        output=save_path,
                        sf2_path=self.current_sf2,
                        gain=self.volume_slider.value() / 100.0,
                        format=fmt_param
                    )
                elif src_ext in (".xml", ".mxl"):
                    musicxml_to_ogg(
                        xml_path=src_path,
                        output=save_path,
                        sf2_path=self.current_sf2,
                        gain=self.volume_slider.value() / 100.0,
                        format=fmt_param
                    )
                else:
                    # MIDI는 그대로, MML은 로드 시 이미 변환해 둔 재생용 임시 MIDI를 사용
                    midi_src = self.current_midi_file if src_ext == ".mml" else src_path
                    midi_to_ogg(
                        midi_path=midi_src,
                        output=save_path,
                        sf2_path=self.current_sf2,
                        gain=self.volume_slider.value() / 100.0,
                        format=fmt_param
                    )

            QMessageBox.information(self, "Success", f"Successfully saved to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred during export:\n{e}")
        finally:
            if temp_bridge_midi:
                try:
                    Path(temp_bridge_midi).unlink(missing_ok=True)
                except Exception:
                    pass
            self.lbl_total_time.setText("Ready")

    def on_change_soundfont(self):
        """사운드폰트(.sf2) 파일을 교체 로드합니다."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load SoundFont", "", "SoundFont Files (*.sf2)"
        )
        if file_path:
            # 신디사이저 재생 중인 경우 정지 후 변경
            is_playing_temp = self.is_playing
            self.on_stop_clicked()
            
            if self.load_soundfont(file_path):
                self.lbl_sf2_name.setText(f"SoundFont: {Path(file_path).name}")
                if is_playing_temp:
                    self.on_play_clicked()
            else:
                QMessageBox.warning(self, "Load Failed", "Not a valid SoundFont file.")

    # -----------------------------------------------------------------------
    # 채널별 악기 패널 & 피아노롤
    # -----------------------------------------------------------------------

    def refresh_channels_and_roll(self):
        """현재 재생용 MIDI(self.current_midi_file)를 분석해 채널 패널과 피아노롤을 다시 그립니다."""
        self._clear_channel_rows()

        if not self.current_midi_file:
            self.loaded_score = None
            self.piano_roll.set_data([], 4.0)
            return

        try:
            score = m21.converter.parse(str(self.current_midi_file))
        except Exception as e:
            print(f"[경고] 채널 분석을 위한 MIDI 파싱 실패: {e}")
            self.loaded_score = None
            self.piano_roll.set_data([], 4.0)
            return

        self.loaded_score = score

        mm_list = score.flatten().getElementsByClass(m21.tempo.MetronomeMark)
        self.tempo_bpm = round(mm_list[0].number) if len(mm_list) and mm_list[0].number else 120

        parts = score.parts if len(score.parts) else [score]
        roll_channels = []
        max_ql = 0.0

        for i, part in enumerate(parts):
            program = get_part_program(part, m21)

            notes = []
            for el in part.flatten().notesAndRests:
                if isinstance(el, m21.chord.Chord):
                    pitches = [p.midi for p in el.pitches]
                elif isinstance(el, m21.note.Note):
                    pitches = [el.pitch.midi]
                else:
                    continue
                off = float(el.offset)
                dur = float(el.duration.quarterLength)
                max_ql = max(max_ql, off + dur)
                for midi_num in pitches:
                    notes.append((off, dur, midi_num))

            color = CHANNEL_COLORS[i % len(CHANNEL_COLORS)]
            roll_channels.append({"notes": notes, "color": color})

            self._add_channel_row(i, program, color)

        self.total_ql = max(max_ql, 0.001)
        self.piano_roll.set_data(roll_channels, self.total_ql)

    def _clear_channel_rows(self):
        """채널 패널의 기존 행(라벨+콤보박스)을 모두 제거합니다."""
        for row, combo in self.channel_rows:
            self.channels_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self.channel_rows = []

    def _add_channel_row(self, index, program, color):
        """채널 패널에 채널 하나(색상 표시 + 악기 선택 콤보박스)를 추가합니다."""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        swatch = QLabel()
        swatch.setFixedSize(14, 14)
        swatch.setStyleSheet(f"background-color: {color.name()}; border-radius: 3px;")

        label = QLabel(f"Ch{index + 1}")
        label.setFixedWidth(40)
        label.setStyleSheet("font-size: 12px; color: #e4e4e7;")

        combo = QComboBox()
        combo.addItems([f"{i:03d}: {name}" for i, name in enumerate(GM_INSTRUMENT_NAMES)])
        combo.setCurrentIndex(max(0, min(program, 127)))
        combo.setStyleSheet("""
            QComboBox { background-color: #3f3f46; color: #ffffff; border-radius: 4px; padding: 3px 6px; font-size: 12px; }
            QComboBox QAbstractItemView { background-color: #27272a; color: #e4e4e7; selection-background-color: #0284c7; }
        """)
        combo.currentIndexChanged.connect(lambda program_idx, ch=index: self.on_channel_instrument_changed(ch, program_idx))

        row_layout.addWidget(swatch)
        row_layout.addWidget(label)
        row_layout.addWidget(combo, stretch=1)

        # stretch 아이템 앞에 삽입
        self.channels_layout.insertWidget(self.channels_layout.count() - 1, row)
        self.channel_rows.append((row, combo))

    def on_channel_instrument_changed(self, channel_index, program):
        """채널 패널에서 악기를 바꾸면 해당 파트의 악기를 갱신하고 재생용 MIDI를 재생성합니다."""
        if not self.loaded_score or channel_index >= len(self.loaded_score.parts):
            return

        part = self.loaded_score.parts[channel_index]
        for inst in list(part.recurse().getElementsByClass(m21.instrument.Instrument)):
            part.remove(inst, recurse=True)
        new_inst = m21.instrument.Instrument()
        new_inst.midiProgram = program
        part.insert(0, new_inst)

        # 원본과 달라졌음을 표시 (Export 시 이 변경을 반영하기 위함)
        self.instrument_modified = True

        # 색상 스와치는 그대로 두고, 재생용 MIDI만 새 악기 반영해 재생성
        self._rewrite_temp_midi_from_score()

    def _rewrite_temp_midi_from_score(self):
        """현재 self.loaded_score를 새 임시 MIDI로 내보내고, 재생 대상 파일을 교체합니다."""
        if not self.loaded_score:
            return

        # 재생 중이면 정지 (악기 변경은 다음 재생부터 반영되면 충분함)
        self.on_stop_clicked()

        old_temp_to_remove = self.current_midi_file if self.temp_midi_obj else None

        new_temp_obj = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
        new_temp_obj.close()
        try:
            self.loaded_score.write("midi", fp=new_temp_obj.name)
        except Exception as e:
            QMessageBox.warning(self, "Instrument Change Failed", f"Failed to apply instrument change:\n{e}")
            return

        if old_temp_to_remove:
            try:
                Path(old_temp_to_remove).unlink(missing_ok=True)
            except Exception:
                pass

        self.temp_midi_obj = new_temp_obj
        self.current_midi_file = new_temp_obj.name

    def on_play_clicked(self):
        """오디오 실시간 합성을 시작합니다."""
        if not self.current_midi_file:
            QMessageBox.warning(self, "No File Loaded", "Please open a Score or MIDI file first.")
            return

        if not self.fs_synth:
            QMessageBox.critical(self, "Engine Error", "Fluidsynth synthesizer engine is not active.")
            return

        try:
            if self.is_paused:
                # 일시정지 상태 복구
                if hasattr(self.fs_synth, "player") and self.fs_synth.player:
                    fluidsynth.fluid_player_play(self.fs_synth.player)
                self.is_paused = False
                self.is_playing = True
                self.timer.start(1000)
            else:
                # 완전 신규 재생 시작
                # play_midi_file 내부에서 자동으로 player를 새로 만들고 play 해줌
                self.fs_synth.play_midi_file(str(self.current_midi_file))
                
                # 볼륨(게인) 설정 동기화
                self.on_volume_changed(self.volume_slider.value())
                
                self.is_playing = True
                self.is_paused = False
                self.play_time_seconds = 0
                
                self.timer.start(1000)
                self.lbl_total_time.setText("Playing")
            
            # 버튼 상태 제어
            self.btn_play.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.btn_stop.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Playback Error", f"An error occurred during music playback:\n{e}")

    def on_pause_clicked(self):
        """신디사이저 연주를 일시정지합니다."""
        if self.is_playing and not self.is_paused:
            try:
                if hasattr(self.fs_synth, "player") and self.fs_synth.player:
                    fluidsynth.fluid_player_stop(self.fs_synth.player)
                self.is_paused = True
                self.is_playing = False
                self.timer.stop()
                
                self.btn_play.setEnabled(True)
                self.btn_pause.setEnabled(False)
                self.lbl_total_time.setText("Paused")
            except Exception as e:
                print(f"[경고] 일시정지 제어 실패: {e}")

    def on_stop_clicked(self):
        """연주를 완전 정지하고 플레이어를 리셋합니다."""
        self.timer.stop()
        self.play_time_seconds = 0
        self.lbl_current_time.setText("00:00")
        self.piano_roll.set_playhead(0.0)

        try:
            if hasattr(self.fs_synth, "player") and self.fs_synth.player:
                # play_midi_stop가 내부적으로 stop, seek, delete_player를 전부 한 번에 안전히 해줌
                self.fs_synth.play_midi_stop()
        except Exception as e:
            print(f"[경고] 플레이어 정지 실패: {e}")
            
        self.is_playing = False
        self.is_paused = False
        
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.lbl_total_time.setText("Stopped")

    def on_volume_changed(self, value):
        """사용자 슬라이더 볼륨 값에 맞춰 마스터 게인을 실시간 동기화합니다."""
        if self.fs_synth:
            # 0~100 범위 -> 0.0~1.0 배율 매핑
            gain = value / 100.0
            try:
                self.fs_synth.setting('synth.gain', gain)
            except Exception as e:
                print(f"[경고] 볼륨 조절 실패: {e}")

    def update_playback_time(self):
        """1초마다 재생 경과 시간을 업데이트하여 라벨과 피아노롤 플레이헤드에 표기합니다."""
        if self.is_playing:
            self.play_time_seconds += 1
            mins = self.play_time_seconds // 60
            secs = self.play_time_seconds % 60
            self.lbl_current_time.setText(f"{mins:02d}:{secs:02d}")

            # 경과 시간(초) -> quarterLength로 환산해 피아노롤 재생 위치 갱신 (근사치, 1초 단위)
            ql = self.play_time_seconds * (self.tempo_bpm / 60.0)
            self.piano_roll.set_playhead(ql)

    # -----------------------------------------------------------------------
    # 리소스 안전 정리 (Cleanup)
    # -----------------------------------------------------------------------

    def cleanup_temp_midi(self):
        """MusicXML 로드를 위해 임시로 생성했던 MIDI 파일을 삭제합니다."""
        if self.current_midi_file and self.temp_midi_obj:
            try:
                path = Path(self.current_midi_file)
                if path.exists():
                    path.unlink(missing_ok=True)
            except Exception as e:
                print(f"[경고] 임시 MIDI 파일 제거 실패: {e}")
            self.current_midi_file = None
            self.temp_midi_obj = None

    def cleanup_resources(self):
        """앱 종료 시 활성화된 신디사이저 오디오 채널과 스레드를 완전히 종료합니다."""
        print("[정보] 신디사이저 리소스 안전 정리 프로세스 시작...")
        self.on_stop_clicked()
        self.cleanup_temp_midi()
        
        try:
            # 수동 생성한 오디오 드라이버 소멸
            if hasattr(self, "fs_adriver") and self.fs_adriver:
                fluidsynth.delete_fluid_audio_driver(self.fs_adriver)
                self.fs_adriver = None
                
            # 신디사이저 소멸
            if self.fs_synth:
                self.fs_synth.delete()
                self.fs_synth = None
        except Exception as e:
            print(f"[경고] 신디사이저 소멸 도중 예외 발생: {e}")

    def show_about_dialog(self):
        """도움말 -> 정보 알림창 표시"""
        QMessageBox.about(
            self, "About MusicXML Player",
            "<h3>MusicXML & MIDI Synthesizer Player</h3>"
            "<p>Version: 1.0.0 (PySide6)</p>"
            "<p>This program is a score player using <b>music21</b> converter and <b>FluidSynth</b> SoundFont rendering.</p>"
            "<p>© 2026 Advanced Agentic Coding Project.</p>"
        )


def main():
    app = QApplication(sys.argv)
    
    # 윈도우 한글 폰트 강제 적용하여 UI 가독성 개선
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    player = MusicXMLPlayer()
    player.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
개선된 음성 텍스트 변환기 - 메인 애플리케이션
"""

import os
import sys
import threading
import traceback
import pygame
import time
from pathlib import Path

# PyQt5 imports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QComboBox, QProgressBar, QTextEdit, QFileDialog,
                            QMessageBox, QGroupBox, QFrame, QStatusBar,
                            QGridLayout, QSplitter, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFont, QIcon

# 필요한 패키지 확인
required_packages = {
    "speech_recognition": "SpeechRecognition",
    "pydub": "pydub",
    "pygame": "pygame"
}

missing_packages = []
for module, package in required_packages.items():
    try:
        __import__(module)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    QMessageBox.critical(None, "필수 패키지 누락", 
                        f"다음 패키지를 설치해야 합니다: {', '.join(missing_packages)}\n"
                        f"다음 명령어를 실행하세요: pip install {' '.join(missing_packages)}")
    sys.exit(1)

# 설정 및 유틸리티 임포트
try:
    from config import LANGUAGES, UI_CONFIG, SAVE_CONFIG, AUDIO_CONFIG, SUPPORTED_AUDIO_FORMATS, SUPPORTED_VIDEO_FORMATS
    from utils import (get_documents_dir, find_ffmpeg_path, find_ffprobe_path, 
                      check_internet_connection, get_file_size_mb, create_temp_directory, 
                      cleanup_temp_files, format_duration, validate_audio_file)
    from ffmpeg_installer import check_and_install_ffmpeg
except ImportError as e:
    QMessageBox.critical(None, "모듈 임포트 오류", 
                        f"필요한 모듈을 찾을 수 없습니다: {e}\n"
                        "config.py, utils.py, ffmpeg_installer.py 파일이 있는지 확인하세요.")
    sys.exit(1)

# FFmpeg 확인 및 설치
if not check_and_install_ffmpeg():
    sys.exit(1)

# 필요한 패키지 임포트
import speech_recognition as sr
from pydub import AudioSegment

class RecognitionThread(QThread):
    """음성 인식 스레드"""
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, audio_file, language, temp_dir, chunk_length_ms=60000):
        super().__init__()
        self.audio_file = audio_file
        self.language = language
        self.temp_dir = temp_dir
        self.chunk_length_ms = chunk_length_ms
        self.is_running = True
    
    def run(self):
        try:
            # 인터넷 연결 확인
            if not check_internet_connection():
                self.error.emit("인터넷 연결이 확인되지 않습니다. Google 음성 인식은 인터넷이 필요합니다.")
                return
            
            # 오디오 로드
            self.status.emit("오디오 파일 로드 중...")
            self.progress.emit(10)
            
            # FFmpeg 경로 설정
            ffmpeg_path = find_ffmpeg_path()
            if not ffmpeg_path:
                self.error.emit("FFmpeg를 찾을 수 없습니다.")
                return
            
            os.environ['FFMPEG_BINARY'] = ffmpeg_path
            
            # 오디오 로드
            file_ext = os.path.splitext(self.audio_file)[1].lower()
            audio_segment = self._load_audio_file(file_ext)
            
            self.progress.emit(20)
            
            # WAV로 변환
            temp_wav = os.path.join(self.temp_dir, "temp_audio.wav")
            
            # 기존 파일이 있다면 삭제
            try:
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
            except Exception as e:
                print(f"[WARNING] 기존 임시 파일 삭제 실패: {e}")
            
            # 새로운 파일 생성
            try:
                audio_segment.export(temp_wav, format="wav")
            except Exception as e:
                # 대안: 다른 파일명 사용
                temp_wav = os.path.join(self.temp_dir, f"temp_audio_{int(time.time())}.wav")
                audio_segment.export(temp_wav, format="wav")
            
            self.progress.emit(30)
            
            # 음성 인식
            lang_code = LANGUAGES.get(self.language)
            
            chunks = self.split_audio_to_chunks(audio_segment, self.chunk_length_ms)
            recognizer = sr.Recognizer()
            
            full_text = ""
            for i, chunk in enumerate(chunks):
                if not self.is_running:
                    break
                    
                progress = 30 + (i / len(chunks)) * 60
                self.progress.emit(int(progress))
                self.status.emit(f"인식 중... 청크 {i+1}/{len(chunks)}")
                
                chunk_file = os.path.join(self.temp_dir, f"chunk_{i}_{int(time.time())}.wav")
                
                # 기존 청크 파일이 있다면 삭제
                try:
                    if os.path.exists(chunk_file):
                        os.remove(chunk_file)
                except:
                    pass
                
                chunk.export(chunk_file, format="wav")
                
                with sr.AudioFile(chunk_file) as source:
                    audio_data = recognizer.record(source)
                    try:
                        text = recognizer.recognize_google(audio_data, language=lang_code)
                        full_text += text + " "
                    except sr.UnknownValueError:
                        full_text += "[인식 불가] "
                    except sr.RequestError as e:
                        full_text += f"[API 요청 오류: {e}] "
                
                # 청크 파일 즉시 삭제
                try:
                    os.remove(chunk_file)
                except:
                    pass
            
            self.progress.emit(100)
            self.status.emit("음성 인식 완료")
            self.finished.emit(full_text)
            
        except Exception as e:
            self.error.emit(f"음성 인식 중 오류 발생: {e}")
    
    def _load_audio_file(self, file_ext):
        """오디오 파일을 로드합니다."""
        if file_ext == ".mp3":
            return AudioSegment.from_mp3(self.audio_file)
        elif file_ext == ".wav":
            return AudioSegment.from_wav(self.audio_file)
        elif file_ext in [".m4a", ".aac"]:
            return AudioSegment.from_file(self.audio_file, format="m4a")
        elif file_ext == ".flac":
            return AudioSegment.from_file(self.audio_file, format="flac")
        elif file_ext == ".ogg":
            return AudioSegment.from_file(self.audio_file, format="ogg")
        else:
            return AudioSegment.from_file(self.audio_file)
    
    def split_audio_to_chunks(self, audio_segment, chunk_length_ms):
        """오디오를 청크로 분할합니다."""
        chunks = []
        total_length = len(audio_segment)
        
        for i in range(0, total_length, chunk_length_ms):
            chunk = audio_segment[i:i + chunk_length_ms]
            chunks.append(chunk)
        
        return chunks
    
    def stop(self):
        """스레드를 중지합니다."""
        self.is_running = False

class AudioTranscriber(QMainWindow):
    """음성 텍스트 변환기 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.audio_file = None
        self.audio_segment = None
        self.is_playing = False
        self.playing_thread = None
        self.recognition_thread = None
        
        # 임시 디렉토리 생성
        self.temp_dir = create_temp_directory()
        if not self.temp_dir:
            QMessageBox.critical(self, "오류", "임시 디렉토리 생성에 실패했습니다.")
            sys.exit(1)
        
        self.temp_wav = os.path.join(self.temp_dir, "temp_audio.wav")
        
        # Pygame 초기화
        try:
            pygame.mixer.init()
        except pygame.error as e:
            QMessageBox.warning(self, "오디오 초기화 오류", f"Pygame 초기화 실패: {e}")
        
        # GUI 구성
        self.init_ui()
    
    def init_ui(self):
        """UI를 초기화합니다."""
        self.setWindowTitle("음성 텍스트 변환기 (개선된 버전)")
        self.setGeometry(100, 100, *UI_CONFIG["window_size"])
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 상단 그룹 (파일 선택 및 제어)
        control_group = QGroupBox("음성/영상 파일 선택 및 제어")
        control_layout = QVBoxLayout(control_group)
        
        # 파일 선택
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("파일을 선택하세요...")
        browse_button = QPushButton("파일 찾기")
        browse_button.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(browse_button)
        control_layout.addLayout(file_layout)
        
        # 파일 정보 표시
        self.file_info_label = QLabel("파일 정보: 선택된 파일이 없습니다")
        self.file_info_label.setStyleSheet("color: gray; font-size: 10px;")
        control_layout.addWidget(self.file_info_label)
        
        # 오디오 제어
        audio_layout = QHBoxLayout()
        self.play_button = QPushButton("재생")
        self.play_button.clicked.connect(self.toggle_play)
        self.play_button.setEnabled(False)
        
        self.auto_save_checkbox = QCheckBox("자동 저장")
        self.auto_save_checkbox.setChecked(True)
        
        audio_layout.addWidget(self.play_button)
        audio_layout.addStretch()
        audio_layout.addWidget(self.auto_save_checkbox)
        control_layout.addLayout(audio_layout)
        
        main_layout.addWidget(control_group)
        
        # 음성 인식 설정 그룹
        recognition_group = QGroupBox("음성 인식 설정")
        recognition_layout = QVBoxLayout(recognition_group)
        
        # 언어 선택
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel("언어:"))
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(list(LANGUAGES.keys()))
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        recognition_layout.addLayout(language_layout)
        
        # 실행 버튼
        button_layout = QHBoxLayout()
        self.recognize_button = QPushButton("음성 인식 시작")
        self.recognize_button.clicked.connect(self.start_recognition)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        button_layout.addWidget(self.progress_bar)
        button_layout.addWidget(self.recognize_button)
        recognition_layout.addLayout(button_layout)
        
        main_layout.addWidget(recognition_group)
        
        # 결과 텍스트 그룹
        result_group = QGroupBox("변환 결과")
        result_layout = QVBoxLayout(result_group)
        
        self.text_result = QTextEdit()
        self.text_result.setFont(QFont(UI_CONFIG["font_family"], UI_CONFIG["font_size"]))
        result_layout.addWidget(self.text_result)
        
        # 하단 버튼들
        bottom_layout = QHBoxLayout()
        clear_button = QPushButton("결과 지우기")
        clear_button.clicked.connect(self.clear_result)
        
        save_button = QPushButton("텍스트 저장")
        save_button.clicked.connect(self.save_text)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(clear_button)
        bottom_layout.addWidget(save_button)
        result_layout.addLayout(bottom_layout)
        
        main_layout.addWidget(result_group)
        
        # 상태 표시줄
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비됨")
    
    def browse_file(self):
        """파일을 선택합니다."""
        filetypes = (f"미디어 파일 (*{' *'.join(AUDIO_CONFIG['supported_formats'])});;"
                    f"오디오 파일 (*{' *'.join(SUPPORTED_AUDIO_FORMATS)});;"
                    f"비디오 파일 (*{' *'.join(SUPPORTED_VIDEO_FORMATS)});;"
                    "모든 파일 (*.*)")
        
        filepath, _ = QFileDialog.getOpenFileName(
            self, "미디어 파일 선택", "", filetypes
        )
        
        if filepath:
            # 파일 유효성 검사
            is_valid, message = validate_audio_file(filepath)
            if not is_valid:
                QMessageBox.warning(self, "파일 오류", message)
                return
            
            self.audio_file = filepath
            self.file_edit.setText(filepath)
            
            # 파일 정보 표시
            file_size_mb = get_file_size_mb(filepath)
            filename = os.path.basename(filepath)
            self.file_info_label.setText(f"파일: {filename} | 크기: {file_size_mb:.1f}MB")
            
            # 비디오 파일인 경우 오디오 추출
            file_ext = os.path.splitext(filepath)[1].lower()
            if file_ext in SUPPORTED_VIDEO_FORMATS:
                self.extract_audio_from_video(filepath)
            else:
                self.load_audio()
            
            self.status_bar.showMessage(f"파일 로드됨: {filename}")
    
    def extract_audio_from_video(self, video_path):
        """비디오 파일에서 오디오를 추출합니다."""
        try:
            self.status_bar.showMessage("비디오에서 오디오 추출 중...")
            QApplication.processEvents()
            
            # 임시 오디오 파일 경로
            temp_audio = os.path.join(self.temp_dir, "extracted_audio.wav")
            
            # FFmpeg 경로 확인
            ffmpeg_path = find_ffmpeg_path()
            if not ffmpeg_path:
                QMessageBox.critical(self, "FFmpeg 오류", "FFmpeg를 찾을 수 없습니다.")
                return
            
            # FFmpeg를 사용하여 오디오 추출
            command = [
                ffmpeg_path, '-i', video_path,
                '-vn',  # 비디오 스트림 제외
                '-acodec', 'pcm_s16le',  # WAV 형식으로 인코딩
                '-ar', '44100',  # 샘플레이트
                '-ac', '2',  # 스테레오
                '-y',  # 기존 파일 덮어쓰기
                temp_audio
            ]
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 진행 상태 표시
            progress_dialog = QMessageBox()
            progress_dialog.setWindowTitle("오디오 추출")
            progress_dialog.setText("오디오 추출 중...")
            progress_dialog.setStandardButtons(QMessageBox.NoButton)
            progress_dialog.show()
            
            # 프로세스 완료 대기
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.audio_file = temp_audio
                self.load_audio()
                progress_dialog.close()
                QMessageBox.information(self, "추출 완료", "비디오에서 오디오가 성공적으로 추출되었습니다.")
            else:
                progress_dialog.close()
                QMessageBox.critical(self, "추출 실패", f"오디오 추출 중 오류가 발생했습니다:\n{stderr.decode()}")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"오디오 추출 중 오류가 발생했습니다: {e}")
            self.status_bar.showMessage("오류: 오디오 추출 실패")
    
    def load_audio(self):
        """오디오 파일을 로드합니다."""
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.play_button.setText("재생")
            
            file_ext = os.path.splitext(self.audio_file)[1].lower()
            self.status_bar.showMessage(f"오디오 파일 로드 중...")
            QApplication.processEvents()
            
            # FFmpeg 경로 설정
            ffmpeg_path = find_ffmpeg_path()
            ffprobe_path = find_ffprobe_path()
            
            if not ffmpeg_path:
                QMessageBox.critical(self, "FFmpeg 오류", "FFmpeg를 찾을 수 없습니다.")
                return
            
            # pydub에 FFmpeg 경로 설정
            os.environ['FFMPEG_BINARY'] = ffmpeg_path
            if ffprobe_path:
                os.environ['FFPROBE_BINARY'] = ffprobe_path
            
            # 오디오 로드
            self.audio_segment = self._load_audio_segment(file_ext)
            
            try:
                # 임시 파일이 이미 존재하면 삭제
                if os.path.exists(self.temp_wav):
                    os.remove(self.temp_wav)
                
                # WAV 파일로 변환
                self.audio_segment.export(self.temp_wav, format="wav")
                
                # 파일 권한 확인
                if not os.access(self.temp_wav, os.R_OK):
                    os.chmod(self.temp_wav, 0o666)
                
                pygame.mixer.music.load(self.temp_wav)
                self.play_button.setEnabled(True)
                self.status_bar.showMessage(f"오디오 파일이 로드되었습니다")
            except (pygame.error, OSError) as e:
                QMessageBox.critical(self, "재생 오류", f"오디오 파일을 재생할 수 없습니다: {e}")
                self.status_bar.showMessage("오류: 파일을 재생할 수 없습니다")
        
        except Exception as e:
            QMessageBox.critical(self, "오류", f"오디오 파일 로드 실패: {e}")
            self.status_bar.showMessage("오류: 오디오 파일을 로드할 수 없습니다.")
    
    def _load_audio_segment(self, file_ext):
        """오디오 세그먼트를 로드합니다."""
        if file_ext == ".mp3":
            return AudioSegment.from_mp3(self.audio_file)
        elif file_ext == ".wav":
            return AudioSegment.from_wav(self.audio_file)
        elif file_ext in [".m4a", ".aac"]:
            return AudioSegment.from_file(self.audio_file, format="m4a")
        elif file_ext == ".flac":
            return AudioSegment.from_file(self.audio_file, format="flac")
        elif file_ext == ".ogg":
            return AudioSegment.from_file(self.audio_file, format="ogg")
        else:
            return AudioSegment.from_file(self.audio_file)
    
    def toggle_play(self):
        """오디오 재생을 토글합니다."""
        if not self.audio_file:
            QMessageBox.information(self, "알림", "먼저 오디오 파일을 선택하세요.")
            return
        
        if not self.temp_wav or not os.path.exists(self.temp_wav):
            QMessageBox.information(self, "알림", "오디오 파일이 아직 준비되지 않았습니다.")
            return
        
        try:
            if self.is_playing:
                pygame.mixer.music.pause()
                self.is_playing = False
                self.play_button.setText("재생")
                self.status_bar.showMessage("일시 정지됨")
            else:
                pygame.mixer.music.load(self.temp_wav)
                pygame.mixer.music.play()
                self.is_playing = True
                self.play_button.setText("일시 정지")
                self.status_bar.showMessage("재생 중...")
        except pygame.error as e:
            QMessageBox.critical(self, "재생 오류", f"오디오 재생 중 오류 발생: {e}")
            self.status_bar.showMessage(f"오류: {e}")
    
    def start_recognition(self):
        """음성 인식을 시작합니다."""
        if not self.audio_file:
            QMessageBox.information(self, "알림", "먼저 오디오 파일을 선택하세요.")
            return
        
        if self.recognition_thread and self.recognition_thread.isRunning():
            QMessageBox.information(self, "알림", "이미 음성 인식이 진행 중입니다.")
            return
        
        language = self.language_combo.currentText()
        
        self.recognition_thread = RecognitionThread(self.audio_file, language, self.temp_dir)
        self.recognition_thread.finished.connect(self.on_recognition_finished)
        self.recognition_thread.progress.connect(self.progress_bar.setValue)
        self.recognition_thread.status.connect(self.status_bar.showMessage)
        self.recognition_thread.error.connect(self.on_recognition_error)
        
        self.recognition_thread.start()
        
        self.recognize_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("음성 인식 진행 중...")
    
    def on_recognition_finished(self, text):
        """음성 인식이 완료되었을 때 호출됩니다."""
        self.recognize_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("음성 인식 완료")
        
        if text.strip():
            self.text_result.setPlainText(text)
            
            # 완료 메시지 표시
            text_length = len(text.strip())
            QMessageBox.information(self, "변환 완료", 
                                  f"음성 인식이 완료되었습니다!\n\n인식된 텍스트 길이: {text_length}자")
            
            # 자동 저장
            if self.auto_save_checkbox.isChecked():
                self.save_text_to_file(text, auto_save=True)
        else:
            self.text_result.setPlainText("인식된 텍스트가 없습니다.")
            QMessageBox.warning(self, "알림", "음성 인식 결과가 없습니다.")
    
    def on_recognition_error(self, error_msg):
        """음성 인식 중 오류가 발생했을 때 호출됩니다."""
        self.recognize_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"오류: {error_msg}")
        QMessageBox.critical(self, "오류", error_msg)
        self.text_result.setPlainText(f"오류 발생: {error_msg}")
    
    def save_text_to_file(self, text, filepath=None, auto_save=False):
        """텍스트를 파일로 저장합니다."""
        if not text:
            if not auto_save:
                QMessageBox.information(self, "알림", "저장할 텍스트가 없습니다.")
            return False
        
        if filepath is None:
            if auto_save:
                docs_dir = get_documents_dir()
                speech_to_text_dir = os.path.join(docs_dir, SAVE_CONFIG["auto_save_dir"])
                os.makedirs(speech_to_text_dir, exist_ok=True)
                base_name = os.path.splitext(os.path.basename(self.audio_file))[0]
                filepath = os.path.join(speech_to_text_dir, f"{base_name}.txt")
            else:
                default_filename = "audio_transcript.txt"
                if self.audio_file:
                    base_name = os.path.splitext(os.path.basename(self.audio_file))[0]
                    default_filename = f"{base_name}_transcript.txt"
                
                filepath, _ = QFileDialog.getSaveFileName(
                    self, "텍스트 저장", default_filename,
                    "텍스트 파일 (*.txt);;모든 파일 (*.*)"
                )
        
        if not filepath:
            return False
        
        try:
            # 인코딩 시도
            try:
                with open(filepath, 'w', encoding=SAVE_CONFIG["default_encoding"]) as file:
                    file.write(text)
            except UnicodeEncodeError:
                with open(filepath, 'w', encoding=SAVE_CONFIG["fallback_encoding"]) as file:
                    file.write(text)
            
            self.status_bar.showMessage(f"텍스트가 저장되었습니다: {os.path.basename(filepath)}")
            if not auto_save:
                QMessageBox.information(self, "저장 성공", f"텍스트가 성공적으로 저장되었습니다:\n{filepath}")
            return True
            
        except Exception as e:
            error_detail = traceback.format_exc()
            print(f"[ERROR] 텍스트 저장 실패:\n{error_detail}")
            if not auto_save:
                QMessageBox.critical(self, "오류", f"파일 저장 중 오류 발생: {e}")
            return False
    
    def save_text(self):
        """텍스트를 저장합니다."""
        text = self.text_result.toPlainText().strip()
        self.save_text_to_file(text)
    
    def clear_result(self):
        """결과를 지웁니다."""
        self.text_result.clear()
        self.status_bar.showMessage("결과가 지워졌습니다.")
    
    def closeEvent(self, event):
        """애플리케이션 종료 시 호출됩니다."""
        try:
            # 음성 인식 스레드 중지
            if self.recognition_thread and self.recognition_thread.isRunning():
                self.recognition_thread.stop()
                self.recognition_thread.wait(3000)  # 3초 대기
            
            # 오디오 재생 중지
            pygame.mixer.music.stop()
            
            # 임시 파일 정리
            if hasattr(self, 'temp_dir') and self.temp_dir:
                cleanup_temp_files(self.temp_dir)
                
        except Exception as e:
            print(f"[WARNING] 종료 시 정리 작업 실패: {e}")
        
        event.accept()

def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    app.setApplicationName("음성 텍스트 변환기 (개선된 버전)")
    
    # Windows에서 콘솔 창 숨기기
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    window = AudioTranscriber()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
import os
import threading
import sys
import subprocess
import traceback
import urllib.request
import tempfile
import pygame
import time
from pathlib import Path
import zipfile
import shutil
import platform

# PyQt5 imports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QComboBox, QProgressBar, QTextEdit, QFileDialog,
                            QMessageBox, QGroupBox, QFrame, QStatusBar,
                            QGridLayout, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFont, QIcon

# FFmpeg 설치 함수
def install_ffmpeg():
    """FFmpeg를 자동으로 설치합니다."""
    try:
        if sys.platform == "win32":
            # Windows용 FFmpeg 다운로드 및 설치
            ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "ffmpeg.zip")
            
            # 다운로드 진행 상태 표시
            progress_dialog = QMessageBox()
            progress_dialog.setWindowTitle("FFmpeg 설치")
            progress_dialog.setText("FFmpeg 설치 준비 중...")
            progress_dialog.setStandardButtons(QMessageBox.NoButton)
            progress_dialog.show()
            
            def update_progress(block_num, block_size, total_size):
                if total_size > 0:
                    progress = min(100, int(block_num * block_size * 100 / total_size))
                    progress_dialog.setText(f"FFmpeg 다운로드 중... {progress}%")
                    QApplication.processEvents()
            
            # FFmpeg 다운로드
            urllib.request.urlretrieve(ffmpeg_url, zip_path, update_progress)
            
            # 압축 해제
            progress_dialog.setText("압축 해제 중...")
            QApplication.processEvents()
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                total_files = len(zip_ref.namelist())
                for i, file in enumerate(zip_ref.namelist()):
                    zip_ref.extract(file, temp_dir)
                    progress = int((i + 1) * 100 / total_files)
                    progress_dialog.setText(f"압축 해제 중... {progress}%")
                    QApplication.processEvents()
            
            # FFmpeg 실행 파일을 시스템 경로에 복사
            progress_dialog.setText("FFmpeg 설치 중...")
            QApplication.processEvents()
            
            ffmpeg_dir = os.path.join(temp_dir, "ffmpeg-master-latest-win64-gpl", "bin")
            system_path = os.environ.get('PATH', '')
            new_path = os.path.join(os.path.expanduser("~"), "ffmpeg", "bin")
            
            # FFmpeg 폴더 생성
            os.makedirs(new_path, exist_ok=True)
            
            # 실행 파일 복사
            files = [f for f in os.listdir(ffmpeg_dir) if f.endswith('.exe')]
            total_files = len(files)
            for i, file in enumerate(files):
                shutil.copy2(os.path.join(ffmpeg_dir, file), new_path)
                progress = int((i + 1) * 100 / total_files)
                progress_dialog.setText(f"설치 중... {progress}%")
                QApplication.processEvents()
            
            # 환경 변수 PATH에 추가
            if new_path not in system_path:
                os.environ['PATH'] = f"{new_path};{system_path}"
            
            # 임시 파일 정리
            progress_dialog.setText("임시 파일 정리 중...")
            QApplication.processEvents()
            
            shutil.rmtree(temp_dir)
            
            progress_dialog.setText("설치 완료!")
            QApplication.processEvents()
            
            time.sleep(1)  # 완료 메시지를 잠시 보여줌
            progress_dialog.close()
            QMessageBox.information(None, "설치 완료", "FFmpeg가 성공적으로 설치되었습니다.")
            return True
            
        elif sys.platform == "darwin":
            # macOS용 FFmpeg 설치 (Homebrew 사용)
            progress_dialog = QMessageBox()
            progress_dialog.setWindowTitle("FFmpeg 설치")
            progress_dialog.setText("FFmpeg 설치 중...")
            progress_dialog.setStandardButtons(QMessageBox.NoButton)
            progress_dialog.show()
            
            try:
                subprocess.run(['brew', 'install', 'ffmpeg'], check=True)
                progress_dialog.close()
                QMessageBox.information(None, "설치 완료", "FFmpeg가 성공적으로 설치되었습니다.")
                return True
            except subprocess.CalledProcessError:
                progress_dialog.close()
                QMessageBox.critical(None, "설치 실패", "Homebrew를 통해 FFmpeg 설치에 실패했습니다.")
                return False
        else:
            QMessageBox.critical(None, "지원되지 않는 시스템", "현재 시스템에서는 자동 설치를 지원하지 않습니다.")
            return False
            
    except Exception as e:
        QMessageBox.critical(None, "설치 오류", f"FFmpeg 설치 중 오류가 발생했습니다: {e}")
        return False

# FFmpeg 확인 및 설치
def check_and_install_ffmpeg():
    """FFmpeg가 설치되어 있는지 확인하고, 없으면 설치를 시도합니다."""
    # 가능한 FFmpeg 경로 목록 (macOS)
    possible_ffmpeg_paths = [
        'ffmpeg',  # 기본 PATH
        '/usr/local/bin/ffmpeg',  # Homebrew 기본 설치 경로
        '/opt/homebrew/bin/ffmpeg',  # Apple Silicon Homebrew 경로
        '/usr/bin/ffmpeg',  # 시스템 경로
        os.path.expanduser('~/bin/ffmpeg'),  # 사용자 bin 디렉토리
    ]
    
    # Windows에서 추가 검색 경로
    if sys.platform == "win32":
        possible_ffmpeg_paths.extend([
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'FFmpeg', 'bin', 'ffmpeg.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'FFmpeg', 'bin', 'ffmpeg.exe'),
            os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
        ])
    
    # 각 경로 시도
    for ffmpeg_path in possible_ffmpeg_paths:
        try:
            subprocess.run([ffmpeg_path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"FFmpeg found at: {ffmpeg_path}")
            # 찾은 경로를 환경 변수에 추가
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            if ffmpeg_dir and ffmpeg_dir not in os.environ.get('PATH', ''):
                os.environ['PATH'] = f"{ffmpeg_dir}{os.pathsep}{os.environ.get('PATH', '')}"
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    # 모든 경로에서 찾지 못한 경우
    response = QMessageBox.question(None, "FFmpeg 설치 필요", 
                                   "FFmpeg가 설치되어 있지 않습니다. 자동으로 설치하시겠습니까?\n"
                                   "설치하지 않으려면 '아니오'를 선택하세요.",
                                   QMessageBox.Yes | QMessageBox.No)
    if response == QMessageBox.Yes:
        return install_ffmpeg()
    else:
        QMessageBox.warning(None, "FFmpeg 필요", 
                           "FFmpeg가 필요합니다. 수동으로 설치하세요:\n"
                           "macOS: brew install ffmpeg\n"
                           "Windows: https://ffmpeg.org/download.html에서 다운로드")
        return False

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

# FFmpeg 확인 및 설치
if not check_and_install_ffmpeg():
    sys.exit(1)

# 필요한 패키지 임포트
import speech_recognition as sr
from pydub import AudioSegment

# 문서 폴더 경로 가져오기
def get_documents_dir():
    """사용자의 문서 폴더 경로를 가져옵니다."""
    try:
        if sys.platform == "win32":
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                    return winreg.QueryValueEx(key, "Personal")[0]
            except ImportError:
                return os.path.join(os.path.expanduser("~"), "Documents")
            except Exception as e:
                print(f"[ERROR] 문서 폴더 경로 가져오기 실패 (Windows): {e}")
                return os.path.join(os.path.expanduser("~"), "Documents")
        elif sys.platform == "darwin":
            return os.path.join(os.path.expanduser("~"), "Documents")
        else:
            return os.path.join(os.path.expanduser("~"), "Documents")
    except Exception as e:
        print(f"[ERROR] 문서 폴더 경로 가져오기 실패: {e}")
        return os.path.join(os.path.expanduser("~"), "Documents")

# 스레드 안전을 위한 시그널 프록시
class SignalProxy(QObject):
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    text_updated = pyqtSignal(str)
    recognition_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

class RecognitionThread(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, audio_file, language, temp_dir):
        super().__init__()
        self.audio_file = audio_file
        self.language = language
        self.temp_dir = temp_dir
        self.is_running = True
    
    def run(self):
        try:
            # 오디오 로드
            self.status.emit("오디오 파일 로드 중...")
            self.progress.emit(10)
            
            file_ext = os.path.splitext(self.audio_file)[1].lower()
            
            # FFmpeg 경로 확인
            ffmpeg_path = 'ffmpeg'
            possible_ffmpeg_paths = [
                'ffmpeg', '/usr/local/bin/ffmpeg', '/opt/homebrew/bin/ffmpeg',
                '/usr/bin/ffmpeg', os.path.expanduser('~/bin/ffmpeg')
            ]
            
            if sys.platform == "win32":
                possible_ffmpeg_paths.extend([
                    os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'FFmpeg', 'bin', 'ffmpeg.exe'),
                    os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'FFmpeg', 'bin', 'ffmpeg.exe'),
                    os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
                ])
            
            for path in possible_ffmpeg_paths:
                try:
                    subprocess.run([path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    ffmpeg_path = path
                    break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            
            os.environ['FFMPEG_BINARY'] = ffmpeg_path
            
            # 오디오 로드
            if file_ext == ".mp3":
                audio_segment = AudioSegment.from_mp3(self.audio_file)
            elif file_ext == ".wav":
                audio_segment = AudioSegment.from_wav(self.audio_file)
            elif file_ext in [".m4a", ".aac"]:
                audio_segment = AudioSegment.from_file(self.audio_file, format="m4a")
            elif file_ext == ".flac":
                audio_segment = AudioSegment.from_file(self.audio_file, format="flac")
            elif file_ext == ".ogg":
                audio_segment = AudioSegment.from_file(self.audio_file, format="ogg")
            else:
                audio_segment = AudioSegment.from_file(self.audio_file)
            
            self.progress.emit(20)
            
            # WAV로 변환
            temp_wav = os.path.join(self.temp_dir, "temp_audio.wav")
            audio_segment.export(temp_wav, format="wav")
            
            self.progress.emit(30)
            
            # 음성 인식
            lang_code = "ko-KR" if self.language == "한국어" else "en-US" if self.language == "영어" else None
            
            chunk_length_ms = 60000  # 60초 청크
            chunks = self.split_audio_to_chunks(audio_segment, chunk_length_ms)
            
            recognizer = sr.Recognizer()
            
            try:
                urllib.request.urlopen('http://google.com', timeout=1)
            except:
                self.error.emit("인터넷 연결이 확인되지 않습니다. Google 음성 인식은 인터넷이 필요합니다.")
                return
            
            full_text = ""
            for i, chunk in enumerate(chunks):
                if not self.is_running:
                    break
                    
                progress = 30 + (i / len(chunks)) * 60
                self.progress.emit(int(progress))
                self.status.emit(f"인식 중... 청크 {i+1}/{len(chunks)}")
                
                chunk_file = os.path.join(self.temp_dir, f"chunk_{i}.wav")
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
    
    def split_audio_to_chunks(self, audio_segment, chunk_length_ms):
        chunks = []
        total_length = len(audio_segment)
        
        for i in range(0, total_length, chunk_length_ms):
            chunk = audio_segment[i:i + chunk_length_ms]
            chunks.append(chunk)
        
        return chunks
    
    def stop(self):
        self.is_running = False

class AudioTranscriber(QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio_file = None
        self.audio_segment = None
        self.is_playing = False
        self.playing_thread = None
        self.recognition_thread = None
        
        # 임시 디렉토리 생성
        try:
            self.temp_dir = tempfile.mkdtemp()
            self.temp_wav = os.path.join(self.temp_dir, "temp_audio.wav")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"임시 디렉토리 생성 실패: {e}")
            sys.exit(1)
        
        # Pygame 초기화
        try:
            pygame.mixer.init()
        except pygame.error as e:
            QMessageBox.warning(self, "오디오 초기화 오류", f"Pygame 초기화 실패: {e}")
        
        # GUI 구성
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("음성 텍스트 변환기")
        self.setGeometry(100, 100, 900, 700)
        
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
        
        # 오디오 제어
        audio_layout = QHBoxLayout()
        self.play_button = QPushButton("재생")
        self.play_button.clicked.connect(self.toggle_play)
        self.play_button.setEnabled(False)
        
        audio_layout.addWidget(self.play_button)
        audio_layout.addStretch()
        control_layout.addLayout(audio_layout)
        
        main_layout.addWidget(control_group)
        
        # 음성 인식 설정 그룹
        recognition_group = QGroupBox("음성 인식 설정")
        recognition_layout = QVBoxLayout(recognition_group)
        
        # 언어 선택
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel("언어:"))
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["한국어", "영어", "자동 감지"])
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
        self.text_result.setFont(QFont("Consolas", 10))
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
        filetypes = "미디어 파일 (*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.mp4 *.avi *.mkv *.mov *.wmv);;오디오 파일 (*.mp3 *.wav *.m4a *.aac *.flac *.ogg);;비디오 파일 (*.mp4 *.avi *.mkv *.mov *.wmv);;모든 파일 (*.*)"
        
        filepath, _ = QFileDialog.getOpenFileName(
            self, "미디어 파일 선택", "", filetypes
        )
        
        if filepath:
            self.audio_file = filepath
            self.file_edit.setText(filepath)
            
            # 비디오 파일인 경우 오디오 추출
            file_ext = os.path.splitext(filepath)[1].lower()
            if file_ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
                self.extract_audio_from_video(filepath)
            else:
                self.load_audio()
            
            filename = os.path.basename(filepath)
            self.status_bar.showMessage(f"파일 로드됨: {filename}")
    
    def extract_audio_from_video(self, video_path):
        """비디오 파일에서 오디오를 추출합니다."""
        try:
            self.status_bar.showMessage("비디오에서 오디오 추출 중...")
            QApplication.processEvents()
            
            # 임시 오디오 파일 경로
            temp_audio = os.path.join(self.temp_dir, "extracted_audio.wav")
            
            # FFmpeg 경로 확인
            ffmpeg_path = 'ffmpeg'
            possible_ffmpeg_paths = [
                'ffmpeg', '/usr/local/bin/ffmpeg', '/opt/homebrew/bin/ffmpeg',
                '/usr/bin/ffmpeg', os.path.expanduser('~/bin/ffmpeg')
            ]
            
            if sys.platform == "win32":
                possible_ffmpeg_paths.extend([
                    os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'FFmpeg', 'bin', 'ffmpeg.exe'),
                    os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'FFmpeg', 'bin', 'ffmpeg.exe'),
                    os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
                ])
            
            for path in possible_ffmpeg_paths:
                try:
                    subprocess.run([path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    ffmpeg_path = path
                    break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            
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
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.play_button.setText("재생")
            
            file_ext = os.path.splitext(self.audio_file)[1].lower()
            self.status_bar.showMessage(f"오디오 파일 로드 중...")
            QApplication.processEvents()
            
            # FFmpeg 경로 확인
            ffmpeg_path = 'ffmpeg'
            ffprobe_path = 'ffprobe'
            
            possible_ffmpeg_paths = [
                'ffmpeg', '/usr/local/bin/ffmpeg', '/opt/homebrew/bin/ffmpeg',
                '/usr/bin/ffmpeg', os.path.expanduser('~/bin/ffmpeg')
            ]
            
            possible_ffprobe_paths = [
                'ffprobe', '/usr/local/bin/ffprobe', '/opt/homebrew/bin/ffprobe',
                '/usr/bin/ffprobe', os.path.expanduser('~/bin/ffprobe')
            ]
            
            if sys.platform == "win32":
                possible_ffmpeg_paths.extend([
                    os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'FFmpeg', 'bin', 'ffmpeg.exe'),
                    os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'FFmpeg', 'bin', 'ffmpeg.exe'),
                    os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
                ])
                
                possible_ffprobe_paths.extend([
                    os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'FFmpeg', 'bin', 'ffprobe.exe'),
                    os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'FFmpeg', 'bin', 'ffprobe.exe'),
                    os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffprobe.exe'),
                ])
            
            for path in possible_ffmpeg_paths:
                try:
                    subprocess.run([path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    ffmpeg_path = path
                    break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
                    
            for path in possible_ffprobe_paths:
                try:
                    subprocess.run([path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    ffprobe_path = path
                    break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            
            # pydub에 FFmpeg 경로 설정
            os.environ['FFMPEG_BINARY'] = ffmpeg_path
            os.environ['FFPROBE_BINARY'] = ffprobe_path
            
            try:
                if file_ext == ".mp3":
                    self.audio_segment = AudioSegment.from_mp3(self.audio_file)
                elif file_ext == ".wav":
                    self.audio_segment = AudioSegment.from_wav(self.audio_file)
                elif file_ext in [".m4a", ".aac"]:
                    self.audio_segment = AudioSegment.from_file(self.audio_file, format="m4a")
                elif file_ext == ".flac":
                    self.audio_segment = AudioSegment.from_file(self.audio_file, format="flac")
                elif file_ext == ".ogg":
                    self.audio_segment = AudioSegment.from_file(self.audio_file, format="ogg")
                else:
                    self.audio_segment = AudioSegment.from_file(self.audio_file)
            except Exception as e:
                if "ffmpeg" in str(e).lower():
                    QMessageBox.critical(self, "FFmpeg 오류", 
                                       f"FFmpeg 관련 오류: {e}\n\n"
                                       f"사용한 FFmpeg 경로: {ffmpeg_path}\n"
                                       f"사용한 FFprobe 경로: {ffprobe_path}\n\n"
                                       "경로가 올바른지 확인하세요.")
                    self.status_bar.showMessage("오류: FFmpeg가 필요합니다")
                    return
                else:
                    raise e
            
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
    
    def toggle_play(self):
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
            self.save_text_to_file(text, auto_save=True)
        else:
            self.text_result.setPlainText("인식된 텍스트가 없습니다.")
            QMessageBox.warning(self, "알림", "음성 인식 결과가 없습니다.")
    
    def on_recognition_error(self, error_msg):
        self.recognize_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"오류: {error_msg}")
        QMessageBox.critical(self, "오류", error_msg)
        self.text_result.setPlainText(f"오류 발생: {error_msg}")
    
    def save_text_to_file(self, text, filepath=None, auto_save=False):
        if not text:
            if not auto_save:
                QMessageBox.information(self, "알림", "저장할 텍스트가 없습니다.")
            return False
        
        if filepath is None:
            if auto_save:
                docs_dir = get_documents_dir()
                speech_to_text_dir = os.path.join(docs_dir, "speech_to_text")
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
            try:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(text)
            except UnicodeEncodeError:
                with open(filepath, 'w', encoding='cp949') as file:
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
        text = self.text_result.toPlainText().strip()
        self.save_text_to_file(text)
    
    def clear_result(self):
        self.text_result.clear()
        self.status_bar.showMessage("결과가 지워졌습니다.")
    
    def closeEvent(self, event):
        try:
            pygame.mixer.music.stop()
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("음성 텍스트 변환기")
    
    # Windows에서 콘솔 창 숨기기
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    window = AudioTranscriber()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
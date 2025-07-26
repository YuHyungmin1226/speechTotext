# -*- coding: utf-8 -*-
"""
FFmpeg 설치 관리자 - 음성 텍스트 변환기
"""

import os
import sys
import subprocess
import tempfile
import urllib.request
import zipfile
import shutil
import time
from PyQt5.QtWidgets import QMessageBox, QApplication
from config import FFMPEG_CONFIG

def install_ffmpeg():
    """FFmpeg를 자동으로 설치합니다."""
    try:
        if sys.platform == "win32":
            return _install_ffmpeg_windows()
        elif sys.platform == "darwin":
            return _install_ffmpeg_macos()
        else:
            QMessageBox.critical(None, "지원되지 않는 시스템", 
                               "현재 시스템에서는 자동 설치를 지원하지 않습니다.")
            return False
            
    except Exception as e:
        QMessageBox.critical(None, "설치 오류", f"FFmpeg 설치 중 오류가 발생했습니다: {e}")
        return False

def _install_ffmpeg_windows():
    """Windows에서 FFmpeg를 설치합니다."""
    try:
        # Windows용 FFmpeg 다운로드 및 설치
        ffmpeg_url = FFMPEG_CONFIG["windows_url"]
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
        
    except Exception as e:
        QMessageBox.critical(None, "설치 오류", f"Windows FFmpeg 설치 중 오류: {e}")
        return False

def _install_ffmpeg_macos():
    """macOS에서 FFmpeg를 설치합니다."""
    try:
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
            QMessageBox.critical(None, "설치 실패", 
                               "Homebrew를 통해 FFmpeg 설치에 실패했습니다.\n"
                               "Homebrew가 설치되어 있는지 확인하세요.")
            return False
        except FileNotFoundError:
            progress_dialog.close()
            QMessageBox.critical(None, "Homebrew 없음", 
                               "Homebrew가 설치되어 있지 않습니다.\n"
                               "https://brew.sh에서 Homebrew를 설치하세요.")
            return False
            
    except Exception as e:
        QMessageBox.critical(None, "설치 오류", f"macOS FFmpeg 설치 중 오류: {e}")
        return False

def check_and_install_ffmpeg():
    """FFmpeg가 설치되어 있는지 확인하고, 없으면 설치를 시도합니다."""
    from utils import find_ffmpeg_path
    
    # FFmpeg 경로 확인
    ffmpeg_path = find_ffmpeg_path()
    if ffmpeg_path:
        return True
    
    # FFmpeg가 없는 경우 설치 여부 확인
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
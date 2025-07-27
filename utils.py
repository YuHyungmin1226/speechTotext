# -*- coding: utf-8 -*-
"""
유틸리티 함수들 - 음성 텍스트 변환기
"""

import os
import sys
import subprocess
import tempfile
import urllib.request
import zipfile
import shutil
import platform
import winreg
import time
from pathlib import Path

def get_documents_dir():
    """사용자의 문서 폴더 경로를 가져옵니다."""
    try:
        if sys.platform == "win32":
            try:
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

def find_ffmpeg_path():
    """FFmpeg 실행 파일의 경로를 찾습니다."""
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
            # exe 파일이 아닌 경우에만 출력
            if not getattr(sys, 'frozen', False):
                print(f"FFmpeg found at: {ffmpeg_path}")
            # 찾은 경로를 환경 변수에 추가
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            if ffmpeg_dir and ffmpeg_dir not in os.environ.get('PATH', ''):
                os.environ['PATH'] = f"{ffmpeg_dir}{os.pathsep}{os.environ.get('PATH', '')}"
            return ffmpeg_path
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    return None

def find_ffprobe_path():
    """FFprobe 실행 파일의 경로를 찾습니다."""
    possible_ffprobe_paths = [
        'ffprobe',  # 기본 PATH
        '/usr/local/bin/ffprobe',  # Homebrew 기본 설치 경로
        '/opt/homebrew/bin/ffprobe',  # Apple Silicon Homebrew 경로
        '/usr/bin/ffprobe',  # 시스템 경로
        os.path.expanduser('~/bin/ffprobe'),  # 사용자 bin 디렉토리
    ]
    
    # Windows에서 추가 검색 경로
    if sys.platform == "win32":
        possible_ffprobe_paths.extend([
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'FFmpeg', 'bin', 'ffprobe.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'FFmpeg', 'bin', 'ffprobe.exe'),
            os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffprobe.exe'),
        ])
    
    # 각 경로 시도
    for ffprobe_path in possible_ffprobe_paths:
        try:
            subprocess.run([ffprobe_path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            # exe 파일이 아닌 경우에만 출력
            if not getattr(sys, 'frozen', False):
                print(f"FFprobe found at: {ffprobe_path}")
            return ffprobe_path
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    return None

def check_internet_connection():
    """인터넷 연결을 확인합니다."""
    try:
        urllib.request.urlopen('http://google.com', timeout=3)
        return True
    except:
        return False

def get_file_size_mb(filepath):
    """파일 크기를 MB 단위로 반환합니다."""
    try:
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024 * 1024)
    except:
        return 0

def create_temp_directory():
    """임시 디렉토리를 생성합니다."""
    try:
        # 사용자 홈 디렉토리에 임시 폴더 생성 (권한 문제 방지)
        home_dir = os.path.expanduser("~")
        temp_base = os.path.join(home_dir, "speech_to_text_temp")
        
        # 기존 임시 폴더가 있다면 정리
        if os.path.exists(temp_base):
            try:
                shutil.rmtree(temp_base, ignore_errors=True)
            except:
                pass
        
        # 새로운 임시 폴더 생성
        temp_dir = os.path.join(temp_base, f"session_{int(time.time())}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # exe 파일이 아닌 경우에만 출력
        if not getattr(sys, 'frozen', False):
            print(f"[INFO] 임시 디렉토리 생성: {temp_dir}")
        return temp_dir
    except Exception as e:
        # exe 파일이 아닌 경우에만 출력
        if not getattr(sys, 'frozen', False):
            print(f"[ERROR] 임시 디렉토리 생성 실패: {e}")
        # 대안: 시스템 임시 디렉토리 사용
        try:
            return tempfile.mkdtemp(prefix="speech_to_text_")
        except Exception as e2:
            if not getattr(sys, 'frozen', False):
                print(f"[ERROR] 시스템 임시 디렉토리 생성도 실패: {e2}")
            return None

def cleanup_temp_files(temp_dir):
    """임시 파일들을 정리합니다."""
    try:
        if temp_dir and os.path.exists(temp_dir):
            # 개별 파일 먼저 삭제
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                    except Exception as e:
                        # exe 파일이 아닌 경우에만 출력
                        if not getattr(sys, 'frozen', False):
                            print(f"[WARNING] 파일 삭제 실패 {file}: {e}")
                
                for dir in dirs:
                    try:
                        dir_path = os.path.join(root, dir)
                        os.rmdir(dir_path)
                    except Exception as e:
                        # exe 파일이 아닌 경우에만 출력
                        if not getattr(sys, 'frozen', False):
                            print(f"[WARNING] 디렉토리 삭제 실패 {dir}: {e}")
            
            # 최종적으로 디렉토리 삭제
            try:
                os.rmdir(temp_dir)
                # exe 파일이 아닌 경우에만 출력
                if not getattr(sys, 'frozen', False):
                    print(f"[INFO] 임시 디렉토리 정리 완료: {temp_dir}")
            except Exception as e:
                # exe 파일이 아닌 경우에만 출력
                if not getattr(sys, 'frozen', False):
                    print(f"[WARNING] 임시 디렉토리 삭제 실패: {e}")
                
    except Exception as e:
        # exe 파일이 아닌 경우에만 출력
        if not getattr(sys, 'frozen', False):
            print(f"[ERROR] 임시 파일 정리 실패: {e}")

def format_duration(seconds):
    """초를 시:분:초 형식으로 변환합니다."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def validate_audio_file(filepath):
    """오디오 파일의 유효성을 검사합니다."""
    if not os.path.exists(filepath):
        return False, "파일이 존재하지 않습니다."
    
    if not os.path.isfile(filepath):
        return False, "유효한 파일이 아닙니다."
    
    file_size_mb = get_file_size_mb(filepath)
    if file_size_mb > 500:  # 500MB 제한
        return False, f"파일 크기가 너무 큽니다. (현재: {file_size_mb:.1f}MB, 최대: 500MB)"
    
    return True, "유효한 파일입니다." 
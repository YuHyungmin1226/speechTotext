# -*- coding: utf-8 -*-
"""
YouTube 유틸리티 함수들 - 음성 텍스트 변환기
"""

import os
import re
import tempfile
import threading
from pathlib import Path
from typing import Optional, Callable, Tuple

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

from PySide6.QtCore import QObject, Signal, QThread

class YouTubeDownloader(QObject):
    """YouTube 비디오 다운로더 클래스"""
    
    # Signals
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(str)  # 다운로드된 파일 경로
    error = Signal(str)
    
    def __init__(self, url: str, download_dir: str):
        super().__init__()
        self.url = url
        self.download_dir = download_dir
        self.downloaded_file = None
        
    def validate_youtube_url(self, url: str) -> Tuple[bool, str]:
        """YouTube URL 유효성 검사"""
        if not url:
            return False, "URL이 비어있습니다."
        
        # YouTube URL 패턴
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                return True, f"https://www.youtube.com/watch?v={video_id}"
        
        return False, "유효한 YouTube URL이 아닙니다."
    
    def progress_hook(self, d):
        """yt-dlp 진행률 콜백"""
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes']:
                percent = int((d['downloaded_bytes'] / d['total_bytes']) * 100)
                self.progress.emit(percent)
                
                speed = d.get('speed', 0)
                if speed:
                    speed_str = f" ({speed/1024/1024:.1f} MB/s)" if speed > 1024*1024 else f" ({speed/1024:.1f} KB/s)"
                else:
                    speed_str = ""
                
                self.status.emit(f"다운로드 중... {percent}%{speed_str}")
        elif d['status'] == 'finished':
            self.downloaded_file = d['filename']
            self.status.emit("다운로드 완료! 오디오 추출 중...")
    
    def download_audio(self):
        """YouTube에서 오디오만 다운로드"""
        if not yt_dlp:
            self.error.emit("yt-dlp 패키지가 설치되지 않았습니다. 'pip install yt-dlp'로 설치해주세요.")
            return
        
        try:
            # URL 유효성 검사
            is_valid, validated_url = self.validate_youtube_url(self.url)
            if not is_valid:
                self.error.emit(validated_url)
                return
            
            self.status.emit("YouTube 정보 가져오는 중...")
            
            # 임시 파일 이름 생성
            temp_filename = os.path.join(self.download_dir, "youtube_audio_%(title)s.%(ext)s")
            
            # yt-dlp 옵션 설정
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
                'outtmpl': temp_filename,
                'progress_hooks': [self.progress_hook],
                'extractaudio': True,
                'audioformat': 'wav',
                'audioquality': '192',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            self.status.emit("다운로드 시작...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 비디오 정보 가져오기
                info = ydl.extract_info(validated_url, download=False)
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                
                # 제목에서 파일명에 사용할 수 없는 문자 제거
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                safe_title = safe_title[:50]  # 파일명 길이 제한
                
                self.status.emit(f"제목: {title}")
                if duration:
                    minutes, seconds = divmod(duration, 60)
                    self.status.emit(f"길이: {int(minutes):02d}:{int(seconds):02d}")
                
                # 실제 다운로드
                ydl.download([validated_url])
                
                # 다운로드된 파일 찾기
                if self.downloaded_file and os.path.exists(self.downloaded_file):
                    # 확장자를 .wav로 변경
                    base_name = os.path.splitext(self.downloaded_file)[0]
                    wav_file = base_name + '.wav'
                    
                    if os.path.exists(wav_file):
                        self.finished.emit(wav_file)
                    else:
                        self.finished.emit(self.downloaded_file)
                else:
                    # 파일을 찾지 못한 경우, 디렉토리에서 가장 최근 파일 찾기
                    files = [f for f in os.listdir(self.download_dir) 
                            if f.startswith('youtube_audio_') and (f.endswith('.wav') or f.endswith('.m4a') or f.endswith('.webm'))]
                    if files:
                        latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(self.download_dir, x)))
                        self.finished.emit(os.path.join(self.download_dir, latest_file))
                    else:
                        self.error.emit("다운로드된 파일을 찾을 수 없습니다.")
                        
        except Exception as e:
            self.error.emit(f"다운로드 중 오류 발생: {str(e)}")


class YouTubeDownloadThread(QThread):
    """YouTube 다운로드를 별도 스레드에서 실행"""
    
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, url: str, download_dir: str):
        super().__init__()
        self.url = url
        self.download_dir = download_dir
        
    def run(self):
        """스레드 실행"""
        downloader = YouTubeDownloader(self.url, self.download_dir)
        
        # Signal 연결
        downloader.progress.connect(self.progress.emit)
        downloader.status.connect(self.status.emit)
        downloader.finished.connect(self.finished.emit)
        downloader.error.connect(self.error.emit)
        
        # 다운로드 실행
        downloader.download_audio()


def check_yt_dlp_installed() -> bool:
    """yt-dlp가 설치되어 있는지 확인"""
    return yt_dlp is not None


def install_yt_dlp():
    """yt-dlp 설치 (권장사항 표시)"""
    return "pip install yt-dlp 명령어로 설치해주세요."
# -*- coding: utf-8 -*-
"""
설정 파일 - 음성 텍스트 변환기
"""

import os
import sys

# 지원하는 오디오 형식
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg']

# 지원하는 비디오 형식
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']

# 언어 설정
LANGUAGES = {
    "한국어": "ko-KR",
    "영어": "en-US",
    "자동 감지": None
}

# FFmpeg 관련 설정
FFMPEG_CONFIG = {
    "windows_url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "chunk_length_ms": 60000,  # 60초 청크
    "sample_rate": 44100,
    "channels": 2,
    "codec": "pcm_s16le"
}

# UI 설정
UI_CONFIG = {
    "window_size": (900, 700),
    "font_family": "Consolas",
    "font_size": 10,
    "temp_dir_prefix": "speech_to_text_"
}

# 파일 저장 설정
SAVE_CONFIG = {
    "auto_save_dir": "speech_to_text",
    "default_encoding": "utf-8",
    "fallback_encoding": "cp949"
}

# 오디오 처리 설정
AUDIO_CONFIG = {
    "max_file_size_mb": 500,  # 최대 파일 크기 (MB)
    "supported_formats": SUPPORTED_AUDIO_FORMATS + SUPPORTED_VIDEO_FORMATS
} 
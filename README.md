# 음성 텍스트 변환기 (Speech to Text Converter)

PyQt5 기반의 음성 텍스트 변환 애플리케이션입니다. 오디오 및 비디오 파일에서 음성을 텍스트로 변환할 수 있습니다.

## 🚀 주요 기능

- **다양한 미디어 형식 지원**: MP3, WAV, M4A, AAC, FLAC, OGG, MP4, AVI, MKV, MOV, WMV
- **Google Speech Recognition API**: 고품질 음성 인식
- **다국어 지원**: 한국어, 영어, 자동 감지
- **FFmpeg 자동 설치**: 필요한 경우 자동으로 FFmpeg 설치
- **오디오 재생**: 변환 전 오디오 미리듣기
- **자동 저장**: 인식 완료 시 자동으로 텍스트 파일 저장
- **진행률 표시**: 실시간 변환 진행 상황 확인

## 📋 시스템 요구사항

- Python 3.7 이상
- Windows, macOS, Linux 지원
- 인터넷 연결 (Google Speech Recognition API 사용)

## 🛠️ 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/YuHyungmin1226/speechTotext.git
cd speechTotext
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 실행
```bash
python speech_to_text.py
```

## 📖 사용 방법

1. **파일 선택**: "파일 찾기" 버튼을 클릭하여 오디오/비디오 파일 선택
2. **재생 확인**: "재생" 버튼으로 오디오 미리듣기 (선택사항)
3. **언어 설정**: 드롭다운에서 인식할 언어 선택
4. **음성 인식 시작**: "음성 인식 시작" 버튼 클릭
5. **결과 확인**: 변환된 텍스트를 결과 창에서 확인
6. **저장**: "텍스트 저장" 버튼으로 파일 저장

## 🔧 기술 스택

- **GUI**: PyQt5
- **음성 인식**: Google Speech Recognition API
- **오디오 처리**: pydub, pygame
- **미디어 처리**: FFmpeg (자동 설치)
- **스레드 처리**: QThread (UI 블로킹 방지)

## 📁 파일 구조

```
speechTotext/
├── speech_to_text.py    # 메인 애플리케이션
├── requirements.txt     # Python 의존성
└── README.md           # 프로젝트 문서
```

## 🎯 주요 개선사항

### PyQt5 기반 GUI
- 현대적이고 직관적인 사용자 인터페이스
- 반응형 레이아웃
- 상태 표시줄 및 진행률 바

### 스레드 안전성
- QThread를 사용한 백그라운드 음성 인식
- UI 블로킹 방지
- 실시간 진행률 업데이트

### 자동화된 설치
- FFmpeg 자동 감지 및 설치
- 플랫폼별 최적화된 설치 과정
- 진행률 표시와 함께 사용자 친화적 설치

### 오류 처리
- 포괄적인 예외 처리
- 사용자 친화적 오류 메시지
- 자동 복구 메커니즘

## 🔍 사용 시나리오

- **회의 녹음 변환**: 회의 녹음 파일을 텍스트로 변환
- **강의 노트 작성**: 강의 영상에서 자동으로 노트 생성
- **음성 메모 변환**: 음성 메모를 텍스트로 변환
- **자막 생성**: 비디오 파일에서 자막 파일 생성
- **접근성 향상**: 청각 장애인을 위한 음성 콘텐츠 텍스트화

## ⚠️ 주의사항

- Google Speech Recognition API는 인터넷 연결이 필요합니다
- 긴 오디오 파일의 경우 처리 시간이 오래 걸릴 수 있습니다
- 음성 품질에 따라 인식 정확도가 달라질 수 있습니다
- FFmpeg 설치 시 관리자 권한이 필요할 수 있습니다

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 문의사항이나 버그 리포트는 [GitHub Issues](https://github.com/YuHyungmin1226/speechTotext/issues)를 통해 제출해 주세요.

---

**개발자**: YuHyungmin1226  
**최종 업데이트**: 2025년 7월 
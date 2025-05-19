#!/bin/bash

# 명령어 인자 확인
if [ $# -eq 0 ]; then
    echo "사용법: $0 [install|start]"
    exit 1
fi

case "$1" in
    "install")
        # Python 버전 확인
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d'.' -f1,2)
        echo "Detected Python version: $PYTHON_VERSION"

        # 가상환경이 없으면 생성
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python3 -m venv venv
        fi

        # 가상환경 활성화
        echo "Activating virtual environment..."
        source venv/bin/activate

        # pip 버전 확인 및 업그레이드
        echo "Checking pip version..."
        if command -v pip3 &> /dev/null; then
            echo "Using pip3..."
            pip3 install --upgrade pip
            PIP_CMD="pip3"
        else
            echo "Using pip..."
            pip install --upgrade pip
            PIP_CMD="pip"
        fi

        # requirements.in 설치
        echo "Installing requirements..."
        $PIP_CMD install -r requirements.in

        echo "Setup completed successfully!"
        ;;
    "start")
        # 가상환경 활성화
        source venv/bin/activate
        
        # 서버 실행
        echo "Starting the server..."
        python -m app.main
        ;;
    *)
        echo "잘못된 명령어입니다. 사용법: $0 [install|start]"
        exit 1
        ;;
esac 
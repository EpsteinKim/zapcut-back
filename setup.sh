#!/bin/bash

# OS 체크
OS_TYPE=$(uname)
echo "Detected OS: $OS_TYPE"

# Ubuntu 체크
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "$ID" != "ubuntu" ]; then
        echo "이 스크립트는 Ubuntu에서만 실행 가능합니다."
        echo "현재 OS: $ID"
        exit 1
    fi
else
    if [ "$OS_TYPE" != "Darwin" ]; then
        echo "이 스크립트는 Ubuntu 또는 macOS에서만 실행 가능합니다."
        echo "현재 OS: $OS_TYPE"
        exit 1
    fi
fi

# 함수 정의
activate_venv() {
    echo "Activating virtual environment..."
    source venv/bin/activate
}

check_and_kill_port() {
    local PORT=$1
    if [ "$OS_TYPE" = "Darwin" ]; then
        if lsof -i :$PORT > /dev/null 2>&1; then
            echo "포트 $PORT가 이미 사용 중입니다. 프로세스를 종료합니다..."
            lsof -ti :$PORT | xargs kill -9
            echo "이전 프로세스가 종료되었습니다."
        fi
    else
        if netstat -tuln | grep ":$PORT " > /dev/null 2>&1; then
            echo "포트 $PORT가 이미 사용 중입니다. 프로세스를 종료합니다..."
            fuser -k $PORT/tcp
            echo "이전 프로세스가 종료되었습니다."
        fi
    fi
}

start_server() {
    local DevFlag=$1
    echo "Starting the server..."
    if [ "$DevFlag" = "--dev" ]; then
        uvicorn app.main:app --reload --workers 1
    else
        # CPU 코어 수 확인 및 worker 수 계산
        CPU_CORES=$(python3 -c "import multiprocessing; print(multiprocessing.cpu_count())")
        WORKERS=$((CPU_CORES * 2 + 1))
        echo "CPU 코어 수: $CPU_CORES, Worker 수: $WORKERS"
        uvicorn app.main:app --workers $WORKERS
    fi
}

# macOS 전용 체크
if [ "$OS_TYPE" = "Darwin" ]; then
    # Xcode Command Line Tools 체크
    if ! xcode-select -p &> /dev/null; then
        echo "Xcode Command Line Tools가 설치되어 있지 않습니다."
        echo "설치를 시작합니다..."
        xcode-select --install
        echo "Xcode Command Line Tools 설치가 완료되면 스크립트를 다시 실행해주세요."
        exit 1
    fi
fi

# Ubuntu/macOS 공통: Python 3.12 설치 확인
if ! command -v python3.12 &> /dev/null; then
    echo "Python 3.12 is not installed. Installing..."
    
    if [ "$OS_TYPE" = "Darwin" ]; then
        # macOS용 설치
        if ! command -v brew &> /dev/null; then
            echo "Homebrew is not installed. Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python@3.12
    elif [ "$ID" = "ubuntu" ]; then
        # Ubuntu용 설치
        if ! command -v add-apt-repository &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y software-properties-common
        fi
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt-get update
        sudo apt-get install -y python3.12 python3.12-venv
    fi
    echo "Python 3.12 has been installed successfully."
fi

# 명령어 인자 확인
if [ $# -eq 0 ]; then
    echo "사용법: $0 [install|start|dev]"
    exit 1
fi

case "$1" in
    "install")
        # Python 버전 확인
        PYTHON_VERSION=$(python3.12 --version 2>&1 | awk '{print $2}')
        echo "Detected Python version: $PYTHON_VERSION"

        # 가상환경이 없으면 생성
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python3.12 -m venv venv
        fi

        # 가상환경 활성화
        activate_venv

        # pip 업그레이드
        echo "Upgrading pip..."
        python3.12 -m pip install --upgrade pip

        # pip-tools 설치
        echo "Installing pip-tools..."
        python3.12 -m pip install pip-tools

        # requirements.txt 생성
        echo "Generating requirements.txt..."
        pip-compile requirements.in

        # requirements.txt로 패키지 설치
        echo "Installing packages from requirements.txt..."
        pip-sync requirements.txt

        echo "Setup completed successfully!"
        ;;
    "start")
        activate_venv
        check_and_kill_port 8000
        start_server
        ;;
    "dev")
        activate_venv
        check_and_kill_port 8000
        start_server --dev
        ;;
    *)
        echo "잘못된 명령어입니다. 사용법: $0 [install|start|dev|prod]"
        exit 1
        ;;
esac 
#!/bin/bash

# OS 체크
OS_TYPE=$(uname)
echo "Detected OS: $OS_TYPE"
export PYTHONDONTWRITEBYTECODE=1
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

    # Ctrl+C 시그널 핸들러 설정
    trap 'echo "\n서버들을 강제 종료합니다..."; pkill -f "uvicorn.*app.server.model_server:app"; pkill -f "uvicorn.*app.main:app"; exit 0' SIGINT

    if [ "$DevFlag" = "--dev" ]; then
        echo "메인 서버를 시작합니다..."
        if ! PYTHONWARNINGS="ignore::SyntaxWarning" uvicorn app.main:app --reload --workers 10; then
            echo "메인 서버 실행 중 오류가 발생했습니다."
            exit 1
        fi
    else
        # CPU 코어 수 확인 및 worker 수 계산
        CPU_CORES=$(python3 -c "import multiprocessing; print(multiprocessing.cpu_count())")
        WORKERS=$((CPU_CORES * 2 + 1))
        echo "CPU 코어 수: $CPU_CORES, Worker 수: $WORKERS"
        
        echo "메인 서버를 시작합니다..."
        if ! PYTHONWARNINGS="ignore::SyntaxWarning" uvicorn app.main:app --workers $WORKERS; then
            echo "메인 서버 실행 중 오류가 발생했습니다."
            exit 1
        fi
    fi
}

install_packages() {
    # 가상환경 활성화
    activate_venv
    
    # 모든 패키지 한 번에 설치
    echo "패키지 설치 중..."
    if ! pip install "$@"; then
        echo "패키지 설치 중 오류가 발생했습니다."
        return 1
    fi
    
    # 설치된 패키지들의 버전 정보를 requirements.in에 추가
    for package in "$@"; do
        # extras가 있는 패키지 처리 (예: package[extra])
        base_package_name=$(echo "$package" | sed -E 's/\[.*\]//g')
        extras=$(echo "$package" | grep -o '\[.*\]' || echo "")
        
        # 패키지 이름과 버전 분리
        package_name=$(echo "$base_package_name" | cut -d'=' -f1)
        requested_version=$(echo "$base_package_name" | cut -d'=' -f2)
        installed_version=$(pip show "$package_name" | grep "^Version:" | awk '{print $2}')
        
        if [ -z "$installed_version" ]; then
            echo "경고: $package_name 패키지의 버전 정보를 가져올 수 없습니다."
            continue
        fi
        
        # requirements.in에 추가 (중복 방지)
        if ! grep -q "^$package_name==" requirements.in; then
            # 패키지가 없으면 추가 (extras 포함)
            if [ -n "$extras" ]; then
                echo -e "\n$package_name$extras==$installed_version" >> requirements.in
            else
                echo -e "\n$package_name==$installed_version" >> requirements.in
            fi
        elif [ -n "$requested_version" ]; then
            # 요청된 버전이 있고, 현재 설치된 버전과 다르면 업데이트
            if [ "$requested_version" != "$installed_version" ]; then
                if [ -n "$extras" ]; then
                    sed -i.bak "s/^$package_name==.*/$package_name$extras==$installed_version/" requirements.in
                else
                    sed -i.bak "s/^$package_name==.*/$package_name==$installed_version/" requirements.in
                fi
                rm -f requirements.in.bak
            fi
        fi
    done
    
    # 연속된 개행을 하나로 줄이기
    if [ -f requirements.in ]; then
        sed -i.bak ':a;N;$!ba;s/\n\n\+/\n/g' requirements.in
        rm -f requirements.in.bak
    fi
    
    # requirements.txt 업데이트
    echo "requirements.txt 업데이트 중..."
    if ! pip-compile requirements.in; then
        echo "requirements.txt 생성 중 오류가 발생했습니다."
        return 1
    fi
    
    if ! pip-sync requirements.txt; then
        echo "패키지 동기화 중 오류가 발생했습니다."
        return 1
    fi
    
    echo "모든 패키지가 성공적으로 설치되었습니다."
    return 0
}

uninstall_packages() {
    # 가상환경 활성화
    activate_venv
    
    # 모든 패키지 한 번에 제거
    echo "패키지 제거 중..."
    if ! pip uninstall -y "$@"; then
        echo "패키지 제거 중 오류가 발생했습니다."
        return 1
    fi
    
    # requirements.in에서 패키지 제거
    for package in "$@"; do
        # 패키지 이름 추출
        package_name=$(echo "$package" | cut -d'=' -f1)
        
        # requirements.in에서 패키지 제거
        if [ -f requirements.in ]; then
            sed -i.bak "/^$package_name==/d" requirements.in
            rm -f requirements.in.bak
        fi
    done
    
    # 연속된 개행을 하나로 줄이기
    if [ -f requirements.in ]; then
        sed -i.bak ':a;N;$!ba;s/\n\n\+/\n/g' requirements.in
        rm -f requirements.in.bak
    fi
    
    # requirements.txt 업데이트
    echo "requirements.txt 업데이트 중..."
    if ! pip-compile requirements.in; then
        echo "requirements.txt 생성 중 오류가 발생했습니다."
        return 1
    fi
    
    if ! pip-sync requirements.txt; then
        echo "패키지 동기화 중 오류가 발생했습니다."
        return 1
    fi
    
    echo "모든 패키지가 성공적으로 제거되었습니다."
    return 0
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
    echo "사용법: $0 [install|uninstall|start|dev]"
    exit 1
fi

case "$1" in
    "install")
        if [ -z "$2" ]; then
            # 기존 설치 로직
            PYTHON_VERSION=$(python3.12 --version 2>&1 | awk '{print $2}')
            echo "Detected Python version: $PYTHON_VERSION"

            if [ ! -d "venv" ]; then
                echo "Creating virtual environment..."
                python3.12 -m venv venv
            fi

            activate_venv

            echo "Upgrading pip..."
            python3.12 -m pip install --upgrade pip

            echo "Installing pip-tools..."
            python3.12 -m pip install pip-tools

            echo "Generating requirements.txt..."
            pip-compile requirements.in

            echo "Installing packages from requirements.txt..."
            pip-sync requirements.txt

            echo "Setup completed successfully!"
        else
            # 모든 패키지 한 번에 설치
            shift  # 첫 번째 인자(install) 제거
            install_packages "$@"
        fi
        ;;
    "uninstall")
        if [ -z "$2" ]; then
            echo "제거할 패키지를 지정해주세요."
            echo "사용법: $0 uninstall package1 [package2 ...]"
            exit 1
        else
            # 모든 패키지 한 번에 제거
            shift  # 첫 번째 인자(uninstall) 제거
            uninstall_packages "$@"
        fi
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
        echo "잘못된 명령어입니다. 사용법: $0 [install|uninstall|start|dev|prod]"
        exit 1
        ;;
esac 
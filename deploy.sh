init() {
    echo "🚀 Setting up Ubuntu EC2 remotely..."
    
    # 원격으로 설치 스크립트 실행 ( 등록 되어 있어야 함 /etc/hosts )
    ssh -q root@zapcut << 'EOF'
        export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1
        echo "🔄 Updating system..."
        sudo apt update -y
        sudo apt upgrade -y -o Dpkg::Options::="--force-confold"
        
        # Docker 설치 확인
        if command -v docker >/dev/null 2>&1; then
            echo "✅ Docker가 이미 설치되어 있습니다."
            docker --version
        else
            echo "🐳 Installing Docker..."
            sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
            
            # Docker GPG 키 추가
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            
            # Docker 저장소 추가
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Docker 설치
            sudo apt update -y
            sudo apt install -y docker-ce docker-ce-cli containerd.io -o Dpkg::Options::="--force-confold"
            
            # Docker 서비스 시작
            sudo systemctl start docker
            sudo systemctl enable docker
            
            # 현재 사용자를 docker 그룹에 추가
            sudo usermod -aG docker $USER
            
            echo "✅ Docker 설치 완료!"
        fi
        
        # Docker Compose 설치 확인
        if command -v docker-compose >/dev/null 2>&1; then
            echo "✅ Docker Compose가 이미 설치되어 있습니다."
            docker-compose --version
        else
            echo "🔧 Installing Docker Compose..."
            sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
            echo "✅ Docker Compose 설치 완료!"
        fi
        
        echo "📋 Checking additional tools..."
        
        # Git 확인
        if command -v git >/dev/null 2>&1; then
            echo "✅ Git이 이미 설치되어 있습니다."
        else
            echo "📥 Installing Git..."
            sudo apt install -y git
        fi
        
        # curl 확인
        if command -v curl >/dev/null 2>&1; then
            echo "✅ curl이 이미 설치되어 있습니다."
        else
            echo "📥 Installing curl..."
            sudo apt install -y curl
        fi
        
        # wget 확인
        if command -v wget >/dev/null 2>&1; then
            echo "✅ wget이 이미 설치되어 있습니다."
        else
            echo "📥 Installing wget..."
            sudo apt install -y wget
        fi
        
        # jq 설치 (JSON 파싱용)
        if command -v jq >/dev/null 2>&1; then
            echo "✅ jq가 이미 설치되어 있습니다."
        else
            echo "📥 Installing jq..."
            sudo apt install -y jq
        fi

        echo "✅ Setup completed on EC2!"
EOF
    
    
    # 프로젝트 파일 전송
    echo "📤 Uploading project files..."
    rsync -avz --exclude='venv' --exclude="deploy.sh" --exclude="*.rdb" --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='nginx-logs' --exclude='temp_blue' --exclude='temp_green' ./ root@zapcut:~/zapcut-back/
    
    # 원격으로 프로젝트 설정
    ssh -q root@zapcut << 'EOF'
        cd ~/zapcut-back
        export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1
        
        # .env 파일 확인
        if [ ! -f .env ]; then
            echo "⚠️  .env file not found. Please create it manually."
        fi
        
        # temp 디렉토리 생성
        mkdir -p temp_blue
        mkdir -p temp_green
        mkdir -p nginx-logs


        docker-compose down
        docker-compose up -d --build

        docker cp ./nginx/nginx.conf zapcut-nginx:/etc/nginx/nginx.conf
        docker exec zapcut-nginx nginx -s reload


        echo "🏠 Project setup completed!"
        echo "📂 Project location: ~/zapcut-back"
EOF
}

deploy_api() {
    # 원격 서버의 proxy_pass 설정 가져오기
    echo "📋 원격 proxy_pass 설정 확인 중..."
    REMOTE_PROXY_PASS=$(ssh -q root@zapcut << 'REMOTE_EOF'
        cd ~/zapcut-back
        if [ -f ./nginx/nginx.conf ]; then
            grep "proxy_pass http://zapcut-api-" ./nginx/nginx.conf | sed -E 's/.*proxy_pass http:\/\/zapcut-api-([^;]+);.*/\1/'
        else
            echo "green"  # 기본값
        fi
REMOTE_EOF
    )

    echo "🔍 원격 proxy_pass 설정: zapcut-api-$REMOTE_PROXY_PASS"

    # 값 검증
    if [[ "$REMOTE_PROXY_PASS" != "blue" && "$REMOTE_PROXY_PASS" != "green" ]]; then
    echo "❌  REMOTE_PROXY_PASS 값은 blue | green 만 허용됩니다."
    exit 1
    fi

    awk -v target="$REMOTE_PROXY_PASS" '
    {
    gsub(/proxy_pass http:\/\/zapcut-api-(blue|green);/, "proxy_pass http://zapcut-api-" target ";")
    print
    }' ./nginx/nginx.conf > ./nginx/nginx.conf.tmp && mv ./nginx/nginx.conf.tmp ./nginx/nginx.conf




    # 프로젝트 파일 동기화
    echo "📤 프로젝트 파일 동기화 중..."
    rsync -avz --exclude='venv' --exclude="deploy.sh" --exclude="*.rdb" --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='nginx-logs' --exclude='temp_blue' --exclude='temp_green' ./ root@zapcut:~/zapcut-back/

    ssh -q root@zapcut << 'DEPLOY_EOF'
        cd ~/zapcut-back
        export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1
        export DEPLOYMENT_DATE=$(TZ=Asia/Seoul date +'%Y-%m-%d %H:%M:%S')

        # 프로젝트 디렉토리로 이동
        cd ~/zapcut-back

        PRODUCTION_ENV=$(grep "proxy_pass http://zapcut-api-" ./nginx/nginx.conf | sed -E 's/.*proxy_pass http:\/\/zapcut-api-([^;]+);.*/\1/')
        if [ -z "$PRODUCTION_ENV" ]; then
            echo "⚠️  ./nginx/nginx.conf에서 zapcut-api-<env> 패턴을 찾지 못했습니다."
            PRODUCTION_ENV="green"  # 기본값 설정
        fi
        
        echo "✅ 현재 환경: $PRODUCTION_ENV"
        
        # 반대 환경으로 배포
        if [ "$PRODUCTION_ENV" = "blue" ]; then
            STAGE_ENV="green"
        else
            STAGE_ENV="blue"
        fi

        docker-compose stop zapcut-api-$STAGE_ENV > /dev/null 2>&1
        docker-compose rm -f zapcut-api-$STAGE_ENV > /dev/null 2>&1

        echo "스테이징 환경($STAGE_ENV) 배포 중..."
        if ! docker-compose up -d --build zapcut-api-$STAGE_ENV; then
            echo "❌ $STAGE_ENV 환경 시작 실패"
            exit 1
        fi

        # 헬스체크 상태 확인
        echo "🔍 헬스체크 상태 확인 중..."
        for i in {1..12}; do  # 최대 1분 대기 (12 * 5초)
            HEALTH_STATUS=$(docker inspect zapcut-api-$STAGE_ENV --format='{{.State.Health.Status}}' 2>/dev/null)
            
            if [ "$HEALTH_STATUS" = "healthy" ]; then
                echo "✅ $STAGE_ENV 환경이 정상입니다! (헬스체크 통과)"
                break
            elif [ "$HEALTH_STATUS" = "unhealthy" ]; then
                echo "❌ $STAGE_ENV 환경이 비정상입니다! (헬스체크 실패)"
                echo "🔍 헬스체크 로그:"
                docker inspect zapcut-api-$STAGE_ENV --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
                echo "🔄 롤백 중..."
                docker-compose stop zapcut-api-$STAGE_ENV
                docker-compose rm -f zapcut-api-$STAGE_ENV
                exit 1
            else
                echo "⏳ 헬스체크 대기 중... (시도 $i/12) - 상태: $HEALTH_STATUS"
                sleep 5
            fi
            
            if [ $i -eq 12 ]; then
                echo "❌ 헬스체크 타임아웃. 롤백 중..."
                docker-compose stop zapcut-api-$STAGE_ENV
                docker-compose rm -f zapcut-api-$STAGE_ENV
                exit 1
            fi
        done

        # Nginx 시작 (없으면)
        if ! docker ps --format "table {{.Names}}" | grep -q "zapcut-nginx"; then
            echo "🌐 Nginx 시작..."
            docker-compose up -d nginx > /dev/null 2>&1
            sleep 3
        fi

        AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
        AVAILABLE_SPACE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
        echo "💾 사용 가능한 디스크 공간: ${AVAILABLE_SPACE_GB}GB"
        
        docker image prune -f > /dev/null 2>&1

        echo "배포가 완료되었습니다. change 를 통해 환경을 전환해주세요."

DEPLOY_EOF
}

dev_test() {
    ssh -q root@zapcut << 'EOF'
        cd ~/zapcut-back

        if docker ps --format "table {{.Names}}" | grep -q "zapcut-api-blue"; then
            if [ -f ./nginx/nginx.conf ]; then
                sed -i '/# *upstream zapcut-api-blue {/,/# *}/s/^# *//' ./nginx/nginx.conf
            fi
        else
            if [ -f ./nginx/nginx.conf ]; then
                sed -i '/upstream zapcut-api-blue {/,/}/s/^/# /' ./nginx/nginx.conf
            fi
        fi

        if docker ps --format "table {{.Names}}" | grep -q "zapcut-api-green"; then
            if [ -f ./nginx/nginx.conf ]; then
                sed -i '/# *upstream zapcut-api-green {/,/# *}/s/^# *//' ./nginx/nginx.conf
            fi
        else
            if [ -f ./nginx/nginx.conf ]; then
                sed -i '/upstream zapcut-api-green {/,/}/s/^/# /' ./nginx/nginx.conf
            fi
        fi
EOF
}

check_status() {
    ssh -q root@zapcut << 'EOF'
        cd ~/zapcut-back
        
        PRODUCTION_ENV=$(grep "proxy_pass http://zapcut-api-" ./nginx/nginx.conf | sed -E 's/.*proxy_pass http:\/\/zapcut-api-([^;]+);.*/\1/')
        if [ -z "$PRODUCTION_ENV" ]; then
            echo "⚠️  ./nginx/nginx.conf에서 zapcut-api-<env> 패턴을 찾지 못했습니다."
            exit 1
        fi
        
        if [ "$PRODUCTION_ENV" = "blue" ]; then
            STAGE_ENV="green"
        else
            STAGE_ENV="blue"
        fi

        echo ""
        echo "------------PRODUCTION-------------"
        echo ""
        echo "Environment: $(echo "$PRODUCTION_ENV" | tr '[:lower:]' '[:upper:]')"
        docker exec zapcut-api-$PRODUCTION_ENV printenv | grep -E 'DEPLOYMENT_DATE'
        echo "Health Status: $(docker inspect zapcut-api-$PRODUCTION_ENV --format='{{.State.Health.Status}}' 2>/dev/null)"
        echo ""
        echo "--------------STAGE----------------"
        echo ""
        echo "Environment: $(echo "$STAGE_ENV" | tr '[:lower:]' '[:upper:]')"
        docker exec zapcut-api-$STAGE_ENV printenv | grep -E 'DEPLOYMENT_DATE'
        echo "Health Status: $(docker inspect zapcut-api-$STAGE_ENV --format='{{.State.Health.Status}}' 2>/dev/null)"
        echo ""
        echo "-----------------------------------"
        echo ""
EOF
}

switch_environment() {
    ssh -q root@zapcut << 'EOF'
        cd ~/zapcut-back
        export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1
        export DEPLOYMENT_DATE=$(TZ=Asia/Seoul date +'%Y-%m-%d %H:%M:%S')

        # 컨테이너 내부의 nginx.conf를 서버로 복사하여 동기화
        docker cp zapcut-nginx:/etc/nginx/nginx.conf ./nginx/nginx.conf

        # upstream 주석 처리 관련
        if docker ps --format "table {{.Names}}" | grep -q "zapcut-api-blue"; then
            if [ -f ./nginx/nginx.conf ]; then
                sed -i '/# *upstream zapcut-api-blue {/,/# *}/s/^# *//' ./nginx/nginx.conf
            fi
        else
            if [ -f ./nginx/nginx.conf ]; then
                sed -i '/upstream zapcut-api-blue {/,/}/s/^/# /' ./nginx/nginx.conf
            fi
        fi

        if docker ps --format "table {{.Names}}" | grep -q "zapcut-api-green"; then
            if [ -f ./nginx/nginx.conf ]; then
                sed -i '/# *upstream zapcut-api-green {/,/# *}/s/^# *//' ./nginx/nginx.conf
            fi
        else
            if [ -f ./nginx/nginx.conf ]; then
                sed -i '/upstream zapcut-api-green {/,/}/s/^/# /' ./nginx/nginx.conf
            fi
        fi
        
        PRODUCTION_ENV=$(grep "proxy_pass http://zapcut-api-" ./nginx/nginx.conf | sed -E 's/.*proxy_pass http:\/\/zapcut-api-([^;]+);.*/\1/')
        if [ -z "$PRODUCTION_ENV" ]; then
            echo "⚠️  ./nginx/nginx.conf에서 zapcut-api-<env> 패턴을 찾지 못했습니다."
            exit 1
        fi

        # ./nginx/nginx.conf의 proxy_pass를 새로운 환경으로 변경
        if [ "$PRODUCTION_ENV" = "blue" ]; then
            STAGE_ENV="green"
        else
            STAGE_ENV="blue"
        fi

        echo "🔄 $PRODUCTION_ENV → $STAGE_ENV 환경으로 전환 중..."

        if ! docker ps --format "table {{.Names}}" | grep -q "zapcut-api-$STAGE_ENV"; then
            echo "❌ $STAGE_ENV 환경이 실행 중이지 않습니다."
            exit 1
        fi
        
        # 헬스체크 대기
        echo "⏳ $STAGE_ENV 환경 헬스체크 대기 중..."
        for i in {1..12}; do
            HEALTH_STATUS=$(docker inspect zapcut-api-$STAGE_ENV --format='{{.State.Health.Status}}' 2>/dev/null)
            if [ "$HEALTH_STATUS" = "healthy" ]; then
                echo "✅ $STAGE_ENV 환경이 정상입니다!"
                break
            elif [ "$HEALTH_STATUS" = "unhealthy" ]; then
                echo "❌ $STAGE_ENV 환경이 비정상입니다!"
                echo "🔍 헬스체크 로그:"
                docker inspect zapcut-api-$STAGE_ENV --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
                echo "🔄 롤백 중..."
                exit 1
            else
                echo "⏳ 헬스체크 대기 중... (시도 $i/12) - 상태: $HEALTH_STATUS"
                sleep 5
            fi
            
            if [ $i -eq 12 ]; then
                echo "❌ 헬스체크 타임아웃. 롤백 중..."
                exit 1
            fi
        done

        # proxy_pass 라인을 STAGE_ENV로 변경
        sed -i "s/proxy_pass http:\/\/zapcut-api-[^;]*;/proxy_pass http:\/\/zapcut-api-$STAGE_ENV;/" ./nginx/nginx.conf
        
        # Nginx 설정을 컨테이너에 복사
        echo "Nginx 설정을 컨테이너에 복사 중..."
        docker cp ./nginx/nginx.conf zapcut-nginx:/etc/nginx/nginx.conf

        # Nginx 설정 테스트
        echo "Nginx 설정 테스트 중..."
        if docker exec zapcut-nginx nginx -t 2>/dev/null; then
            echo "✅ Nginx 설정이 유효합니다!"
            
            # Nginx 무중단 리로드
            echo "Nginx 무중단 리로드 중..."
            if docker exec zapcut-nginx nginx -s reload 2>/dev/null; then
                echo "환경 전환이 완료되었습니다! ($PRODUCTION_ENV → $STAGE_ENV)"
                echo "배포 시간: $DEPLOYMENT_DATE"
            else
                echo "❌ Nginx 리로드 실패. 롤백 중..."
                # 롤백: 이전 설정으로 복원
                sed -i "s/proxy_pass http:\/\/zapcut-api-[^;]*;/proxy_pass http:\/\/zapcut-api-$PRODUCTION_ENV;/" ./nginx/nginx.conf
                docker cp ./nginx/nginx.conf zapcut-nginx:/etc/nginx/nginx.conf
                docker exec zapcut-nginx nginx -s reload 2>/dev/null
                exit 1
            fi
        else
            echo "❌ Nginx 설정 오류. 롤백 중..."
            # 롤백: 이전 설정으로 복원
            sed -i "s/proxy_pass http:\/\/zapcut-api-[^;]*;/proxy_pass http:\/\/zapcut-api-$PRODUCTION_ENV;/" ./nginx/nginx.conf
            docker cp ./nginx/nginx.conf zapcut-nginx:/etc/nginx/nginx.conf
            exit 1
        fi
        
EOF
}

logs() {
    if [ -z "$1" ]; then
        echo "❌ 로그를 볼 컨테이너를 지정해주세요."
        echo "사용법: $0 logs {blue|green|nginx|all}"
        echo ""
        echo "예시:"
        echo "  $0 logs blue     # 블루 환경 로그"
        echo "  $0 logs green    # 그린 환경 로그"
        echo "  $0 logs nginx    # Nginx 로그"
        echo "  $0 logs all      # 모든 로그 (새 터미널에서)"
        exit 1
    fi
    
    case $1 in
        blue)
            echo "🔵 블루 환경 로그를 실시간으로 확인합니다... (Ctrl+C로 종료)"
            ssh -q root@zapcut "cd ~/zapcut-back && docker logs -f zapcut-api-blue"
            ;;
        green)
            echo "🟢 그린 환경 로그를 실시간으로 확인합니다... (Ctrl+C로 종료)"
            ssh -q root@zapcut "cd ~/zapcut-back && docker logs -f zapcut-api-green"
            ;;
        nginx)
            echo "🌐 Nginx 로그를 실시간으로 확인합니다... (Ctrl+C로 종료)"
            ssh -q root@zapcut "cd ~/zapcut-back && docker logs -f zapcut-nginx"
            ;;
        redis)
            echo "🔴 Redis 로그를 실시간으로 확인합니다... (Ctrl+C로 종료)"
            ssh -q root@zapcut "cd ~/zapcut-back && docker logs -f zapcut-redis"
            ;;
        *)
            echo "❌ 잘못된 옵션입니다: $1"
            echo "사용 가능한 옵션: blue, green, nginx, redis"
            exit 1
            ;;
    esac
}

stop_api() {
    ssh -q root@zapcut << 'EOF'
        cd ~/zapcut-back

        docker-compose stop zapcut-api-blue

        docker-compose stop zapcut-api-green
EOF
}
stop_nginx() {
    ssh -q root@zapcut << 'EOF'
        cd ~/zapcut-back

        docker-compose stop nginx
EOF
}
start_nginx() {
    ssh -q root@zapcut << 'EOF'
        cd ~/zapcut-back

        docker-compose start nginx
EOF
}
start_api() {
    ssh -q root@zapcut << 'EOF'
        cd ~/zapcut-back

        if docker ps -a --format "table {{.Names}}" | grep -q "zapcut-api-blue"; then
            docker-compose start zapcut-api-blue
        else
            docker-compose up -d zapcut-api-blue
        fi
        
        if docker ps -a --format "table {{.Names}}" | grep -q "zapcut-api-green"; then
            docker-compose start zapcut-api-green
        else
            docker-compose up -d zapcut-api-green
        fi
        
        sleep 20
        
        if docker inspect zapcut-api-blue --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; then
            echo "✅ Blue 환경 정상"
        else
            echo "⚠️  Blue 환경 헬스체크 실패"
        fi
        
        if docker inspect zapcut-api-green --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; then
            echo "✅ Green 환경 정상"
        else
            echo "⚠️  Green 환경 헬스체크 실패"
        fi
EOF
}

case $1 in
    api)
        deploy_api
        ;;
    init)
        init
        ;;
    check|status)
        check_status
        ;;
    switch|change)
        switch_environment
        ;;
    stop)
        stop_api
        ;;
    start)
        start_api
        ;;
    test)
        dev_test
        ;;
    logs)
        logs $2
        ;;
    nginx)
        if [ "$2" = "stop" ]; then
            stop_nginx
        elif [ "$2" = "start" ]; then
            start_nginx
        fi
        ;;
    redis)
        docker exec -it zapcut-redis redis-cli
        ;;
    *)
        echo "Usage: $0 {api|init|check|switch|stop|start|logs}"
        echo ""
        echo "명령어 설명:"
        echo "  api      - 블루그린 배포"
        echo "  init     - EC2 초기 설정"
        echo "  check    - 현재 상태 확인"
        echo "  switch   - 환경 전환"
        echo "  stop     - API 서비스 중지"
        echo "  start    - API 서비스 시작"
        echo "  nginx    - Nginx 서비스 (start|stop)"
        echo "  logs     - 실시간 로그 확인 (blue|green|nginx|redis|all)"
        exit 1
        ;;
esac
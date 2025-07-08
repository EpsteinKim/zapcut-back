#!/bin/bash

# 올인원 FastAPI 블루그린 배포 스크립트
set -e

show_usage() {
    echo "🚀 ZAPCUT FastAPI 블루그린 배포 스크립트"
    echo "======================================="
    echo ""
    echo "사용법: $0 [명령어] [옵션]"
    echo ""
    echo "명령어:"
    echo "  deploy              - 반대 환경으로 배포 (기본값)"
    echo "  status|check        - 현재 상태 및 배포 정보 확인"
    echo "  switch              - 환경 전환 및 우선순위 변경"
    echo "  stop                - 서비스 중지"
    echo "  restart             - 서비스 재시작"
    echo "  setup               - EC2 환경 설정"
    echo ""
    echo "예시:"
    echo "  $0                    # 배포 (기본값)"
    echo "  $0 deploy             # 반대 환경으로 배포"
    echo "  $0 status             # 상태 및 배포 정보 확인"
    echo "  $0 switch             # 현재 주환경의 반대로 전환"
    echo "  $0 stop               # 모든 서비스 중지"
    echo "  $0 restart            # 서비스 재시작"
    echo "  $0 setup              # EC2 설정 (중지하고 사용)"
    echo "  $0 debug              # 디버깅 정보 출력"
}

# 디버깅 함수
debug_info() {
    echo "🔍 디버깅 정보 수집 중..."
    
    ssh -q -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o UpdateHostKeys=no root@zapcut << 'EOF'
        cd ~/zapcut-back
        export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1
        
        echo "🔍 === 디버깅 정보 ==="
        echo ""
        
        echo "📦 Docker 컨테이너 상태:"
        docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        
        echo "📋 현재 nginx.conf 업스트림 설정:"
        grep -A 5 "upstream zapcut_backend" nginx.conf
        echo ""
        
        echo "🏥 컨테이너 헬스체크:"
        echo "  - 블루 (8000): $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "연결 실패")"
        echo "  - 그린 (8001): $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "연결 실패")"
        echo "  - Nginx (8800): $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8800/health 2>/dev/null || echo "연결 실패")"
        echo ""
        
        echo "🌐 네트워크 포트 상태:"
        netstat -tlnp | grep -E ":(8000|8001|8800)" || echo "포트 정보 없음"
        echo ""
        
        echo "📝 최근 Docker 로그 (마지막 20줄):"
        echo "--- Nginx 로그 ---"
        docker logs --tail 5 zapcut-nginx 2>/dev/null || echo "Nginx 컨테이너 없음"
        echo ""
        echo "--- Blue 로그 ---"
        docker logs --tail 5 zapcut-api-blue 2>/dev/null || echo "Blue 컨테이너 없음"
        echo ""
        echo "--- Green 로그 ---"
        docker logs --tail 5 zapcut-api-green 2>/dev/null || echo "Green 컨테이너 없음"
        echo ""
        
        echo "🔧 Nginx 설정 테스트:"
        docker exec zapcut-nginx nginx -t 2>&1 || echo "Nginx 컨테이너에서 테스트 실패"
        echo ""
        
        echo "📂 파일 시스템 상태:"
        echo "  - nginx.conf 존재: $([ -f nginx.conf ] && echo "✅" || echo "❌")"
        echo "  - .env 존재: $([ -f .env ] && echo "✅" || echo "❌")"
        echo "  - temp 디렉토리: $([ -d temp ] && echo "✅" || echo "❌")"
        
EOF
}

# Nginx 업스트림 전환 함수
switch_nginx_upstream() {
    local NEW_ENV=$1
    local NEW_PORT=$2
    
    echo "🔧 Nginx 업스트림 전환 중..."
    
    # nginx.conf 백업
    cp nginx.conf nginx.conf.bak
    
    # 현재 설정 확인
    echo "📋 현재 nginx.conf 업스트림 설정:"
    grep -A 3 "upstream zapcut_backend" nginx.conf
    
    # 업스트림 설정 변경 (zapcut_backend 블록 내에서만 변경)
    if [ "$NEW_ENV" = "blue" ]; then
        # 블루 환경 활성화: 8000 활성화, 8001 비활성화
        sed -i '/upstream zapcut_backend {/,/}/ {
            s/^[[:space:]]*# server 127\.0\.0\.1:8000;.*/        server 127.0.0.1:8000;  # 블루 환경/
            s/^[[:space:]]*server 127\.0\.0\.1:8001;.*/        # server 127.0.0.1:8001;  # 그린 환경 (주석 처리)/
        }' nginx.conf
    else
        # 그린 환경 활성화: 8001 활성화, 8000 비활성화
        sed -i '/upstream zapcut_backend {/,/}/ {
            s/^[[:space:]]*# server 127\.0\.0\.1:8001;.*/        server 127.0.0.1:8001;  # 그린 환경/
            s/^[[:space:]]*server 127\.0\.0\.1:8000;.*/        # server 127.0.0.1:8000;  # 블루 환경 (주석 처리)/
        }' nginx.conf
    fi
    
    # 변경 후 설정 확인
    echo "📋 변경 후 nginx.conf 업스트림 설정:"
    grep -A 3 "upstream zapcut_backend" nginx.conf
    
    # Nginx 설정 테스트
    echo "🧪 Nginx 설정 테스트 중..."
    if docker exec zapcut-nginx nginx -t 2>&1; then
        echo "✅ Nginx 설정이 유효합니다!"
        
        # Nginx 리로드
        echo "🔄 Nginx 리로드 중..."
        docker exec zapcut-nginx nginx -s reload
        
        if [ $? -eq 0 ]; then
            echo "✅ Nginx 업스트림이 $NEW_ENV 환경으로 전환되었습니다!"
            return 0
        else
            echo "❌ Nginx 리로드 실패"
            # 백업 복원
            cp nginx.conf.bak nginx.conf
            return 1
        fi
    else
        echo "❌ Nginx 설정 오류"
        echo "🔍 Nginx 설정 테스트 결과:"
        docker exec zapcut-nginx nginx -t
        # 백업 복원
        cp nginx.conf.bak nginx.conf
        return 1
    fi
}

switch_environment() {
    local TARGET_ENV=$1
    
    # TARGET_ENV가 없으면 현재 주 환경의 반대로 설정
    if [ -z "$TARGET_ENV" ]; then
        echo "🔍 현재 우선순위 환경 확인 중..."
        
        # 원격 서버에서 현재 우선순위 확인
        CURRENT_PRIMARY=$(ssh -q -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o UpdateHostKeys=no root@zapcut << 'EOF'
            cd ~/zapcut-back
            export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1
            if [ -f nginx.conf ]; then
                if grep -q 'set \$primary_backend "zapcut-api-blue:8000"' nginx.conf; then
                    echo "blue"
                elif grep -q 'set \$primary_backend "zapcut-api-green:8000"' nginx.conf; then
                    echo "green"
                else
                    echo "blue"  # 기본값
                fi
            else
                echo "blue"  # nginx.conf가 없으면 기본값
            fi
EOF
        )
        
        # 반대 환경으로 설정
        if [ "$CURRENT_PRIMARY" = "blue" ]; then
            TARGET_ENV="green"
            echo "📋 현재 주 환경: blue → green으로 전환"
        else
            TARGET_ENV="blue"
            echo "📋 현재 주 환경: green → blue로 전환"
        fi
    else
        if [ "$TARGET_ENV" != "blue" ] && [ "$TARGET_ENV" != "green" ]; then
            echo "❌ 잘못된 환경입니다. 'blue' 또는 'green'을 입력하세요."
            exit 1
        fi
    fi
    
    echo "🔄 $TARGET_ENV 환경으로 전환..."
    
    # 원격 서버에서 환경 스위치 실행
    ssh -q -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o UpdateHostKeys=no root@zapcut << EOF
        cd ~/zapcut-back
        export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1
        
        # 현재 활성 환경 확인
        if docker ps --format "table {{.Names}}" | grep -q "zapcut-api-blue"; then
            CURRENT_ENV="blue"
        elif docker ps --format "table {{.Names}}" | grep -q "zapcut-api-green"; then
            CURRENT_ENV="green"
        else
            CURRENT_ENV="none"
        fi
        
        # 대상 환경이 실행 중인지 확인
        if ! docker ps --format "table {{.Names}}" | grep -q "zapcut-api-$TARGET_ENV"; then
            echo "🚀 $TARGET_ENV 환경 시작..."
            
            # 환경 변수 설정
            ENVIRONMENT="$ENVIRONMENT"
            echo "🔄 기존 $TARGET_ENV 환경을 다시 활성화합니다 (배포 날짜 유지)"
            
            docker-compose up -d zapcut-api-$TARGET_ENV > /dev/null 2>&1
            
            # 헬스체크 대기
            echo "⏳ 헬스체크 대기..."
            sleep 10
            
            if [ "$TARGET_ENV" = "blue" ]; then
                CHECK_PORT=8000
            else
                CHECK_PORT=8001
            fi
            
            # 헬스체크 재시도
            for i in {1..10}; do
                if curl -s http://localhost:\$CHECK_PORT/health > /dev/null 2>&1; then
                    echo "✅ $TARGET_ENV 환경 시작 완료"
                    break
                fi
                sleep 5
                
                if [ \$i -eq 10 ]; then
                    echo "❌ $TARGET_ENV 환경 시작 실패"
                    exit 1
                fi
            done
        fi
        
        # Nginx 우선순위 변경
        echo "🔧 Nginx 우선순위를 $TARGET_ENV 환경으로 변경 중..."
        
        # nginx.conf 백업
        cp nginx.conf nginx.conf.bak
        
        # 활성 환경에 따라 우선순위 변경
        if [ "$TARGET_ENV" = "blue" ]; then
            # 블루 우선, 그린 fallback
            sed -i 's/set \$primary_backend "zapcut-api-[^"]*"/set \$primary_backend "zapcut-api-blue:8000"/g' nginx.conf
            sed -i 's/set \$fallback_backend "zapcut-api-[^"]*"/set \$fallback_backend "zapcut-api-green:8000"/g' nginx.conf
            echo "📋 설정: 블루 우선 → 그린 fallback"
        else
            # 그린 우선, 블루 fallback
            sed -i 's/set \$primary_backend "zapcut-api-[^"]*"/set \$primary_backend "zapcut-api-green:8000"/g' nginx.conf
            sed -i 's/set \$fallback_backend "zapcut-api-[^"]*"/set \$fallback_backend "zapcut-api-blue:8000"/g' nginx.conf
            echo "📋 설정: 그린 우선 → 블루 fallback"
        fi
        
        # Nginx 설정 테스트 및 리로드
        if docker exec zapcut-nginx nginx -t > /dev/null 2>&1; then
            if docker exec zapcut-nginx nginx -s reload > /dev/null 2>&1; then
                echo "✅ $TARGET_ENV 환경으로 우선순위 전환 완료!"
            else
                echo "❌ Nginx 리로드 실패"
                cp nginx.conf.bak nginx.conf
                exit 1
            fi
        else
            echo "❌ Nginx 설정 오류"
            cp nginx.conf.bak nginx.conf
            exit 1
        fi
EOF
    
    if [ $? -eq 0 ]; then
        show_status
    else
        echo "❌ 환경 전환 실패"
        exit 1
    fi
}

show_status() {
    echo "🔍 원격 서버 상태 확인 중..."
    
    ssh -q -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o UpdateHostKeys=no root@zapcut << 'EOF'
        # Ubuntu 업데이트 메시지 숨기기
        export DEBIAN_FRONTEND=noninteractive
        touch ~/.hushlogin 2>/dev/null || true

        cd ~/zapcut-back
        # 컨테이너 상태 확인
        BLUE_RUNNING=false
        GREEN_RUNNING=false
        NGINX_RUNNING=false
        
        if docker ps --format "table {{.Names}}" | grep -q "zapcut-api-blue"; then
            BLUE_RUNNING=true
        fi
        
        if docker ps --format "table {{.Names}}" | grep -q "zapcut-api-green"; then
            GREEN_RUNNING=true
        fi
        
        if docker ps --format "table {{.Names}}" | grep -q "zapcut-nginx"; then
            NGINX_RUNNING=true
        fi
        
        
        # 현재 활성 환경 확인 (both 제거)
        if [ "$BLUE_RUNNING" = true ] && [ "$GREEN_RUNNING" = false ]; then
            ACTIVE_ENV="blue"
        elif [ "$GREEN_RUNNING" = true ] && [ "$BLUE_RUNNING" = false ]; then
            ACTIVE_ENV="green"
        elif [ "$BLUE_RUNNING" = true ] && [ "$GREEN_RUNNING" = true ]; then
            # 두 환경이 모두 실행 중일 때는 nginx.conf의 primary_backend로 우선순위 판단
            if [ -f nginx.conf ]; then
                if grep -q 'set \$primary_backend "zapcut-api-blue:8000"' nginx.conf; then
                    ACTIVE_ENV="blue"
                elif grep -q 'set \$primary_backend "zapcut-api-green:8000"' nginx.conf; then
                    ACTIVE_ENV="green"
                else
                    ACTIVE_ENV="blue"  # 기본값
                fi
            else
                ACTIVE_ENV="blue"  # nginx.conf가 없으면 기본값
            fi
        else
            ACTIVE_ENV="none"
        fi
        
        # nginx.conf에서 현재 우선순위 환경 확인
        if [ -f nginx.conf ]; then
            if grep -q 'set \$primary_backend "zapcut-api-blue:8000"' nginx.conf; then
                PRIMARY_ENV="blue"
            elif grep -q 'set \$primary_backend "zapcut-api-green:8000"' nginx.conf; then
                PRIMARY_ENV="green"
            else
                PRIMARY_ENV="blue"  # 기본값
            fi
        else
            echo "⚠️  nginx.conf 파일이 없습니다. 기본값으로 설정합니다."
            PRIMARY_ENV="blue"  # 기본값
        fi

        # Nginx 상태 확인
        if [ "$NGINX_RUNNING" = true ] && curl -s http://localhost:8800/health > /dev/null 2>&1; then
            NGINX_HEALTH="healthy"
        else
            NGINX_HEALTH="unhealthy"
        fi

        # 블루 환경 정보 수집
        if [ "$BLUE_RUNNING" = true ]; then
            BLUE_STATUS="running"
            if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                BLUE_HEALTH="healthy"
            else
                BLUE_HEALTH="unhealthy"
            fi
        else
            BLUE_STATUS="stopped"
            BLUE_HEALTH="stopped"
        fi
        
        # 블루 환경 정보 수집
        if [ "$BLUE_RUNNING" = true ]; then
            BLUE_STATUS="running"
            if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                BLUE_HEALTH="healthy"
            else
                BLUE_HEALTH="unhealthy"
            fi
            
            # 블루 컨테이너에서 배포 날짜 환경변수 가져오기
            BLUE_DEPLOYMENT_DATE=$(docker exec zapcut-api-blue printenv DEPLOYMENT_DATE 2>/dev/null || echo "Unknown")
        else
            BLUE_STATUS="stopped"
            BLUE_HEALTH="stopped"
            BLUE_DEPLOYMENT_DATE="Unknown"
        fi

        # 그린 환경 정보 수집
        if [ "$GREEN_RUNNING" = true ]; then
            GREEN_STATUS="running"
            if curl -s http://localhost:8001/health > /dev/null 2>&1; then
                GREEN_HEALTH="healthy"
            else
                GREEN_HEALTH="unhealthy"
            fi
            
            # 그린 컨테이너에서 배포 날짜 환경변수 가져오기
            GREEN_DEPLOYMENT_DATE=$(docker exec zapcut-api-green printenv DEPLOYMENT_DATE 2>/dev/null || echo "Unknown")
        else
            GREEN_STATUS="stopped"
            GREEN_HEALTH="stopped"
            GREEN_DEPLOYMENT_DATE="Unknown"
        fi


        echo ""
        echo "🎯 현재 상태 요약:"
        echo "=================="
        echo "📊 활성 환경: $ACTIVE_ENV"
        echo "🔄 Nginx 우선순위: $PRIMARY_ENV ($([ "$PRIMARY_ENV" = "blue" ] && echo "블루 → 그린" || echo "그린 → 블루") fallback)"
        echo "🌐 Nginx: $([ "$NGINX_RUNNING" = true ] && echo "✅ 실행 중" || echo "❌ 중지됨")"
        echo ""
        echo "🔵 Blue 환경 (포트 8000):"
        echo "   상태: $([ "$BLUE_RUNNING" = true ] && echo "✅ 실행 중" || echo "❌ 중지됨")"
        echo "   헬스: $([ "$BLUE_HEALTH" = "healthy" ] && echo "✅ 정상" || echo "❌ 비정상")"
        echo "   우선순위: $([ "$PRIMARY_ENV" = "blue" ] && echo "⭐ 1순위" || echo "🔄 2순위")"
        echo "   배포일: $BLUE_DEPLOYMENT_DATE"
        echo ""
        echo "🟢 Green 환경 (포트 8001):"
        echo "   상태: $([ "$GREEN_RUNNING" = true ] && echo "✅ 실행 중" || echo "❌ 중지됨")"
        echo "   헬스: $([ "$GREEN_HEALTH" = "healthy" ] && echo "✅ 정상" || echo "❌ 비정상")"
        echo "   우선순위: $([ "$PRIMARY_ENV" = "green" ] && echo "⭐ 1순위" || echo "🔄 2순위")"
        echo "   배포일: $GREEN_DEPLOYMENT_DATE"
EOF
}

deploy_service() {
    echo "🚀 배포 시작"
    
    # 프로젝트 파일 업로드
    echo "📤 파일 업로드 중..."
    rsync -avz --exclude='venv' --exclude='.git' --exclude='__pycache__' --progress --exclude='*.pyc' --exclude='temp' --exclude='logs' --exclude='nginx-logs' ./ root@zapcut:~/zapcut-back/

    # 원격 서버에서 배포 실행
    ssh -q -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o UpdateHostKeys=no root@zapcut << 'DEPLOY_EOF'
        cd ~/zapcut-back
        export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1
        
        
        # 배포 정보 설정 (SSH 세션 내에서 직접 설정)
        DEPLOYMENT_DATE=$(date '+%Y-%m-%d %H:%M:%S')
        ENVIRONMENT="production"
        export DEPLOYMENT_DATE
        export ENVIRONMENT
        
        echo "  날짜: $DEPLOYMENT_DATE"
        
        # 현재 우선순위 환경 확인하여 반대 환경으로 배포
        if [ -f nginx.conf ] && grep -q 'set \$primary_backend "zapcut-api-blue:8000"' nginx.conf; then
            CURRENT_PRIMARY="blue"
            NEW_ENV="green"
            NEW_PORT="8001"
            echo "🔄 현재 주 환경: 블루 → 그린 배포"
        elif [ -f nginx.conf ] && grep -q 'set \$primary_backend "zapcut-api-green:8000"' nginx.conf; then
            CURRENT_PRIMARY="green"
            NEW_ENV="blue"
            NEW_PORT="8000"
            echo "🔄 현재 주 환경: 그린 → 블루 배포"
        else
            # nginx.conf에 설정이 없으면 실행 중인 컨테이너 확인
            if docker ps --format "table {{.Names}}" | grep -q "zapcut-api-blue"; then
                CURRENT_PRIMARY="blue"
                NEW_ENV="green"
                NEW_PORT="8001"
                echo "🔄 현재 실행 환경: 블루 → 그린 배포"
            elif docker ps --format "table {{.Names}}" | grep -q "zapcut-api-green"; then
                CURRENT_PRIMARY="green"
                NEW_ENV="blue"
                NEW_PORT="8000"
                echo "🔄 현재 실행 환경: 그린 → 블루 배포"
            else
                CURRENT_PRIMARY="none"
                NEW_ENV="blue"
                NEW_PORT="8000"
                echo "🔄 최초 배포 (블루)"
            fi
        fi
        
        
        # 이미지 빌드
        echo "🔨 빌드 중..."
        if ! docker build -t zapcut-api:latest . > /dev/null 2>&1; then
            echo "❌ 빌드 실패"
            exit 1
        fi
        echo "✅ 빌드 완료"
        
        # Nginx 시작 (없으면)
        if ! docker ps --format "table {{.Names}}" | grep -q "zapcut-nginx"; then
            echo "🌐 Nginx 시작..."
            docker-compose up -d nginx > /dev/null 2>&1
            sleep 3
        fi
        
        # 환경별 배포 날짜 설정 및 파일 저장
        if [ "$NEW_ENV" = "blue" ]; then
            export BLUE_DEPLOYMENT_DATE="$DEPLOYMENT_DATE"
            echo "$DEPLOYMENT_DATE" > .blue_deployment_date
            echo "🔵 블루 환경 배포 날짜: $BLUE_DEPLOYMENT_DATE"
        else
            export GREEN_DEPLOYMENT_DATE="$DEPLOYMENT_DATE"
            echo "$DEPLOYMENT_DATE" > .green_deployment_date
            echo "🟢 그린 환경 배포 날짜: $GREEN_DEPLOYMENT_DATE"
        fi
        
        # 새 환경 시작
        echo "🚀 $NEW_ENV 환경 시작 중 (포트 $NEW_PORT)..."
        if ! docker-compose up -d zapcut-api-$NEW_ENV; then
            echo "❌ $NEW_ENV 환경 시작 실패"
            exit 1
        fi
        
        # 헬스체크
        echo "⏳ 헬스체크 중..."
        for i in {1..30}; do
            if curl -f http://localhost:$NEW_PORT/health > /dev/null 2>&1; then
                echo "✅ $NEW_ENV 환경이 정상입니다!"
                break
            fi
            echo "시도 $i/30..."
            sleep 2
        done
        
        if [ $i -eq 30 ]; then
            echo "❌ 헬스체크 실패. 롤백 중..."
            docker-compose stop zapcut-api-$NEW_ENV
            docker-compose rm -f zapcut-api-$NEW_ENV
            exit 1
        fi
        
        # 성공 메시지
        PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
        
        echo ""
        echo "✅ 배포 완료!"
        echo "🎯 활성: $NEW_ENV (포트 $NEW_PORT)"
        echo ""
        

        echo "🔧 Nginx 우선순위를 $NEW_ENV 환경으로 변경 중..."
        
        # nginx.conf 백업
        cp nginx.conf nginx.conf.bak
        
        # 활성 환경에 따라 우선순위 변경
        if [ "$NEW_ENV" = "blue" ]; then
            # 블루 우선, 그린 fallback
            sed -i 's/set \$primary_backend "zapcut-api-[^"]*"/set \$primary_backend "zapcut-api-blue:8000"/g' nginx.conf
            sed -i 's/set \$fallback_backend "zapcut-api-[^"]*"/set \$fallback_backend "zapcut-api-green:8000"/g' nginx.conf
        else
            # 그린 우선, 블루 fallback
            sed -i 's/set \$primary_backend "zapcut-api-[^"]*"/set \$primary_backend "zapcut-api-green:8000"/g' nginx.conf
            sed -i 's/set \$fallback_backend "zapcut-api-[^"]*"/set \$fallback_backend "zapcut-api-blue:8000"/g' nginx.conf
        fi
        
        # Nginx 설정 테스트 및 리로드
        echo "🔄 Nginx 설정 적용 중..."
        if docker exec zapcut-nginx nginx -t > /dev/null 2>&1; then
            if docker exec zapcut-nginx nginx -s reload 2>&1; then
                echo "✅ Nginx 우선순위가 $NEW_ENV 환경으로 변경되었습니다!"
                NGINX_SUCCESS=true
            else
                echo "❌ Nginx 리로드 실패"
                cp nginx.conf.bak nginx.conf
                NGINX_SUCCESS=false
            fi
        else
            echo "❌ Nginx 설정 오류"
            cp nginx.conf.bak nginx.conf
            NGINX_SUCCESS=false
        fi
        
        if [ "$NGINX_SUCCESS" != true ]; then
            echo "⚠️  Nginx 설정 확인이 필요합니다."
        fi

        # 디스크 공간 확인 후 이미지 정리 (10GB 이하일 때만)
        AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
        AVAILABLE_SPACE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
        
        echo "💾 사용 가능한 디스크 공간: ${AVAILABLE_SPACE_GB}GB"
        
        if [ $AVAILABLE_SPACE_GB -le 10 ]; then
            echo "⚠️  디스크 공간이 부족합니다 (${AVAILABLE_SPACE_GB}GB). 이미지 정리를 시작합니다..."
            docker image prune -f
            echo "🧽 사용하지 않는 Docker 이미지 정리 완료"
        else
            echo "✅ 디스크 공간이 충분합니다 (${AVAILABLE_SPACE_GB}GB). 이미지 정리를 건너뜁니다."
        fi

DEPLOY_EOF
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ 원격 배포가 성공적으로 완료되었습니다!"
    else
        echo ""
        echo "❌ 원격 배포 중 오류가 발생했습니다."
        exit 1
    fi
}

stop_service() {
    echo "🛑 모든 서비스 중지 중..."
    
    ssh -q -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o UpdateHostKeys=no root@zapcut "export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1; cd ~/zapcut-back && docker-compose down"
    
    if [ $? -eq 0 ]; then
        echo "✅ 모든 서비스가 중지되었습니다"
    else
        echo "❌ 서비스 중지 중 오류가 발생했습니다"
    fi
}

restart_service() {
    echo "🚀 블루 환경 시작 중..."
    
    ssh -q -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o UpdateHostKeys=no root@zapcut "export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1; cd ~/zapcut-back && docker-compose up -d nginx zapcut-api-blue"
    
    if [ $? -eq 0 ]; then
        echo "✅ 블루 환경이 시작되었습니다"
        echo "⏳ 시작 대기 중..."
        sleep 5
        show_status
    else
        echo "❌ 서비스 시작 중 오류가 발생했습니다"
    fi
}

setup() {
    echo "🚀 Setting up Ubuntu EC2 remotely..."
    
    # 원격으로 설치 스크립트 실행 ( 등록 되어 있어야 함 /etc/hosts )
    ssh -q -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o UpdateHostKeys=no root@zapcut << 'EOF'
        export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1
        echo "🔄 Updating system..."
        sudo apt update -y
        sudo apt upgrade -y
        
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
            sudo apt install -y docker-ce docker-ce-cli containerd.io
            
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
    
    echo ""
    echo "🚀 Deploying project to EC2..."
    
    # 프로젝트 파일 전송
    echo "📤 Uploading project files..."
    rsync -avz --exclude='venv' --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='nginx-logs' ./ root@zapcut:~/zapcut-back/
    
    # 원격으로 프로젝트 설정
    ssh -q -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o UpdateHostKeys=no root@zapcut << 'EOF'
        cd ~/zapcut-back
        export DEBIAN_FRONTEND=noninteractive >/dev/null 2>&1
        
        # 스크립트 실행 권한 부여
        chmod +x deploy.sh
        
        # .env 파일 확인
        if [ ! -f .env ]; then
            echo "⚠️  .env file not found. Please create it manually."
            echo "Example .env content:"
            echo "OPENAI_API_KEY=your_key_here"
            echo "GOOGLE_API_KEY=your_key_here"
        fi
        
        # temp 디렉토리 생성
        mkdir -p temp
        mkdir -p nginx-logs
        
        echo "🏠 Project setup completed!"
        echo "📂 Project location: ~/zapcut-back"
EOF
}

case $1 in
    api)
        deploy_service
        ;;
    check|status)
        show_status
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    setup)
        setup
        ;;
    switch)
        switch_environment $2
        ;;
    debug)
        debug_info
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        if [ -z "$1" ]; then
            deploy_service
        else
            echo "❌ Unknown command: $1"
            show_usage
            exit 1
        fi
        ;;
esac 
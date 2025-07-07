## SSH 터널링 설정 가이드

### 1. Bastion 호스트 설정

bastion에 접속한 뒤 본인의 public key를 생성하여 기입합니다.

### 2. Zapcut 인스턴스 설정

zapcut 인스턴스에도 동일한 과정을 진행합니다.

### 3. SSH Config 설정

`~/.ssh/config` 파일에 다음과 같이 설정합니다:

Host zapcut-bastion
HostName (public ip)
User (user-name)

Host zapcut
HostName (private ip)
User (user-name)
ProxyJump bastion

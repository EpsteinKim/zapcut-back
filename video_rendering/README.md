# Video Rendering Image

## Build

```bash
docker build -f video_rendering/Dockerfile -t zapcut-video-render:latest .
```

## Run (local)

```bash
docker run --rm -p 8080:80 \
  -e ENV=production \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e GOOGLE_AI_API_KEY=$GOOGLE_AI_API_KEY \
  -e DATABASE_URL=$DATABASE_URL \
  -e SECRET_KEY=$SECRET_KEY \
  zapcut-video-render:latest
```

## EKS (example manifest)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zapcut-video-render
spec:
  replicas: 2
  selector:
    matchLabels:
      app: zapcut-video-render
  template:
    metadata:
      labels:
        app: zapcut-video-render
    spec:
      containers:
        - name: render
          image: <ECR_OR_REGISTRY>/zapcut-video-render:latest
          ports:
            - containerPort: 80
          env:
            - name: ENV
              value: "production"
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: zapcut-secrets
                  key: openai_api_key
            - name: GOOGLE_AI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: zapcut-secrets
                  key: google_ai_api_key
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: zapcut-secrets
                  key: database_url
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: zapcut-secrets
                  key: secret_key
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "2000m"
              memory: "4Gi"
```

엔드포인트: `POST /shorts/video` 등 렌더링 관련 라우트를 이 이미지에서 처리.

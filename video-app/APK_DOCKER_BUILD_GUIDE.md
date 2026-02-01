# Docker APK 构建指南 🐳

本文档介绍如何使用 Docker 容器构建 Android APK，无需本地安装 Android SDK 和 JDK。

## 为什么使用 Docker？

| 优点 | 说明 |
|------|------|
| 🔄 环境一致 | 团队成员使用相同的构建环境，避免"在我机器上能用"的问题 |
| 📦 无需配置 | 不需要本地安装 JDK、Android SDK 等工具 |
| 🚀 CI/CD 友好 | 可以轻松集成到持续集成/持续部署流程 |
| 🧹 干净隔离 | 构建环境与本地系统完全隔离 |

## 前置要求

1. **Docker** - 确保已安装并运行 Docker
   - macOS/Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: `sudo apt install docker.io` 或参考 [官方文档](https://docs.docker.com/engine/install/)

2. **检查 Docker 状态**:
   ```bash
   docker --version
   docker info
   ```

## 快速开始

### 方法一：使用封装脚本（推荐）

```bash
# 进入项目目录
cd video-app

# 构建 Debug APK
./build-apk.sh --docker

# 构建 Release APK
./build-apk.sh release --docker

# APK 输出到 output/ 目录
```

### 方法二：使用 Docker 脚本

```bash
# 构建 Debug APK
./build-apk-docker.sh debug

# 构建 Release APK
./build-apk-docker.sh release

# 强制重新构建镜像
./build-apk-docker.sh release --rebuild
```

### 方法三：使用 Docker Compose

```bash
# 构建 Debug APK
docker-compose -f docker-compose.apk-builder.yml up --build

# 构建 Release APK
docker-compose -f docker-compose.apk-builder.yml run --rm apk-builder release
```

### 方法四：手动 Docker 命令

```bash
# 构建 Docker 镜像
docker build -f Dockerfile.apk-builder -t video-app-apk-builder .

# 运行构建 (Debug)
docker run --rm \
  -v $(pwd):/app/source:ro \
  -v $(pwd)/output:/app/output \
  -v video-app-gradle-cache:/root/.gradle \
  video-app-apk-builder debug

# 运行构建 (Release)
docker run --rm \
  -v $(pwd):/app/source:ro \
  -v $(pwd)/output:/app/output \
  -v video-app-gradle-cache:/root/.gradle \
  video-app-apk-builder release
```

## 构建输出

APK 文件将输出到 `output/` 目录:

```
output/
├── app-debug.apk       # Debug 版本
└── app-release.apk     # Release 版本
```

## 安装 APK 到设备

```bash
# 连接设备并启用 USB 调试
adb devices

# 安装 Debug APK
adb install output/app-debug.apk

# 安装 Release APK
adb install output/app-release.apk
```

## EOV 配置文件

EOV (Environment Override Variables) 文件用于配置 API 地址等环境变量。

### 创建 eov 文件

在项目根目录（`video-app` 的父目录）创建 `eov` 文件：

```bash
# API 服务器地址
API_BASE_URL=http://your-api-server:5000

# 可选配置
API_VERSION=v1
API_TIMEOUT=30000
```

### Docker 构建时使用

`build-apk-docker.sh` 脚本会自动检测并挂载 eov 文件到容器中。

## 缓存管理

Docker 构建使用命名卷缓存 Gradle 和 node_modules，以加速后续构建：

```bash
# 查看缓存卷
docker volume ls | grep video-app

# 清理 Gradle 缓存（如果构建失败）
docker volume rm video-app-gradle-cache

# 清理 node_modules 缓存
docker volume rm video-app-node-modules

# 清理所有缓存
docker volume rm video-app-gradle-cache video-app-node-modules
```

## Dockerfile 说明

`Dockerfile.apk-builder` 包含以下组件：

| 组件 | 版本 | 说明 |
|------|------|------|
| Ubuntu | 24.04 | 基础操作系统 |
| OpenJDK | 21 | Java 运行环境 |
| Node.js | 20.x LTS | JavaScript 运行环境 |
| Android SDK | 35 | Android 构建工具 |
| Build Tools | 35.0.0 | Android 构建工具链 |

## 故障排查

### 构建失败

1. **清理缓存重试**:
   ```bash
   docker volume rm video-app-gradle-cache
   ./build-apk-docker.sh --rebuild
   ```

2. **查看详细日志**:
   ```bash
   docker logs video-app-apk-builder-running
   ```

3. **进入容器调试**:
   ```bash
   docker run -it --rm \
     -v $(pwd):/app/source:ro \
     video-app-apk-builder bash
   ```

### 镜像构建失败

1. **检查网络连接**:
   ```bash
   docker run --rm alpine ping -c 3 dl.google.com
   ```

2. **清理 Docker 缓存**:
   ```bash
   docker system prune -f
   docker builder prune -f
   ```

3. **重新构建镜像**:
   ```bash
   docker build --no-cache -f Dockerfile.apk-builder -t video-app-apk-builder .
   ```

### 内存不足

Gradle 构建需要较多内存，确保 Docker 有足够资源：

1. **macOS/Windows**: Docker Desktop → Settings → Resources → Memory (建议 4GB+)
2. **Linux**: 检查可用内存 `free -h`

### APK 安装失败

1. **检查 APK 签名**:
   ```bash
   apksigner verify --verbose output/app-debug.apk
   ```

2. **检查设备兼容性**:
   - minSdkVersion: 23 (Android 6.0)
   - targetSdkVersion: 35

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Build APK

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build APK
        working-directory: ./video-app
        run: |
          chmod +x build-apk-docker.sh
          ./build-apk-docker.sh release
      
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: app-release
          path: video-app/output/*.apk
```

### GitLab CI 示例

```yaml
build-apk:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - cd video-app
    - chmod +x build-apk-docker.sh
    - ./build-apk-docker.sh release
  artifacts:
    paths:
      - video-app/output/*.apk
```

## 常见问题

### Q: 首次构建很慢？

首次构建需要下载 Docker 镜像（约 2GB）和依赖项，后续构建会使用缓存，速度会更快。

### Q: 如何使用私有 npm registry？

在 Dockerfile 中添加 npm 配置：

```dockerfile
RUN npm config set registry https://your-private-registry.com
```

### Q: 如何添加签名密钥？

将签名密钥挂载到容器中：

```bash
docker run --rm \
  -v $(pwd):/app/source:ro \
  -v $(pwd)/output:/app/output \
  -v /path/to/keystore.jks:/app/keystore.jks:ro \
  video-app-apk-builder release
```

---

如有问题，请参考 [APK_BUILD_GUIDE.md](./APK_BUILD_GUIDE.md) 或提交 Issue。

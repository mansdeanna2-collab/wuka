# 视频播放器应用 (Video Player App)

一个现代化的视频播放器应用，支持 H5 网页和移动端 App 打包。

## 项目结构

```
├── video-app/          # 前端 Vue.js 应用
│   ├── src/
│   │   ├── api/        # API 接口封装
│   │   ├── components/ # Vue 组件
│   │   ├── views/      # 页面视图
│   │   ├── router/     # 路由配置
│   │   └── assets/     # 静态资源
│   ├── package.json    # 依赖配置
│   └── capacitor.config.json  # 移动端配置
├── api/                # 后端 API 服务
│   ├── api_server.py   # Flask API 服务器
│   └── requirements.txt
├── video_database.py   # 数据库模块 (MySQL/SQLite)
├── video_collector.py  # 视频采集脚本
├── deploy.py           # Docker自动部署脚本
├── docker-compose.yml  # Docker Compose配置
└── video_viewer.html   # 旧版 HTML 播放器
```

## 功能特性

- ✅ Vue 3 + Vite 现代化前端架构
- ✅ 支持 H5 网页访问
- ✅ 支持打包为 Android/iOS App (Capacitor)
- ✅ 视频分类和搜索
- ✅ 视频播放器支持多集
- ✅ 响应式设计，适配手机和平板
- ✅ REST API 接口
- ✅ 支持 MySQL 和 SQLite 数据库
- ✅ Docker 一键自动部署 (Ubuntu 22)

## 🚀 Docker 一键部署 (推荐)

适用于 **Ubuntu 22.04 LTS**，自动检测并安装所有依赖。

### 一键部署

```bash
# 克隆项目
git clone <repository-url>
cd <project-directory>

# 运行自动部署脚本 (需要sudo权限)
sudo python3 deploy.py
```

部署脚本会自动:
- 检测并安装 Docker (如未安装)
- 检测并安装 Docker Compose (如未安装)
- 构建前端和后端镜像
- 启动所有服务

### 部署命令

```bash
sudo python3 deploy.py              # 完整部署
sudo python3 deploy.py --check      # 仅检查依赖
sudo python3 deploy.py --no-build   # 不重新构建镜像
sudo python3 deploy.py --stop       # 停止应用
sudo python3 deploy.py --restart    # 重启应用
sudo python3 deploy.py --logs       # 查看日志
sudo python3 deploy.py --clean      # 清理所有容器和镜像
```

### 访问应用

部署完成后:
- 前端: http://localhost:8080
- API: http://localhost:5000/api

## 手动安装

### 1. 安装前端依赖

```bash
cd video-app
npm install
```

### 2. 安装后端依赖

```bash
cd api
pip install -r requirements.txt
```

### 3. 启动开发服务器

启动后端 API 服务器:
```bash
cd api
python api_server.py --sqlite  # 使用 SQLite
# 或
python api_server.py           # 使用 MySQL
```

启动前端开发服务器:
```bash
cd video-app
npm run dev
```

访问 http://localhost:3000 查看应用。

## Docker 手动部署

如果不使用自动部署脚本，可以手动使用 Docker Compose:

```bash
# 构建并启动
docker compose up -d --build

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

## 打包为移动端 App

### Android

```bash
cd video-app
npm run build                    # 构建前端
npm run cap:add:android          # 添加 Android 平台 (首次)
npm run cap:sync                 # 同步构建文件
npm run cap:open:android         # 打开 Android Studio
```

### iOS

```bash
cd video-app
npm run build                    # 构建前端
npm run cap:add:ios              # 添加 iOS 平台 (首次)
npm run cap:sync                 # 同步构建文件
npm run cap:open:ios             # 打开 Xcode
```

## API 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/videos | 获取视频列表 |
| GET | /api/videos/:id | 获取单个视频 |
| GET | /api/videos/search | 搜索视频 |
| GET | /api/videos/category | 按分类获取 |
| GET | /api/videos/top | 热门视频 |
| POST | /api/videos/:id/play | 更新播放次数 |
| GET | /api/categories | 获取分类列表 |
| GET | /api/statistics | 数据库统计 |

## 数据库配置

默认使用 MySQL，通过环境变量配置:

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_DATABASE=psspsj
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
```

如果 MySQL 不可用，自动降级到 SQLite。

## 导入视频数据

从采集器导入:
```bash
python video_collector.py --all --format json
python video_database.py --import-spjs videos_*.json
```

## 技术栈

- **前端**: Vue 3, Vite, Vue Router, Axios
- **后端**: Flask, Flask-CORS
- **数据库**: MySQL / SQLite
- **移动端**: Capacitor (支持 Android/iOS)

## 许可证

ISC
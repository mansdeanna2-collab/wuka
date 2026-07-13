#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker自动部署脚本 (Docker Auto-Deployment Script)
================================================
适用于 Ubuntu 22.04 LTS 的自动部署脚本

功能:
- 自动检测并安装 Docker
- 自动检测并安装 Docker Compose
- 自动检测并安装其他依赖
- 构建并启动 Docker 容器

使用方法:
    sudo python3 deploy.py              # 部署应用
    sudo python3 deploy.py --check      # 仅检查依赖
    sudo python3 deploy.py --stop       # 停止应用
    sudo python3 deploy.py --restart    # 重启应用
    sudo python3 deploy.py --logs       # 查看日志
    sudo python3 deploy.py --clean      # 清理所有容器和镜像

作者: Auto-generated
日期: 2026-01-30
"""

import os
import sys
import subprocess
import argparse
import shutil
import time
from typing import Tuple


class Colors:
    """终端颜色常量"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str) -> None:
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}{Colors.RESET}\n")


def print_step(text: str) -> None:
    """打印步骤"""
    print(f"{Colors.BLUE}[*]{Colors.RESET} {text}")


def print_success(text: str) -> None:
    """打印成功信息"""
    print(f"{Colors.GREEN}[✓]{Colors.RESET} {text}")


def print_warning(text: str) -> None:
    """打印警告信息"""
    print(f"{Colors.YELLOW}[!]{Colors.RESET} {text}")


def print_error(text: str) -> None:
    """打印错误信息"""
    print(f"{Colors.RED}[✗]{Colors.RESET} {text}")


def run_command(cmd: str, check: bool = True, capture: bool = False,
                shell: bool = True) -> Tuple[int, str, str]:
    """
    执行系统命令

    Args:
        cmd: 要执行的命令
        check: 是否检查返回码
        capture: 是否捕获输出
        shell: 是否使用shell执行

    Returns:
        (返回码, 标准输出, 标准错误)
    """
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=capture,
            text=True,
            check=check
        )
        return (result.returncode,
                result.stdout if capture else '',
                result.stderr if capture else '')
    except subprocess.CalledProcessError as e:
        return (e.returncode,
                e.stdout if capture else '',
                e.stderr if capture else '')
    except Exception as e:
        return (1, '', str(e))


def check_root() -> bool:
    """检查是否为root用户"""
    return os.geteuid() == 0


def check_ubuntu_version() -> Tuple[bool, str]:
    """
    检查Ubuntu版本

    Returns:
        (是否为Ubuntu 22, 版本信息)
    """
    code, stdout, _ = run_command("lsb_release -rs", capture=True, check=False)
    if code != 0:
        # 尝试读取 /etc/os-release
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read()
                if 'VERSION_ID="22' in content:
                    return True, "22.04"
                if 'VERSION_ID=' in content:
                    for line in content.split('\n'):
                        if line.startswith('VERSION_ID='):
                            version = line.split('=')[1].strip('"')
                            return version.startswith('22'), version
        except FileNotFoundError:
            pass
        return False, "Unknown"

    version = stdout.strip()
    return version.startswith('22'), version


def is_docker_installed() -> bool:
    """检查Docker是否已安装"""
    code, _, _ = run_command("docker --version", capture=True, check=False)
    return code == 0


def is_docker_compose_installed() -> bool:
    """检查Docker Compose是否已安装"""
    # 先检查 docker compose (V2)
    code, _, _ = run_command("docker compose version", capture=True, check=False)
    if code == 0:
        return True

    # 再检查 docker-compose (V1)
    code, _, _ = run_command("docker-compose --version", capture=True, check=False)
    return code == 0


def is_docker_running() -> bool:
    """检查Docker服务是否运行"""
    code, _, _ = run_command("docker info", capture=True, check=False)
    return code == 0


def install_docker() -> bool:
    """
    安装Docker (适用于Ubuntu)

    Returns:
        安装是否成功
    """
    print_step("正在更新apt包索引...")
    code, _, _ = run_command("apt-get update -y")
    if code != 0:
        print_error("更新apt包索引失败")
        return False

    print_step("正在安装必要的依赖...")
    code, _, _ = run_command(
        "apt-get install -y ca-certificates curl gnupg lsb-release"
    )
    if code != 0:
        print_error("安装依赖失败")
        return False

    print_step("正在添加Docker官方GPG密钥...")
    run_command("install -m 0755 -d /etc/apt/keyrings", check=False)
    code, _, _ = run_command(
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | "
        "gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes"
    )
    if code != 0:
        print_error("添加GPG密钥失败")
        return False

    run_command("chmod a+r /etc/apt/keyrings/docker.gpg", check=False)

    print_step("正在添加Docker软件源...")
    code, arch, _ = run_command("dpkg --print-architecture", capture=True)
    arch = arch.strip()

    code, codename, _ = run_command(
        ". /etc/os-release && echo $VERSION_CODENAME", capture=True
    )
    codename = codename.strip() or "jammy"  # Ubuntu 22.04的代号

    repo_line = (
        f'deb [arch={arch} signed-by=/etc/apt/keyrings/docker.gpg] '
        f'https://download.docker.com/linux/ubuntu {codename} stable'
    )

    with open('/etc/apt/sources.list.d/docker.list', 'w') as f:
        f.write(repo_line + '\n')

    print_step("正在更新apt包索引...")
    code, _, _ = run_command("apt-get update -y")
    if code != 0:
        print_error("更新apt包索引失败")
        return False

    print_step("正在安装Docker Engine...")
    code, _, _ = run_command(
        "apt-get install -y docker-ce docker-ce-cli containerd.io "
        "docker-buildx-plugin docker-compose-plugin"
    )
    if code != 0:
        print_error("安装Docker Engine失败")
        return False

    print_step("正在启动Docker服务...")
    code, _, _ = run_command("systemctl start docker")
    if code != 0:
        print_error("启动Docker服务失败")
        return False

    code, _, _ = run_command("systemctl enable docker")

    print_success("Docker安装完成!")
    return True


def install_docker_compose_standalone() -> bool:
    """
    安装独立版本的Docker Compose (如果docker compose plugin不可用)

    Returns:
        安装是否成功
    """
    print_step("正在下载Docker Compose...")

    # 获取最新版本
    code, version, _ = run_command(
        'curl -s https://api.github.com/repos/docker/compose/releases/latest | '
        'grep "tag_name" | cut -d\'"\' -f4',
        capture=True,
        check=False
    )

    if code != 0 or not version.strip():
        version = "v2.24.0"  # 使用默认版本
    else:
        version = version.strip()

    print_step(f"正在安装 Docker Compose {version}...")

    code, arch, _ = run_command("uname -m", capture=True)
    arch = arch.strip()

    # 架构映射
    arch_map = {
        'x86_64': 'x86_64',
        'aarch64': 'aarch64',
        'armv7l': 'armv7'
    }
    arch = arch_map.get(arch, 'x86_64')

    download_url = (
        f"https://github.com/docker/compose/releases/download/{version}/"
        f"docker-compose-linux-{arch}"
    )

    code, _, _ = run_command(
        f"curl -SL {download_url} -o /usr/local/bin/docker-compose"
    )
    if code != 0:
        print_error("下载Docker Compose失败")
        return False

    code, _, _ = run_command("chmod +x /usr/local/bin/docker-compose")

    print_success("Docker Compose安装完成!")
    return True


def check_and_install_dependencies() -> bool:
    """
    检查并安装所有依赖

    Returns:
        所有依赖是否就绪
    """
    print_header("检查系统依赖")

    # 检查Ubuntu版本
    print_step("检查操作系统版本...")
    is_ubuntu22, version = check_ubuntu_version()
    if is_ubuntu22:
        print_success(f"检测到 Ubuntu {version}")
    else:
        print_warning(f"当前系统版本: {version} (建议使用 Ubuntu 22.04)")

    # 检查Docker
    print_step("检查Docker安装状态...")
    if is_docker_installed():
        print_success("Docker 已安装")

        if not is_docker_running():
            print_warning("Docker服务未运行，正在启动...")
            code, _, _ = run_command("systemctl start docker", check=False)
            if code != 0:
                print_error("无法启动Docker服务")
                return False
            print_success("Docker服务已启动")
    else:
        print_warning("Docker 未安装，正在安装...")
        if not install_docker():
            print_error("Docker安装失败")
            return False

    # 检查Docker Compose
    print_step("检查Docker Compose安装状态...")
    if is_docker_compose_installed():
        print_success("Docker Compose 已安装")
    else:
        print_warning("Docker Compose 未安装，正在安装...")
        if not install_docker_compose_standalone():
            print_error("Docker Compose安装失败")
            return False

    # 检查必要的命令
    required_commands = ['curl', 'git']
    for cmd in required_commands:
        print_step(f"检查 {cmd}...")
        if shutil.which(cmd):
            print_success(f"{cmd} 已安装")
        else:
            print_warning(f"{cmd} 未安装，正在安装...")
            code, _, _ = run_command(f"apt-get install -y {cmd}", check=False)
            if code != 0:
                print_error(f"安装 {cmd} 失败")
                return False
            print_success(f"{cmd} 安装完成")

    print_success("所有依赖检查完成!")
    return True


def create_docker_files(base_dir: str) -> bool:
    """
    创建Docker相关文件

    Args:
        base_dir: 项目根目录

    Returns:
        是否成功创建
    """
    print_header("创建Docker配置文件")

    # 创建API服务的Dockerfile
    api_dockerfile = os.path.join(base_dir, 'api', 'Dockerfile')
    if not os.path.exists(api_dockerfile):
        print_step("创建API服务Dockerfile...")
        api_dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api_server.py .

# Note: video_database.py is mounted at runtime via docker-compose

# Default to SQLite (overridable via docker-compose environment)
ENV USE_MYSQL=false

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run the application with a production WSGI server (gunicorn)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "api_server:app"]
'''
        with open(api_dockerfile, 'w') as f:
            f.write(api_dockerfile_content)
        print_success("API Dockerfile 已创建")
    else:
        print_success("API Dockerfile 已存在")

    # 创建前端的Dockerfile
    frontend_dockerfile = os.path.join(base_dir, 'video-app', 'Dockerfile')
    if not os.path.exists(frontend_dockerfile):
        print_step("创建前端Dockerfile...")
        frontend_dockerfile_content = '''# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# npm registry (can be overridden, e.g. https://registry.npmmirror.com for
# hosts with poor connectivity to registry.npmjs.org)
ARG NPM_REGISTRY=https://registry.npmjs.org

# Copy package files
COPY package*.json ./

# Configure npm registry and make network fetches more resilient
RUN npm config set registry "$NPM_REGISTRY" \\
    && npm config set fetch-retries 5 \\
    && npm config set fetch-retry-mintimeout 20000 \\
    && npm config set fetch-retry-maxtimeout 120000 \\
    && npm config set fetch-timeout 600000

# Install dependencies (include devDependencies so build tools like vite
# are available even when NODE_ENV=production is set in the build environment).
# Verify vite is actually installed afterwards: on network timeouts npm can
# crash with "Exit handler never called!" but still exit 0, leaving an
# incomplete node_modules that Docker would cache as a "successful" layer.
RUN npm ci --include=dev && node_modules/.bin/vite --version

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD wget --quiet --tries=1 --spider http://localhost:80 || exit 1
'''
        with open(frontend_dockerfile, 'w') as f:
            f.write(frontend_dockerfile_content)
        print_success("前端 Dockerfile 已创建")
    else:
        print_success("前端 Dockerfile 已存在")

    # 创建nginx配置
    nginx_conf = os.path.join(base_dir, 'video-app', 'nginx.conf')
    if not os.path.exists(nginx_conf):
        print_step("创建Nginx配置...")
        nginx_conf_content = '''server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;

    # API proxy
    location /api {
        proxy_pass http://api:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 60s;
    }

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
        # Prevent caching of HTML files to ensure updates are always fetched
        add_header Cache-Control "no-cache, no-store, must-revalidate" always;
        add_header Pragma "no-cache" always;
        add_header Expires "0" always;
    }

    # Cache static assets (use aggressive caching since Vite uses hashed filenames)
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
'''
        with open(nginx_conf, 'w') as f:
            f.write(nginx_conf_content)
        print_success("Nginx配置已创建")
    else:
        print_success("Nginx配置已存在")

    # 创建docker-compose.yml
    compose_file = os.path.join(base_dir, 'docker-compose.yml')
    if not os.path.exists(compose_file):
        print_step("创建docker-compose.yml...")
        compose_content = '''name: video-app

services:
  # API服务
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    container_name: video-api
    restart: unless-stopped
    ports:
      - "5001:5000"
    volumes:
      - video-data:/app/data
      - ./tools/video_database.py:/app/video_database.py:ro
      - ./tools/hanime_scraper.py:/app/hanime_scraper.py:ro
    environment:
      - USE_MYSQL=false
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - video-network

  # 前端服务
  frontend:
    build:
      context: ./video-app
      dockerfile: Dockerfile
      args:
        NPM_REGISTRY: ${NPM_REGISTRY:-https://registry.npmjs.org}
    container_name: video-frontend
    restart: unless-stopped
    ports:
      - "8898:80"
    depends_on:
      api:
        condition: service_healthy
    networks:
      - video-network

networks:
  video-network:
    driver: bridge

volumes:
  video-data:
'''
        with open(compose_file, 'w') as f:
            f.write(compose_content)
        print_success("docker-compose.yml 已创建")
    else:
        print_success("docker-compose.yml 已存在")

    # 创建.dockerignore
    api_dockerignore = os.path.join(base_dir, 'api', '.dockerignore')
    if not os.path.exists(api_dockerignore):
        print_step("创建API .dockerignore...")
        with open(api_dockerignore, 'w') as f:
            f.write('''__pycache__
*.pyc
*.pyo
*.db
.git
.gitignore
*.log
.env
.venv
venv
''')
        print_success("API .dockerignore 已创建")

    frontend_dockerignore = os.path.join(base_dir, 'video-app', '.dockerignore')
    if not os.path.exists(frontend_dockerignore):
        print_step("创建前端 .dockerignore...")
        with open(frontend_dockerignore, 'w') as f:
            f.write('''node_modules
dist
.git
.gitignore
*.log
.env
.env.local
android
ios
''')
        print_success("前端 .dockerignore 已创建")

    print_success("所有Docker配置文件已就绪!")
    return True


def get_compose_command() -> str:
    """获取正确的docker compose命令"""
    # 使用 -p video-app 明确指定项目名称，避免目录名称问题
    code, _, _ = run_command("docker compose version", capture=True, check=False)
    if code == 0:
        return "docker compose -p video-app"
    return "docker-compose -p video-app"


DEFAULT_NPM_REGISTRY = "https://registry.npmjs.org"
MIRROR_NPM_REGISTRY = "https://registry.npmmirror.com"


def detect_npm_registry() -> str:
    """
    检测可用的npm registry

    前端镜像构建时需要从npm registry下载依赖。如果服务器访问
    registry.npmjs.org 不稳定(常见于国内服务器)，npm ci 会因网络超时
    而安装出不完整的 node_modules(npm 存在超时后仍以退出码0结束的bug，
    即 "Exit handler never called!")，进而导致构建时报 "vite: not found"。
    这里先探测官方registry的连通性，不通则自动切换到国内镜像。
    """
    # 允许用户通过环境变量显式指定
    env_registry = os.environ.get('NPM_REGISTRY')
    if env_registry:
        print_step(f"使用环境变量指定的npm registry: {env_registry}")
        return env_registry

    print_step("检测npm registry连通性...")
    code, _, _ = run_command(
        f"curl -sf -m 10 -o /dev/null {DEFAULT_NPM_REGISTRY}/vite",
        capture=True, check=False
    )
    if code == 0:
        print_success(f"npm官方registry可用: {DEFAULT_NPM_REGISTRY}")
        return DEFAULT_NPM_REGISTRY

    print_warning("无法访问 registry.npmjs.org，尝试国内镜像...")
    code, _, _ = run_command(
        f"curl -sf -m 10 -o /dev/null {MIRROR_NPM_REGISTRY}/vite",
        capture=True, check=False
    )
    if code == 0:
        print_success(f"已切换到npm国内镜像: {MIRROR_NPM_REGISTRY}")
        return MIRROR_NPM_REGISTRY

    print_warning(
        "官方registry和国内镜像均无法访问，仍使用官方registry，"
        "构建可能因网络问题失败"
    )
    return DEFAULT_NPM_REGISTRY


def clean_build_cache(compose_cmd: str) -> None:
    """
    清理可能导致依赖缺失的Docker构建缓存

    构建阶段依赖(如 vite)被安装在 node_modules 层中。如果之前用旧的
    Dockerfile(未包含 devDependencies)构建过，BuildKit 会缓存一个缺少
    vite 的层。由于 frontend 与 admin 共享相同的构建步骤，该损坏的缓存层
    会被复用，导致即使加了 --no-cache 也可能出现 "vite: not found"。
    这里主动删除项目镜像并清理 BuildKit 构建缓存，确保下次为全新构建。
    """
    print_step("清理旧的镜像与构建缓存以避免依赖缺失...")
    # 删除本项目已构建的镜像(忽略不存在的情况)
    run_command(f"{compose_cmd} down --rmi local", check=False)
    # 清理 BuildKit 构建缓存(包含损坏的 node_modules 层)
    run_command("docker builder prune -f", check=False)


def wait_for_service_healthy(compose_cmd: str, service: str, timeout: int = 60) -> bool:
    """
    等待服务变为健康状态

    Args:
        compose_cmd: docker compose命令
        service: 服务名称
        timeout: 超时时间(秒)

    Returns:
        服务是否健康
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        code, stdout, _ = run_command(
            f"{compose_cmd} ps --format json",
            capture=True,
            check=False
        )
        if code == 0 and 'healthy' in stdout.lower():
            return True
        time.sleep(2)
    return False


def deploy_application(base_dir: str, build: bool = True,
                       no_cache: bool = False) -> bool:
    """
    部署应用

    Args:
        base_dir: 项目根目录
        build: 是否重新构建镜像
        no_cache: 是否禁用Docker缓存强制重新构建

    Returns:
        是否部署成功
    """
    print_header("部署应用")

    compose_cmd = get_compose_command()
    os.chdir(base_dir)

    if build:
        # 选择可用的npm registry(通过NPM_REGISTRY环境变量传给docker compose
        # 的build args)，避免因访问registry.npmjs.org超时导致依赖安装不完整
        os.environ['NPM_REGISTRY'] = detect_npm_registry()

        print_step("正在构建Docker镜像...")
        build_cmd = f"{compose_cmd} build"
        if no_cache:
            build_cmd += " --no-cache"
            print_step("使用 --no-cache 强制重新构建...")
        code, _, _ = run_command(build_cmd)
        if code != 0:
            # 常见失败原因:
            # 1. 网络问题导致npm依赖下载超时(npm可能超时后仍以退出码0结束，
            #    留下不完整的node_modules缓存层，报 "vite: not found")
            # 2. 旧的Docker构建缓存中存在缺少devDependencies的node_modules层
            # 因此先主动清理镜像与构建缓存，再使用 --no-cache --pull 重新构建。
            if not no_cache:
                print_warning("构建镜像失败，可能是Docker缓存导致依赖缺失")
                clean_build_cache(compose_cmd)
                print_step("正在使用 --no-cache 自动重新构建...")
                code, _, _ = run_command(
                    f"{compose_cmd} build --no-cache --pull"
                )
            if code != 0:
                print_error("构建镜像失败")
                print_warning(
                    "如果日志中出现 \"vite: not found\" 或 npm 报 "
                    "\"Exit handler never called!\"，通常是服务器访问npm "
                    "registry网络超时导致依赖安装不完整。可尝试:"
                )
                print("  1. 检查服务器到npm registry的网络连通性")
                print("  2. 使用国内镜像重试: "
                      "NPM_REGISTRY=https://registry.npmmirror.com "
                      "sudo -E python3 deploy.py --force-rebuild")
                return False
        print_success("镜像构建完成")

    print_step("正在启动容器...")
    code, _, _ = run_command(f"{compose_cmd} up -d")
    if code != 0:
        print_error("启动容器失败")
        return False

    print_success("容器启动完成!")

    # 等待服务就绪
    print_step("等待服务就绪 (最多60秒)...")
    if wait_for_service_healthy(compose_cmd, "api", timeout=60):
        print_success("API服务已就绪")
    else:
        print_warning("API服务健康检查超时，请手动检查服务状态")

    # 检查服务状态
    code, stdout, _ = run_command(f"{compose_cmd} ps", capture=True)
    print(f"\n{stdout}")

    print_success("部署完成!")
    print(f"\n{Colors.GREEN}访问地址:{Colors.RESET}")
    print("  - 前端: http://localhost:8898")
    print("  - API:  http://localhost:5001/api")

    return True


def stop_application(base_dir: str) -> bool:
    """停止应用"""
    print_header("停止应用")

    compose_cmd = get_compose_command()
    os.chdir(base_dir)

    code, _, _ = run_command(f"{compose_cmd} down")
    if code != 0:
        print_error("停止应用失败")
        return False

    print_success("应用已停止")
    return True


def restart_application(base_dir: str) -> bool:
    """重启应用"""
    print_header("重启应用")

    compose_cmd = get_compose_command()
    os.chdir(base_dir)

    code, _, _ = run_command(f"{compose_cmd} restart")
    if code != 0:
        print_error("重启应用失败")
        return False

    print_success("应用已重启")
    return True


def show_logs(base_dir: str, follow: bool = True) -> None:
    """显示日志"""
    compose_cmd = get_compose_command()
    os.chdir(base_dir)

    cmd = f"{compose_cmd} logs"
    if follow:
        cmd += " -f"

    run_command(cmd, check=False)


def clean_all(base_dir: str) -> bool:
    """清理所有容器和镜像"""
    print_header("清理Docker资源")

    compose_cmd = get_compose_command()
    os.chdir(base_dir)

    print_step("停止并删除容器...")
    run_command(f"{compose_cmd} down -v --rmi local", check=False)

    print_step("清理未使用的资源...")
    run_command("docker system prune -f", check=False)

    print_success("清理完成")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='视频应用Docker自动部署脚本 (适用于Ubuntu 22)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  sudo python3 deploy.py              # 完整部署
  sudo python3 deploy.py --check      # 仅检查依赖
  sudo python3 deploy.py --no-build   # 不重新构建镜像
  sudo python3 deploy.py --force-rebuild  # 强制重新构建(禁用缓存)
  sudo python3 deploy.py --stop       # 停止应用
  sudo python3 deploy.py --restart    # 重启应用
  sudo python3 deploy.py --logs       # 查看日志
  sudo python3 deploy.py --clean      # 清理所有容器和镜像
        '''
    )

    parser.add_argument('--check', action='store_true',
                        help='仅检查依赖，不部署')
    parser.add_argument('--no-build', action='store_true',
                        help='不重新构建镜像')
    parser.add_argument('--force-rebuild', action='store_true',
                        help='强制重新构建镜像(禁用Docker缓存)')
    parser.add_argument('--stop', action='store_true',
                        help='停止应用')
    parser.add_argument('--restart', action='store_true',
                        help='重启应用')
    parser.add_argument('--logs', action='store_true',
                        help='查看日志')
    parser.add_argument('--clean', action='store_true',
                        help='清理所有容器和镜像')
    parser.add_argument('--dir', type=str, default=None,
                        help='项目目录 (默认: 脚本所在目录)')

    args = parser.parse_args()

    # 获取项目目录
    if args.dir:
        base_dir = os.path.abspath(args.dir)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    print_header("视频应用 Docker 自动部署工具")
    print(f"项目目录: {base_dir}")
    print("系统: Ubuntu")

    # 检查root权限
    if not check_root():
        print_error("请使用 sudo 运行此脚本")
        print("示例: sudo python3 deploy.py")
        sys.exit(1)

    # 检查冲突的参数
    if args.no_build and args.force_rebuild:
        print_error("--no-build 和 --force-rebuild 不能同时使用")
        sys.exit(1)

    # 处理不同的操作
    if args.logs:
        show_logs(base_dir)
        return

    if args.stop:
        if stop_application(base_dir):
            sys.exit(0)
        sys.exit(1)

    if args.restart:
        if restart_application(base_dir):
            sys.exit(0)
        sys.exit(1)

    if args.clean:
        if clean_all(base_dir):
            sys.exit(0)
        sys.exit(1)

    # 检查并安装依赖
    if not check_and_install_dependencies():
        print_error("依赖检查失败")
        sys.exit(1)

    if args.check:
        print_success("依赖检查完成")
        sys.exit(0)

    # 创建Docker配置文件
    if not create_docker_files(base_dir):
        print_error("创建Docker配置文件失败")
        sys.exit(1)

    # 部署应用
    if not deploy_application(base_dir, build=not args.no_build,
                              no_cache=args.force_rebuild):
        print_error("部署失败")
        sys.exit(1)

    print_header("部署成功! 🎉")
    print("使用以下命令管理应用:")
    print(f"  查看日志: sudo python3 {os.path.basename(__file__)} --logs")
    print(f"  停止应用: sudo python3 {os.path.basename(__file__)} --stop")
    print(f"  重启应用: sudo python3 {os.path.basename(__file__)} --restart")
    print(f"  强制重建: sudo python3 {os.path.basename(__file__)} --force-rebuild")
    print(f"  清理资源: sudo python3 {os.path.basename(__file__)} --clean")


if __name__ == '__main__':
    main()

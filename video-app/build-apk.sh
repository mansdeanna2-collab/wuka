#!/bin/bash
# =============================================================================
# APK 打包脚本
# 用法: ./build-apk.sh [debug|release] [--auto-install] [--docker]
# 示例: ./build-apk.sh release
#       ./build-apk.sh release --auto-install
#       ./build-apk.sh release --docker
# =============================================================================
# 版本: 2.0.0
# 更新日志:
#   - 添加 Docker 构建支持 (--docker)
#   - 改进错误处理和日志输出
#   - 优化 Gradle 缓存清理逻辑
#   - 添加版本检测功能
# =============================================================================

set -e  # 遇到错误立即退出

MODE=${1:-debug}
AUTO_INSTALL=false
USE_DOCKER=false
SCRIPT_VERSION="2.0.0"

# 解析参数
for arg in "$@"; do
    case $arg in
        --auto-install|-y)
            AUTO_INSTALL=true
            ;;
        --docker|-d)
            USE_DOCKER=true
            ;;
        --version|-v)
            echo "build-apk.sh 版本: $SCRIPT_VERSION"
            exit 0
            ;;
        --help|-h)
            echo "用法: ./build-apk.sh [debug|release] [选项]"
            echo ""
            echo "选项:"
            echo "  --auto-install, -y    自动安装缺失的依赖"
            echo "  --docker, -d          使用 Docker 容器构建 (推荐)"
            echo "  --version, -v         显示脚本版本"
            echo "  --help, -h            显示帮助信息"
            echo ""
            echo "示例:"
            echo "  ./build-apk.sh                    # 构建 Debug APK"
            echo "  ./build-apk.sh release            # 构建 Release APK"
            echo "  ./build-apk.sh release --docker   # 使用 Docker 构建 Release APK"
            echo "  ./build-apk.sh release -y         # 自动安装依赖并构建 Release APK"
            exit 0
            ;;
    esac
done

# 如果使用 Docker 模式，调用 Docker 脚本
if [ "$USE_DOCKER" = true ]; then
    echo "🐳 使用 Docker 模式构建..."
    if [ -f "build-apk-docker.sh" ]; then
        ./build-apk-docker.sh "$MODE"
        exit $?
    else
        echo "❌ 错误: 找不到 build-apk-docker.sh 脚本"
        echo "   请确保在正确的目录下运行此脚本"
        exit 1
    fi
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          📱 视频应用 APK 打包脚本                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 构建模式: $MODE"
if [ "$AUTO_INSTALL" = true ]; then
    echo "🔧 自动安装模式: 已启用"
fi
echo ""

# =============================================================================
# 辅助函数
# =============================================================================

# 询问用户是否安装
ask_install() {
    local tool_name=$1
    if [ "$AUTO_INSTALL" = true ]; then
        return 0
    fi
    echo ""
    read -p "是否自动安装 $tool_name? (y/n): " choice
    case "$choice" in
        y|Y|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ "$(uname)" = "Darwin" ]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# 安装 Node.js
install_nodejs() {
    local os=$(detect_os)
    echo "🔄 正在安装 Node.js..."
    
    case $os in
        ubuntu|debian)
            # 使用 NodeSource 安装最新 LTS
            echo "   使用 NodeSource 安装 Node.js 20.x..."
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>/dev/null
            sudo apt-get install -y nodejs 2>/dev/null
            ;;
        centos|rhel|fedora)
            curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash - 2>/dev/null
            sudo yum install -y nodejs 2>/dev/null || sudo dnf install -y nodejs 2>/dev/null
            ;;
        macos)
            if command -v brew &> /dev/null; then
                brew install node
            else
                echo "❌ 请先安装 Homebrew: https://brew.sh"
                return 1
            fi
            ;;
        *)
            # 尝试使用 nvm 安装
            if command -v nvm &> /dev/null; then
                nvm install --lts
            else
                echo "⚠️  无法自动安装，请手动安装 Node.js"
                echo "   下载地址: https://nodejs.org/"
                return 1
            fi
            ;;
    esac
    
    if command -v node &> /dev/null; then
        echo "✅ Node.js 安装成功: $(node --version)"
        return 0
    else
        echo "❌ Node.js 安装失败"
        return 1
    fi
}

# 安装 Java/JDK
install_java() {
    local os=$(detect_os)
    echo "🔄 正在安装 JDK 21..."
    
    case $os in
        ubuntu|debian)
            sudo apt-get update 2>/dev/null
            sudo apt-get install -y openjdk-21-jdk 2>/dev/null
            ;;
        centos|rhel|fedora)
            sudo yum install -y java-21-openjdk-devel 2>/dev/null || sudo dnf install -y java-21-openjdk-devel 2>/dev/null
            ;;
        macos)
            if command -v brew &> /dev/null; then
                brew install openjdk@21
                BREW_PREFIX=$(brew --prefix openjdk@21 2>/dev/null)
                if [ -n "$BREW_PREFIX" ] && [ -d "$BREW_PREFIX/libexec/openjdk.jdk" ]; then
                    sudo ln -sfn "$BREW_PREFIX/libexec/openjdk.jdk" /Library/Java/JavaVirtualMachines/openjdk-21.jdk 2>/dev/null
                fi
            else
                echo "❌ 请先安装 Homebrew: https://brew.sh"
                return 1
            fi
            ;;
        *)
            echo "⚠️  无法自动安装，请手动安装 JDK 21+"
            echo "   下载地址: https://adoptium.net/"
            return 1
            ;;
    esac
    
    if command -v java &> /dev/null; then
        echo "✅ Java 安装成功: $(java --version 2>&1 | head -1)"
        return 0
    else
        echo "❌ Java 安装失败"
        return 1
    fi
}

# 安装 Android SDK 命令行工具
install_android_sdk() {
    local os=$(detect_os)
    echo "🔄 正在安装 Android SDK 命令行工具..."
    
    # 设置默认 SDK 路径
    if [ -z "$ANDROID_HOME" ]; then
        case $os in
            macos)
                export ANDROID_HOME="$HOME/Library/Android/sdk"
                ;;
            *)
                export ANDROID_HOME="$HOME/Android/sdk"
                ;;
        esac
    fi
    
    mkdir -p "$ANDROID_HOME/cmdline-tools"
    
    # 下载命令行工具
    local CMDLINE_TOOLS_VERSION="11076708"
    local CMDLINE_TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_TOOLS_VERSION}_latest.zip"
    
    if [ "$os" = "macos" ]; then
        CMDLINE_TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-mac-${CMDLINE_TOOLS_VERSION}_latest.zip"
    fi
    
    echo "   下载 Android 命令行工具..."
    local TEMP_ZIP="/tmp/cmdline-tools.zip"
    curl -L "$CMDLINE_TOOLS_URL" -o "$TEMP_ZIP"
    
    echo "   解压命令行工具..."
    unzip -q "$TEMP_ZIP" -d "$ANDROID_HOME/cmdline-tools"
    mv "$ANDROID_HOME/cmdline-tools/cmdline-tools" "$ANDROID_HOME/cmdline-tools/latest"
    rm "$TEMP_ZIP"
    
    # 更新 PATH
    export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"
    
    # 接受许可协议并安装必要组件
    echo "   接受许可协议..."
    yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses 2>/dev/null || true
    
    echo "   安装必要的 SDK 组件..."
    "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" \
        "platform-tools" \
        "platforms;android-35" \
        "build-tools;35.0.0"
    
    echo "✅ Android SDK 安装成功"
    echo "   请将以下内容添加到您的 ~/.bashrc 或 ~/.zshrc:"
    echo "   export ANDROID_HOME=\"$ANDROID_HOME\""
    echo "   export PATH=\"\$PATH:\$ANDROID_HOME/cmdline-tools/latest/bin:\$ANDROID_HOME/platform-tools\""
    
    return 0
}

# =============================================================================
# 依赖检查
# =============================================================================

echo "🔍 检查依赖..."
echo ""

# 检查 Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js: $NODE_VERSION"
else
    echo "❌ Node.js 未安装"
    if ask_install "Node.js"; then
        install_nodejs
    else
        echo "请手动安装 Node.js 后重试"
        exit 1
    fi
fi

# 检查 npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm: $NPM_VERSION"
else
    echo "❌ npm 未安装"
    exit 1
fi

# 检查 Java
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java --version 2>&1 | head -1)
    echo "✅ Java: $JAVA_VERSION"
else
    echo "❌ Java 未安装"
    if ask_install "JDK 21"; then
        install_java
    else
        echo "请手动安装 JDK 21+ 后重试"
        exit 1
    fi
fi

# 检查 ANDROID_HOME
if [ -n "$ANDROID_HOME" ] && [ -d "$ANDROID_HOME" ]; then
    echo "✅ Android SDK: $ANDROID_HOME"
else
    echo "⚠️  ANDROID_HOME 未设置或目录不存在"
    
    # 尝试检测常见的 Android SDK 路径
    POSSIBLE_PATHS=(
        "$HOME/Android/sdk"
        "$HOME/Library/Android/sdk"
        "/opt/android-sdk"
        "/usr/local/android-sdk"
    )
    
    for path in "${POSSIBLE_PATHS[@]}"; do
        if [ -d "$path" ]; then
            export ANDROID_HOME="$path"
            echo "   发现 Android SDK: $ANDROID_HOME"
            break
        fi
    done
    
    if [ -z "$ANDROID_HOME" ] || [ ! -d "$ANDROID_HOME" ]; then
        if ask_install "Android SDK 命令行工具"; then
            install_android_sdk
        else
            echo "请手动安装 Android SDK 并设置 ANDROID_HOME 环境变量后重试"
            exit 1
        fi
    fi
fi

echo ""

# =============================================================================
# 构建流程
# =============================================================================

# 安装依赖
echo "📦 安装依赖..."
npm install --quiet
if [ $? -ne 0 ]; then
    echo "❌ npm install 失败！"
    exit 1
fi

# 安装 Capacitor 依赖
npm install @capacitor/core @capacitor/cli @capacitor/android --quiet
if [ $? -ne 0 ]; then
    echo "❌ Capacitor 依赖安装失败！"
    exit 1
fi
echo "✅ 依赖安装完成"
echo ""

# 注入 EOV 配置 (如果存在)
if [ -f "scripts/inject-eov.js" ]; then
    echo "📝 注入 EOV 配置..."
    node scripts/inject-eov.js || true
    echo ""
fi

# 检查是否需要初始化 Capacitor
if [ ! -f "capacitor.config.ts" ] && [ ! -f "capacitor.config.json" ]; then
    echo "📝 初始化 Capacitor..."
    npx cap init "视频播放器" "com.videoapp.player" --web-dir=dist
fi

# 检查是否添加了 Android 平台
if [ ! -d "android" ]; then
    echo "📲 添加 Android 平台..."
    npx cap add android
    if [ $? -ne 0 ]; then
        echo "❌ 添加 Android 平台失败！"
        exit 1
    fi
fi

# 修复 Kotlin stdlib 重复类冲突
KOTLIN_VERSION=${KOTLIN_VERSION:-1.8.22}
echo ""
echo "🔧 修复 Kotlin 依赖冲突 (Kotlin $KOTLIN_VERSION)..."
if [ -f "android/build.gradle" ]; then
    KOTLIN_FIX_MARKER="VIDEOAPP_KOTLIN_STDLIB_FIX_APPLIED"
    if ! grep -q "$KOTLIN_FIX_MARKER" "android/build.gradle"; then
        cat >> "android/build.gradle" << KOTLIN_FIX

// $KOTLIN_FIX_MARKER
// =============================================================================
// 修复 Kotlin stdlib 重复类冲突
// 从 Kotlin 1.8 开始，kotlin-stdlib-jdk7 和 kotlin-stdlib-jdk8 已合并到 kotlin-stdlib
// 这个配置确保所有模块使用统一的 Kotlin 版本，避免类重复错误
// =============================================================================
subprojects {
    afterEvaluate {
        configurations.all {
            resolutionStrategy.eachDependency { details ->
                if (details.requested.group == 'org.jetbrains.kotlin') {
                    details.useVersion '$KOTLIN_VERSION'
                }
            }
            exclude group: 'org.jetbrains.kotlin', module: 'kotlin-stdlib-jdk7'
            exclude group: 'org.jetbrains.kotlin', module: 'kotlin-stdlib-jdk8'
        }
    }
}
KOTLIN_FIX
        echo "✅ Kotlin 依赖冲突修复已应用"
    else
        echo "✅ Kotlin 依赖冲突修复已存在"
    fi
fi

# 构建 Web 应用
echo ""
echo "🔨 构建 Web 应用..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Web 构建失败！"
    exit 1
fi

# 同步 Capacitor
echo ""
echo "📲 同步到 Android..."
npx cap sync android

if [ $? -ne 0 ]; then
    echo "❌ Capacitor 同步失败！"
    exit 1
fi

# 构建 APK
echo ""
echo "📦 构建 APK..."
cd android

# 清理之前的构建 (忽略错误，因为可能是首次构建)
./gradlew clean 2>&1 || true

if [ "$MODE" = "release" ]; then
    echo "   模式: Release (签名版本)"
    ./gradlew --no-daemon assembleRelease
    APK_PATH="app/build/outputs/apk/release/app-release.apk"
    APK_UNSIGNED_PATH="app/build/outputs/apk/release/app-release-unsigned.apk"
else
    echo "   模式: Debug (调试版本)"
    ./gradlew --no-daemon assembleDebug
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
fi

BUILD_RESULT=$?
cd ..

if [ $BUILD_RESULT -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "✅ APK 打包成功！"
    echo ""
    
    # 复制 APK 到输出目录
    mkdir -p output
    FULL_APK_PATH="android/$APK_PATH"
    if [ -f "$FULL_APK_PATH" ]; then
        cp "$FULL_APK_PATH" output/
        SIZE=$(du -h "$FULL_APK_PATH" | cut -f1)
        echo "📍 APK 路径: $FULL_APK_PATH"
        echo "📍 已复制到: output/$(basename $APK_PATH)"
        echo "📊 APK 大小: $SIZE"
    elif [ -f "android/$APK_UNSIGNED_PATH" ]; then
        cp "android/$APK_UNSIGNED_PATH" output/
        SIZE=$(du -h "android/$APK_UNSIGNED_PATH" | cut -f1)
        echo "📍 APK 路径: android/$APK_UNSIGNED_PATH"
        echo "📍 已复制到: output/$(basename $APK_UNSIGNED_PATH)"
        echo "📊 APK 大小: $SIZE"
        echo ""
        echo "⚠️  注意: 这是未签名的 APK，需要签名后才能发布"
    fi
    
    echo ""
    echo "📲 安装到设备:"
    if [ "$MODE" = "release" ]; then
        echo "   adb install output/app-release.apk"
    else
        echo "   adb install output/app-debug.apk"
    fi
    echo "════════════════════════════════════════════════════════════"
else
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "❌ APK 打包失败！"
    echo ""
    echo "📋 故障排查:"
    echo "   1. 检查 Java 版本是否为 21+"
    echo "   2. 确认 ANDROID_HOME 环境变量已正确设置"
    echo "   3. 尝试清理 Gradle 缓存: rm -rf ~/.gradle/caches"
    echo "   4. 查看详细日志: cd android && ./gradlew assembleDebug --stacktrace"
    echo "   5. 使用 Docker 构建: ./build-apk.sh $MODE --docker"
    echo "════════════════════════════════════════════════════════════"
    exit 1
fi

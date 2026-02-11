#!/bin/bash
# WebUI 快速验证脚本
# 使用: 在项目根目录运行此脚本

echo "=== AUTO-MAS-Lite WebUI 版本验证开始 ==="
echo ""

# 1. 检查基础环境
echo "[1/4] 检查环境..."
python --version || echo "❌ Python 未安装"
node --version || echo "❌ Node.js 未安装"
yarn --version || echo "❌ Yarn 未安装"
echo ""

# 2. 检查后端
echo "[2/4] 启动后端 (http://localhost:36163)..."
cd "$(dirname "$0")"
timeout 3 python main.py &
BACKEND_PID=$!
sleep 2
curl -s http://localhost:36163/docs > /dev/null && echo "✅ 后端运行中" || echo "❌ 后端未响应"
kill $BACKEND_PID 2>/dev/null
echo ""

# 3. 检查前端依赖
echo "[3/4] 检查前端依赖..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules 不存在，运行 yarn install..."
    yarn install
fi
echo "✅ 前端依赖已就绪"
echo ""

# 4. 显示启动命令
echo "[4/4] 准备就绪！"
echo ""
echo "=== 启动命令 ==="
echo ""
echo "终端 1 - 启动后端:"
echo "  cd \"$(dirname "$0")\""
echo "  python main.py"
echo ""
echo "终端 2 - 启动前端:"
echo "  cd \"$(dirname "$0")/frontend\""
echo "  yarn dev"
echo ""
echo "终端 3 - 打开浏览器:"
echo "  http://localhost:5173"
echo ""
echo "=== 验证清单 ==="
echo "□ 后端运行在 http://localhost:36163"
echo "□ 前端运行在 http://localhost:5173"
echo "□ 页面正常加载"
echo "□ TitleBar 窗口控制按钮隐藏"
echo "□ 浏览器控制台无 Electron API 错误"
echo "□ localStorage 配置已保存"
echo ""
echo "详细检查清单见: docs-AI/web-validation-checklist.md"

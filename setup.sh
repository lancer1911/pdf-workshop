#!/usr/bin/env bash
# 在 pdf_workshop 目录下创建 venv 并安装依赖（macOS / Linux）
# 用法： bash setup.sh
set -e
cd "$(dirname "$0")"

echo "==> 创建虚拟环境 venv/ ..."
python3 -m venv venv

echo "==> 升级 pip ..."
./venv/bin/python -m pip install --upgrade pip

echo "==> 安装依赖 ..."
./venv/bin/python -m pip install -U -r requirements.txt

# Linux 下 pywebview 需要 GUI 后端，尝试安装 Qt 后端（失败不致命）
if [[ "$(uname)" == "Linux" ]]; then
  echo "==> 检测到 Linux，安装 pywebview Qt 后端 ..."
  ./venv/bin/python -m pip install "pywebview[qt]" || \
    echo "   (Qt 后端安装失败，可改用 GTK：pip install pywebview[gtk] 并安装系统库)"
fi

echo ""
echo "完成 ✓  运行方式："
echo "  ./venv/bin/python app.py        # 直接运行"
echo "或先激活环境再运行："
echo "  source venv/bin/activate"
echo "  python app.py"

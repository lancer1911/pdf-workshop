# PDF Workshop —— 环境搭建说明

## 关于虚拟环境（重要）

虚拟环境（venv）**不能跨电脑或跨系统拷贝**——它内部写死了创建时的绝对路径和当前平台的二进制文件。因此压缩包里**不包含**建好的 venv，而是给你一个一键脚本，让你在**自己的机器上**生成。这样才能保证可用。

## 一键搭建

把 `pdf_workshop` 文件夹解压到任意位置，然后：

### macOS / Linux

```bash
cd pdf_workshop
bash setup.sh
```

### Windows

双击 `setup.bat`，或在命令行：

```bat
cd pdf_workshop
setup.bat
```

脚本会在 `pdf_workshop/venv/` 下创建虚拟环境并安装 `requirements.txt` 里的依赖（pywebview、pikepdf、pypdf）。

## 运行

搭建完成后，可直接用 venv 里的解释器运行，不必每次激活：

```bash
# macOS / Linux
./venv/bin/python app.py

# Windows
venv\Scripts\python.exe app.py
```

或先激活环境：

```bash
# macOS / Linux
source venv/bin/activate
python app.py

# Windows
venv\Scripts\activate
python app.py
```

调试模式（打开开发者工具）：在命令后加 `--debug`。

## 手动搭建（如不想用脚本）

```bash
cd pdf_workshop
python3 -m venv venv

# 激活
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows

pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## 各平台的 GUI 后端

pywebview 依赖系统的网页渲染后端：

- **Windows**：使用系统自带的 Edge WebView2（Win10/11 通常已内置），无需额外操作。
- **macOS**：使用系统自带的 WebKit，无需额外操作。
- **Linux**：需要额外后端。`setup.sh` 会自动尝试安装 Qt 后端（`pywebview[qt]`）。若失败，可改用 GTK：
  ```bash
  pip install pywebview[gtk]
  # 并安装系统库，例如 Debian/Ubuntu：
  sudo apt install python3-gi gir1.2-webkit2-4.1
  ```

## 目录结构

```
pdf_workshop/
├── app.py            # pywebview 窗口 + PDF 后端逻辑
├── web/
│   └── index.html    # 前端界面
├── requirements.txt  # 依赖清单
├── setup.sh          # macOS/Linux 一键搭建 venv
├── setup.bat         # Windows 一键搭建 venv
├── .gitignore
├── README.md         # 功能与用法说明
└── SETUP.md          # 本文件
```

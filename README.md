# LANCER1911 PDF Workshop

**LANCER1911 PDF Workshop** 是一个基于 **pywebview + Python** 的跨平台桌面 PDF 工具，面向日常专利/法律文档处理场景，提供 PDF 解除限制、合并、拆分、预览、书签补全、页码添加和日志排查等功能。

当前版本：**v0.1w**

---

## 主要功能

| 功能 | 说明 | 输出位置 |
|---|---|---|
| **解除限制** | 移除 PDF 的复制、打印、编辑等权限限制；普通权限限制会自动解除 | 系统“下载”目录 |
| **合并 PDF** | 多个 PDF 拖入后排序合并；支持拖动排序、点击编序、自动补书签、可选添加红色页码 | 系统“下载”目录 |
| **拆分 PDF** | 单个 PDF 左侧预览，右侧填写任意页码范围，自动生成多个 PDF | 系统“下载”目录 |
| **PDF 预览** | 拆分页内置页面图片预览，支持上一页/下一页和滚轮翻页 | 界面内显示 |
| **日志查看** | 内置日志窗口，可刷新、复制、打开日志文件夹、清空日志 | 应用日志目录 |
| **跨平台打包** | 支持 macOS `.app` / `.dmg` 和 Windows `.exe` 打包准备 | `dist/` |

---

## 界面与文件处理逻辑

### 解除限制

拖入或选择任意数量的 PDF 后，点击 **解除限制**。

处理结果默认保存为：

```text
原文件名-decrypted.pdf
```

说明：

- 对于仅设置了复制、打印、编辑限制的 PDF，可直接解除；
- 对于设置了“打开密码”的 PDF，仍需先提供正确密码；
- 输出文件若重名，会自动追加 ` (1)`、` (2)`，避免覆盖已有文件。

### 合并 PDF

拖入至少两个 PDF 后，可以通过以下方式控制合并顺序：

1. 拖动每行左侧的拖动手柄；
2. 点击每行右侧的编序框，按点击顺序生成 `1、2、3...`；
3. 如果不使用编序，则按当前列表顺序合并；
4. 如果只给部分文件编序，程序会提示补全编序或清空编序。

合并输出默认保存为：

```text
首个文件名-merged.pdf
```

合并时会自动处理：

- **合并前自动解密**：先把输入 PDF 转换为无权限限制的临时副本，再合并；
- **书签保留与补全**：
  - 原 PDF 有书签：保留原书签；
  - 原 PDF 没有书签：自动使用原文件名添加顶层书签，指向该文件在合并后 PDF 中的首页；
- **添加页码**：勾选“添加页码”后，在合并后的 PDF 每页底部居中添加红色页码，按照合并后的页面顺序连续编号。

### 拆分 PDF

拆分页只允许选择一个 PDF。选择后：

- 左侧显示 PDF 页面预览；
- 右侧显示拆分表格；
- 默认第一行显示 `1-2`，下方始终保留一个空白行；
- 在最后空白行输入内容后，会自动增加下一空白行；
- 如果删空倒数第 2 行，该行会自动删除，从而始终只保留一个末尾空白行。

页码范围支持：

```text
1-2
3-4
8
10-12
```

填写顺序可以任意，例如先写 `3-4`，再写 `1-2` 也可以。

输出命名规则：

- 如果填写了“文件名”，输出为：

```text
用户填写的文件名.pdf
```

- 如果文件名为空，输出为：

```text
原文件名-页码范围.pdf
```

拆分时也会在处理前自动解密，拆分结果默认保存为无权限限制的 PDF。

---

## 安装与源码运行

### macOS

```bash
cd pdf_workshop
chmod +x setup.sh
./setup.sh
./venv/bin/python app.py
```

调试模式：

```bash
./venv/bin/python app.py --debug
```

### Windows 10/11 64-bit

推荐环境：

- Windows 11 64-bit；
- Python 3.11 或 3.12 x64；
- Microsoft Edge WebView2 Runtime；
- Microsoft Visual C++ Redistributable 2015-2022 x64。

首次运行：

```bat
cd pdf_workshop
setup.bat
start_windows.bat
```

如果旧虚拟环境损坏、依赖缺失，或出现 `proxy_tools` / `pywebview` 相关错误：

```bat
repair_windows_venv.bat
```

手动重建虚拟环境：

```bat
cd pdf_workshop
deactivate
rmdir /s /q venv
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install -U pip setuptools wheel
python -m pip install --no-cache-dir -U -r requirements.txt
python app.py
```

如果没有 Python 3.12，可改用：

```bat
py -3.11 -m venv venv
```

---

## 依赖

核心依赖：

```text
pywebview
proxy_tools
bottle
typing_extensions
pythonnet / clr-loader    # Windows GUI 后端相关
pikepdf                   # PDF 解密/权限清洗
pypdf                     # PDF 合并/拆分基础处理
pymupdf                   # PDF 页面预览、页码和书签后处理
pyinstaller               # 打包 app/exe 时使用
```

安装：

```bash
python -m pip install -U -r requirements.txt
```

---

## 打包

详细说明见：

```text
BUILD.md
```

### Windows 生成 `.exe`

```bat
cd pdf_workshop
build_windows_exe.bat
```

输出：

```text
dist\LANCER1911-PDF-Workshop.exe
dist\LANCER1911-PDF-Workshop-Windows.zip
```

### macOS 生成 `.app`

```bash
cd pdf_workshop
chmod +x build_macos_app.sh
./build_macos_app.sh
```

输出：

```text
dist/LANCER1911 PDF Workshop.app
dist/LANCER1911 PDF Workshop-macOS.zip
```

### macOS 生成 `.dmg`

先生成 `.app`，然后运行：

```bash
cd pdf_workshop
chmod +x build_macos_dmg.sh
./build_macos_dmg.sh
```

输出：

```text
dist/LANCER1911-PDF-Workshop-macOS.dmg
```

DMG 内包含：

```text
LANCER1911 PDF Workshop.app
Applications -> /Applications
```

用户打开 DMG 后，可将 App 拖入 Applications 文件夹。

---

## 图标与 DMG 资源

项目内包含应用图标：

```text
assets/app.icns   # macOS App 图标
assets/app.ico    # Windows exe 图标
```

打包脚本会自动使用上述图标。

如需自定义 DMG 背景，可将背景图放入 `assets/`，并在 `build_macos_dmg.sh` 中配置对应路径。

---

## 日志

程序内置日志窗口，顶部图标按钮支持：

- 清空日志；
- 刷新日志；
- 打开日志文件夹；
- 复制全部日志；
- 关闭日志窗口。

源码运行时日志默认位置：

```text
pdf_workshop/logs/pdf_workshop.log
```

打包后日志位置：

```text
macOS: ~/Library/Logs/LANCER1911 PDF Workshop/pdf_workshop.log
Windows: %LOCALAPPDATA%\LANCER1911 PDF Workshop\logs\pdf_workshop.log
```

---

## 项目结构

```text
pdf_workshop/
├── app.py                         # pywebview 窗口与 PDF 后端逻辑
├── web/
│   └── index.html                 # 前端界面
├── assets/
│   ├── app.icns                   # macOS 图标
│   ├── app.ico                    # Windows 图标
│   └── app_icon_1024.png          # 图标源图
├── setup.sh                       # macOS/Linux 源码运行环境安装
├── setup.bat                      # Windows 源码运行环境安装/修复
├── repair_windows_venv.bat        # Windows 虚拟环境强修复
├── start_windows.bat              # Windows 启动脚本
├── build_macos_app.sh             # macOS .app 打包
├── build_macos_dmg.sh             # macOS .dmg 打包
├── build_windows_exe.bat          # Windows .exe 打包
├── build_windows_exe.ps1          # Windows PowerShell 打包
├── BUILD.md                       # 打包说明
├── RELEASE_NOTES_0.1w.md          # v0.1w 发布说明
├── requirements.txt
└── README.md
```

---

## 版本摘要

### v0.1w

- 替换新的 macOS / Windows 应用图标；
- 修复 Windows `setup.bat`，增强虚拟环境创建、依赖安装和依赖验证；
- 增加 macOS DMG 打包准备脚本；
- 更新打包说明；
- 保留 v0.1s-v0.1v 中的 PDF 合并、拆分、自动解密、书签补全、页码添加、预览、日志和图标相关改进。


# LANCER1911 PDF Workshop 打包说明

由于 PyInstaller 不能可靠跨平台编译，macOS 的 `.app` / `.dmg` 需要在 macOS 上构建，Windows 的 `.exe` 需要在 Windows 上构建。

## 一、源码运行

### macOS

```bash
cd pdf_workshop
chmod +x setup.sh
./setup.sh
./venv/bin/python app.py
```

### Windows 10/11 64-bit

推荐 Python 3.11 或 3.12 x64。第一次运行：

```bat
cd pdf_workshop
setup.bat
start_windows.bat
```

如果旧虚拟环境损坏或缺依赖：

```bat
repair_windows_venv.bat
```

`setup.bat` 会优先寻找 `py -3.12`、`py -3.11`、`py -3.10`，并自动安装/验证 `proxy_tools`、`pywebview`、`pymupdf`、`pikepdf`、`pypdf` 等依赖。

## 二、Windows 生成 `.exe`

在 Windows 终端或 PowerShell 中进入项目目录：

```bat
cd pdf_workshop
build_windows_exe.bat
```

或使用 PowerShell：

```powershell
cd pdf_workshop
powershell -ExecutionPolicy Bypass -File .\build_windows_exe.ps1
```

输出：

```text
dist\LANCER1911-PDF-Workshop.exe
dist\LANCER1911-PDF-Workshop-Windows.zip
```

## 三、macOS 生成 `.app`

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

第一次打开如果提示未验证开发者，可在 Finder 中右键该 App，选择“打开”。

## 四、macOS 生成 `.dmg`

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

该 DMG 会包含：

```text
LANCER1911 PDF Workshop.app
Applications -> /Applications
```

因此用户打开 DMG 后，可以把 App 拖到 Applications。

注意：该脚本只负责打包 DMG，不负责 Apple Developer ID 签名和 notarization。正式分发时建议另行 codesign / notarize。

## 五、应用图标

项目内包含应用图标：

```text
assets/app.icns   # macOS .app / .dmg 中 App 图标
assets/app.ico    # Windows .exe 图标
```

打包脚本已经自动使用这些图标：

- macOS: `build_macos_app.sh` 使用 `--icon assets/app.icns`
- Windows: `build_windows_exe.bat` / `build_windows_exe.ps1` 使用 `--icon assets\app.ico`

Windows 如果旧 exe 图标没有立刻刷新，通常是资源管理器图标缓存导致，可以换一个输出文件名、重启资源管理器，或清理 Windows 图标缓存后再查看。

## 六、日志位置

源码运行日志默认在：

```text
pdf_workshop/logs/pdf_workshop.log
```

打包后日志位置：

```text
macOS: ~/Library/Logs/LANCER1911 PDF Workshop/pdf_workshop.log
Windows: %LOCALAPPDATA%\LANCER1911 PDF Workshop\logs\pdf_workshop.log
```

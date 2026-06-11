#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 工坊 —— 基于 pywebview 的桌面 PDF 工具
功能：解除限制（pikepdf）/ 合并 / 拆分
运行：python app.py
依赖：pip install pywebview pikepdf pypdf pymupdf
"""
import io
import os
import re
import base64
import tempfile
import sys
import platform
import functools
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pikepdf
from pypdf import PdfReader, PdfWriter

try:
    import fitz  # PyMuPDF 传统导入名，用于稳定渲染拆分预览页
except Exception:
    try:
        import pymupdf as fitz  # PyMuPDF 新导入名，兼容部分环境
    except Exception:
        fitz = None

import webview

# 资源目录 / 程序目录
# 普通源码运行时，二者相同；PyInstaller 打包后，web 等资源在 _MEIPASS，
# 日志等可写文件则放到用户目录，避免写入 .app / .exe 所在目录失败。
if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    APP_DIR = Path(sys.executable).resolve().parent
else:
    RESOURCE_DIR = Path(__file__).resolve().parent
    APP_DIR = RESOURCE_DIR

DOWNLOADS = Path.home() / "Downloads"
DROP_DIR = Path(tempfile.gettempdir()) / "pdf_workshop_dropped"

# ---------------------------------------------------------------- 日志
# 写到 logs/pdf_workshop.log（滚动保留几份），同时输出到终端。
# Python 异常、未捕获异常、前端 JS 报错都会进这个文件，可在界面里查看/复制。
DROP_DIR.mkdir(parents=True, exist_ok=True)

if getattr(sys, "frozen", False):
    if platform.system() == "Darwin":
        LOG_DIR = Path.home() / "Library" / "Logs" / "LANCER1911 PDF Workshop"
    elif platform.system() == "Windows":
        LOG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LANCER1911 PDF Workshop" / "logs"
    else:
        LOG_DIR = Path.home() / ".lancer1911-pdf-workshop" / "logs"
else:
    LOG_DIR = APP_DIR / "logs"
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIR / "pdf_workshop.log"
except Exception:
    # 万一日志目录不可写，退回到下载目录
    LOG_DIR = DOWNLOADS
    LOG_FILE = DOWNLOADS / "pdf_workshop.log"

logger = logging.getLogger("pdf_workshop")
logger.setLevel(logging.DEBUG)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
_fh = RotatingFileHandler(LOG_FILE, maxBytes=512 * 1024, backupCount=3, encoding="utf-8")
_fh.setFormatter(_fmt)
_sh = logging.StreamHandler()       # 从终端启动时也能看到
_sh.setFormatter(_fmt)
logger.addHandler(_fh)
logger.addHandler(_sh)


def _excepthook(exc_type, exc, tb):
    logger.error("未捕获的异常", exc_info=(exc_type, exc, tb))
    sys.__excepthook__(exc_type, exc, tb)


sys.excepthook = _excepthook
logger.info("=" * 60)
logger.info("LANCER1911 PDF Workshop 启动  平台=%s  Python=%s", platform.system(), platform.python_version())
logger.info("日志文件：%s", LOG_FILE)


def logged(fn):
    """装饰 API 方法：记录调用与异常的完整堆栈到日志。"""
    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        logger.info("调用 %s()", fn.__name__)
        try:
            return fn(*args, **kwargs)
        except Exception:
            logger.exception("%s() 抛出异常", fn.__name__)
            raise
    return wrap


# ---------------------------------------------------------------- 工具函数

def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n} B"


def unique_path(p: Path) -> Path:
    """若文件已存在，自动追加 (1)、(2)…"""
    if not p.exists():
        return p
    stem, suffix = p.stem, p.suffix
    i = 1
    while True:
        cand = p.with_name(f"{stem} ({i}){suffix}")
        if not cand.exists():
            return cand
        i += 1


def sanitize(name: str) -> str:
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/:*?"<>|\r\n]+', "_", name).strip() or "untitled"


def parse_range(text: str, page_count: int):
    """把 '1-5, 8, 10-12' 解析为零起始页码列表（保持书写顺序）"""
    pages = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a > b:
                a, b = b, a
            span = range(a, b + 1)
        elif part.isdigit():
            span = [int(part)]
        else:
            raise ValueError(f"无法识别的范围写法：{part}")
        for p in span:
            if p < 1 or p > page_count:
                raise ValueError(f"页码 {p} 超出范围（该文件共 {page_count} 页）")
            pages.append(p - 1)
    if not pages:
        raise ValueError("页码范围为空")
    return pages


def open_unrestricted(path: str, password: str = "") -> io.BytesIO:
    """用 pikepdf 打开并去掉加密/限制，返回内存中的干净副本，供 pypdf 使用"""
    buf = io.BytesIO()
    with pikepdf.open(path, password=password or "") as pdf:
        pdf.save(buf)
    buf.seek(0)
    return buf


def save_unrestricted_copy(src: str, dst: Path, password: str = "") -> Path:
    """把 PDF 显式另存为无加密/无限制副本。

    合并、拆分、加页码之前都先走这里，避免权限加密或安全标记影响
    pypdf/PyMuPDF 后续处理。若 PDF 需要“打开密码”，仍会抛出 PasswordError。
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    with pikepdf.open(src, password=password or "") as pdf:
        pdf.save(dst)
    return dst


def has_outline(reader: PdfReader) -> bool:
    """判断 PDF 是否已有书签/大纲。pypdf 对不同 PDF 可能返回空列表或抛异常。"""
    try:
        return bool(getattr(reader, "outline", None))
    except Exception:
        return False


def finalize_pdf_with_bookmarks_and_page_numbers(
    src: Path,
    dst: Path,
    add_page_numbers: bool = False,
    bookmarks_to_add=None,
):
    """保存最终 PDF，并可补充文件名书签、添加红色页码。

    之前的实现把文件名书签交给 pypdf.append(outline_item=...)，
    页码则在后续 PyMuPDF 保存步骤中处理。不同 pypdf/PyMuPDF 组合下，
    书签和页码有可能没有稳定落到最终文件。这里统一在最终保存前用
    PyMuPDF 对最终文件进行一次显式处理：
    - 先读取已有 TOC；
    - 对原本无书签的源 PDF，补充顶层文件名书签；
    - 勾选时在每页底部居中添加红色页码；
    - 最后只保存一次，确保这些修改真正写进最终输出 PDF。
    """
    bookmarks_to_add = bookmarks_to_add or []
    if not add_page_numbers and not bookmarks_to_add:
        with open(src, "rb") as s, open(dst, "wb") as d:
            d.write(s.read())
        return

    if fitz is None:
        raise RuntimeError("缺少 PyMuPDF 依赖，请运行：./venv/bin/python -m pip install -U pymupdf 或 ./venv/bin/python -m pip install -U -r requirements.txt")

    doc = fitz.open(str(src))
    try:
        if add_page_numbers:
            for i, page in enumerate(doc, start=1):
                # 直接在最终 PDF 页面上写红色页码。
                # v0.1r 使用 insert_textbox 居中，在部分 PDF / 阅读器组合下可能
                # 因页面 CropBox、旋转或文本框适配问题看不到。这里改为：
                # 1) 先 wrap_contents，确保新增内容覆盖在原内容之上；
                # 2) 用 insert_text 直接写入明确坐标；
                # 3) 按文本实际宽度计算水平居中；
                # 4) 距底边略高，避免落在裁切区外。
                try:
                    page.wrap_contents()
                except Exception:
                    pass
                rect = page.rect
                num_text = str(i)
                font_size = max(22, min(38, rect.width / 18))
                try:
                    text_width = fitz.get_text_length(num_text, fontname="helv", fontsize=font_size)
                except Exception:
                    text_width = len(num_text) * font_size * 0.55
                x = rect.x0 + (rect.width - text_width) / 2
                y = rect.y1 - max(30, font_size * 1.15)
                page.insert_text(
                    fitz.Point(x, y),
                    num_text,
                    fontsize=font_size,
                    fontname="helv",
                    color=(1, 0, 0),
                    overlay=True,
                )

        if bookmarks_to_add:
            toc = doc.get_toc(simple=True) or []
            for page_no, title in bookmarks_to_add:
                page_no = max(1, min(int(page_no), doc.page_count))
                toc.append([1, str(title), page_no])
            toc.sort(key=lambda x: (int(x[2] or 1), int(x[0] or 1), str(x[1])))
            doc.set_toc(toc)

        doc.save(str(dst), garbage=4, deflate=True)
    finally:
        doc.close()


# ---------------------------------------------------------------- JS API

class Api:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    # ---------- 通用 ----------

    def get_env(self):
        return {"downloads": str(DOWNLOADS), "platform": platform.system(),
                "log_file": str(LOG_FILE)}

    @logged
    def pick_files(self, multiple=True):
        """文件选择对话框（拖放之外的备用入口）。

        不同 pywebview / macOS 组合返回值略有差异：可能是字符串、Path，
        也可能是 file:// URL。这里统一转换成后端可直接打开的绝对路径。
        """
        dialog_type = getattr(getattr(webview, "FileDialog", None), "OPEN", webview.OPEN_DIALOG)
        result = self._window.create_file_dialog(
            dialog_type,
            allow_multiple=bool(multiple),
            file_types=("PDF 文件 (*.pdf)",),
        )
        if not result:
            return []
        if isinstance(result, (str, os.PathLike)):
            result = [result]
        paths = []
        for item in result:
            text = str(item)
            if text.startswith("file://"):
                from urllib.parse import unquote, urlparse
                text = unquote(urlparse(text).path)
            # 若 pywebview 返回相对路径，至少按当前工作目录补全；正常情况下应为绝对路径。
            pp = Path(text).expanduser()
            if not pp.is_absolute():
                pp = Path.cwd() / pp
            paths.append(str(pp.resolve()))
        logger.info("pick_files 返回：%s", paths)
        return paths

    @logged
    def save_dropped_file(self, name, data_url):
        """接收前端拖拽文件内容，保存到临时目录并返回真实路径。

        macOS 的 WebView 拖拽事件有时只能拿到文件名，拿不到原始路径；
        因此拖拽入口不再依赖 f.path，而是把 PDF 内容写入临时文件。
        """
        safe_name = sanitize(Path(str(name)).name)
        if not safe_name.lower().endswith(".pdf"):
            safe_name += ".pdf"
        if isinstance(data_url, str) and "," in data_url:
            data_url = data_url.split(",", 1)[1]
        raw = base64.b64decode(data_url or "")
        dst = unique_path(DROP_DIR / safe_name)
        dst.write_bytes(raw)
        logger.info("拖拽文件已保存：%s (%s)", dst, human_size(len(raw)))
        return str(dst.resolve())

    @logged
    def get_pdf_data_url(self, path):
        """返回 PDF 的 data URL。保留给旧预览逻辑/备用。"""
        raw = Path(path).read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        return "data:application/pdf;base64," + b64

    def get_pdf_page_image(self, path, page=1, max_px=1800):
        """把 PDF 指定页渲染为 PNG data URL，用于拆分页左侧预览。

        之前用 iframe 直接嵌入 PDF，macOS WebView/Chrome PDF 插件会自行缩放、
        内部滚动，导致页面显示不完整，页码也无法可靠监听。改为后端渲染
        单页图片后，前端只显示一张完整图片，滚轮/按钮翻页由本程序控制。
        """
        if fitz is None:
            return {"ok": False, "error": "缺少 PyMuPDF 依赖，请运行：./venv/bin/python -m pip install -U pymupdf 或 ./venv/bin/python -m pip install -U -r requirements.txt"}
        doc = None
        try:
            page = int(page or 1)
            max_px = int(max_px or 1600)
            if page < 1:
                page = 1

            # 优先直接读取文件字节并用 PyMuPDF 打开；如果遇到权限限制/加密兼容问题，
            # 再用 pikepdf 生成一份内存中的 unrestricted PDF 作为回退。
            try:
                raw_pdf = Path(path).read_bytes()
                doc = fitz.open(stream=raw_pdf, filetype="pdf")
            except Exception:
                if doc is not None:
                    try:
                        doc.close()
                    except Exception:
                        pass
                clean = open_unrestricted(path)
                doc = fitz.open(stream=clean.getvalue(), filetype="pdf")

            total = doc.page_count
            if total < 1:
                return {"ok": False, "error": "PDF 没有可预览页面"}
            if page > total:
                page = total
            pg = doc.load_page(page - 1)
            rect = pg.rect
            longer = max(float(rect.width), float(rect.height), 1.0)
            # 控制输出尺寸，避免 data URL 过大；图片只用于左侧预览，1600px 已足够清晰。
            zoom = max(0.8, min(2.5, max_px / longer))
            pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False, annots=True)
            raw = pix.tobytes("png")
            b64 = base64.b64encode(raw).decode("ascii")
            return {"ok": True, "page": page, "total": total, "data_url": "data:image/png;base64," + b64}
        except Exception as e:
            logger.exception("渲染 PDF 预览失败：%s 第 %s 页", path, page)
            return {"ok": False, "error": str(e)}
        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass

    @logged
    def inspect(self, paths):
        """读取每个 PDF 的页数 / 大小 / 加密状态"""
        out = []
        for p in paths:
            info = {"path": p, "name": Path(p).name, "pages": None,
                    "size": "", "encrypted": False, "locked": False, "error": ""}
            try:
                info["size"] = human_size(os.path.getsize(p))
                try:
                    with pikepdf.open(p) as pdf:
                        info["pages"] = len(pdf.pages)
                        info["encrypted"] = pdf.is_encrypted
                except pikepdf.PasswordError:
                    info["locked"] = True   # 需要打开密码
                    info["encrypted"] = True
            except Exception as e:
                info["error"] = str(e)
                logger.exception("inspect 读取失败：%s", p)
            out.append(info)
        return out

    @logged
    def open_downloads(self):
        return self._open_in_os(DOWNLOADS)

    # ---------- 日志相关 ----------

    def _open_in_os(self, target: Path):
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(str(target))  # type: ignore[attr-defined]
            elif system == "Darwin":
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
            return {"ok": True}
        except Exception as e:
            logger.exception("打开失败：%s", target)
            return {"ok": False, "error": str(e)}

    def open_logs(self):
        """在系统文件管理器中打开日志文件所在文件夹"""
        return self._open_in_os(LOG_FILE.parent)

    def read_log(self, max_chars=60000):
        """返回日志文件末尾内容，供界面内查看 / 复制"""
        try:
            if not LOG_FILE.exists():
                return {"ok": True, "text": "(日志文件还是空的)", "path": str(LOG_FILE)}
            data = LOG_FILE.read_text(encoding="utf-8", errors="replace")
            if len(data) > max_chars:
                data = "…（仅显示末尾部分）\n" + data[-max_chars:]
            return {"ok": True, "text": data, "path": str(LOG_FILE)}
        except Exception as e:
            logger.exception("读取日志失败")
            return {"ok": False, "error": str(e), "path": str(LOG_FILE)}

    def clear_log(self):
        """清空当前日志文件，并保持日志查看窗口可继续读取。"""
        try:
            for h in logger.handlers:
                try:
                    h.flush()
                except Exception:
                    pass
            # 直接截断当前日志文件；不记录本次调用，避免清空后又马上产生新日志。
            with open(LOG_FILE, "w", encoding="utf-8"):
                pass
            return {"ok": True, "text": "", "path": str(LOG_FILE)}
        except Exception as e:
            logger.exception("清空日志失败")
            return {"ok": False, "error": str(e), "path": str(LOG_FILE)}

    def log_js_error(self, message):
        """前端把 JS 报错转发到这里，统一写进日志"""
        logger.error("[前端] %s", message)
        return {"ok": True}

    # ---------- 功能 1：解除限制 ----------

    @logged
    def unlock(self, paths, password=""):
        DOWNLOADS.mkdir(parents=True, exist_ok=True)
        results = []
        for p in paths:
            name = Path(p).name
            try:
                dst = unique_path(DOWNLOADS / f"{Path(p).stem}-decrypted.pdf")
                with pikepdf.open(p, password=password or "") as pdf:
                    # 不带 encryption 参数保存 => 移除全部加密与权限限制
                    pdf.save(dst)
                results.append({"name": name, "ok": True, "output": dst.name})
                logger.info("解除限制成功：%s -> %s", name, dst.name)
            except pikepdf.PasswordError:
                results.append({"name": name, "ok": False,
                                "error": "需要打开密码（密码不正确或未填写）"})
                logger.warning("解除限制失败（需密码）：%s", name)
            except Exception as e:
                results.append({"name": name, "ok": False, "error": str(e)})
                logger.exception("解除限制失败：%s", name)
        return results

    # ---------- 功能 2：合并 ----------

    @logged
    def merge(self, paths, add_page_numbers=False):
        try:
            if len(paths) < 2:
                return {"ok": False, "error": "至少需要两个 PDF 才能合并"}
            DOWNLOADS.mkdir(parents=True, exist_ok=True)
            writer = PdfWriter()
            bookmarks_to_add = []
            added_name_bookmarks = 0
            current_page = 0

            # 先把所有输入 PDF 显式转换为无加密/无限制临时副本，再进行合并。
            # 对“无原书签”的 PDF，不再依赖 pypdf.append(outline_item=...)；
            # 而是在最终输出前用 PyMuPDF set_toc() 显式写入文件名书签，
            # 避免后续清洗/加页码步骤覆盖书签。
            with tempfile.TemporaryDirectory(prefix="pdf_workshop_merge_") as td:
                tmpdir = Path(td)
                clean_paths = []
                for idx, p in enumerate(paths, start=1):
                    clean = tmpdir / f"input-{idx}.pdf"
                    save_unrestricted_copy(p, clean)
                    clean_paths.append((p, clean))

                for original_path, clean_path in clean_paths:
                    reader = PdfReader(str(clean_path))
                    page_count = len(reader.pages)
                    if has_outline(reader):
                        # 源 PDF 已有书签：原样导入，不额外套一层文件名。
                        writer.append(reader, import_outline=True)
                    else:
                        # 源 PDF 没有书签：记录该文件在合并后 PDF 中的首页，
                        # 最终保存前统一补一个顶层文件名书签。
                        writer.append(reader, import_outline=False)
                        bookmarks_to_add.append((current_page + 1, Path(original_path).stem))
                        added_name_bookmarks += 1
                    current_page += page_count

                dst = unique_path(DOWNLOADS / f"{Path(paths[0]).stem}-merged.pdf")
                merged_clean = tmpdir / "merged-unrestricted.pdf"
                with open(merged_clean, "wb") as f:
                    writer.write(f)

                finalize_pdf_with_bookmarks_and_page_numbers(
                    merged_clean,
                    dst,
                    add_page_numbers=bool(add_page_numbers),
                    bookmarks_to_add=bookmarks_to_add,
                )

            logger.info(
                "合并成功：%d 个文件 -> %s；输入已自动解密；补充文件名书签 %d 个；添加页码=%s",
                len(paths), dst.name, added_name_bookmarks, bool(add_page_numbers)
            )
            return {"ok": True, "output": dst.name}
        except pikepdf.PasswordError:
            return {"ok": False, "error": "列表中有文件需要打开密码；权限加密会自动解除，但打开密码仍需先在“解除限制”中填写密码处理"}
        except Exception as e:
            logger.exception("合并失败")
            return {"ok": False, "error": str(e)}

    # ---------- 功能 3：拆分 ----------

    @logged
    def split(self, path, ranges):
        """
        ranges: [{ "range": "1-5", "filename": "第一部分" }, ...]
        每条范围输出一个文件。filename 仅用于输出文件名；不填写时使用：原文件名-页码范围.pdf。
        默认保留原 PDF 中与拆分页相关的书签。
        """
        results = []
        try:
            DOWNLOADS.mkdir(parents=True, exist_ok=True)
            stem = Path(path).stem

            # 拆分前同样先生成无加密/无限制副本；所有拆分结果也再经 pikepdf 清洗后输出。
            with tempfile.TemporaryDirectory(prefix="pdf_workshop_split_") as td:
                tmpdir = Path(td)
                clean_src = save_unrestricted_copy(path, tmpdir / "source-unrestricted.pdf")
                reader = PdfReader(str(clean_src))
                total = len(reader.pages)

                for i, item in enumerate(ranges, start=1):
                    rng_text = (item.get("range") or "").strip()
                    filename = (item.get("filename") or item.get("label") or "").strip()
                    try:
                        pages = parse_range(rng_text, total)
                        writer = PdfWriter()
                        writer.append(
                            reader,
                            pages=pages,
                            import_outline=True,
                        )
                        if filename:
                            out_name = sanitize(filename)
                        else:
                            out_name = f"{stem}-{sanitize(rng_text.replace(' ', ''))}"
                        if not out_name.lower().endswith(".pdf"):
                            out_name += ".pdf"
                        dst = unique_path(DOWNLOADS / out_name)
                        tmp_out = tmpdir / f"split-{i}.pdf"
                        with open(tmp_out, "wb") as f:
                            writer.write(f)
                        save_unrestricted_copy(str(tmp_out), dst)
                        results.append({"range": rng_text, "ok": True, "output": dst.name})
                        logger.info("拆分成功：%s -> %s（已自动解密）", rng_text, dst.name)
                    except Exception as e:
                        results.append({"range": rng_text or f"范围 {i}", "ok": False,
                                        "error": str(e)})
                        logger.exception("拆分某段失败：%s", rng_text or f"范围 {i}")
            return {"ok": True, "results": results}
        except pikepdf.PasswordError:
            return {"ok": False, "error": "该文件需要打开密码；权限加密会自动解除，但打开密码仍需先在“解除限制”中填写密码处理"}
        except Exception as e:
            logger.exception("拆分失败")
            return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------- 启动

def main():
    api = Api()
    window = webview.create_window(
        title="LANCER1911 PDF Workshop",
        url=str(RESOURCE_DIR / "web" / "index.html"),
        js_api=api,
        width=1020,
        height=720,
        min_size=(860, 600),
        background_color="#14161B",
    )
    api.set_window(window)
    debug = "--debug" in sys.argv
    logger.info("打开窗口（debug=%s）", debug)
    webview.start(debug=debug)
    logger.info("窗口已关闭，程序退出")


if __name__ == "__main__":
    main()

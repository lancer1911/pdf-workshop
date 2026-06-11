#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包 pdf_workshop 为 pdf_workshop-v0.1<字母>.zip
每次运行自动把字母版本号 +1（a -> b -> c ... -> z -> aa）。
版本号记录在 VERSION 文件中。
排除：venv、__pycache__、*.pyc、.zip、.git 等。

用法： python pack.py
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION_FILE = ROOT / "VERSION"
BASE = "0.1"                      # 数字主版本，按需手动修改
EXCLUDE_DIRS = {"venv", ".venv", "__pycache__", ".git"}
EXCLUDE_SUFFIX = {".pyc", ".zip"}
EXCLUDE_NAMES = {".DS_Store"}


def next_letter(s: str) -> str:
    """a->b, z->aa, az->ba（类似 Excel 列号的进位）"""
    chars = list(s)
    i = len(chars) - 1
    while i >= 0:
        if chars[i] != "z":
            chars[i] = chr(ord(chars[i]) + 1)
            return "".join(chars)
        chars[i] = "a"
        i -= 1
    return "a" + "".join(chars)


def read_and_bump() -> str:
    """读取当前字母版本，返回本次应使用的版本并写回递增后的值。"""
    if VERSION_FILE.exists():
        cur = VERSION_FILE.read_text().strip() or "a"
    else:
        cur = "a"          # 首次打包为 a
    VERSION_FILE.write_text(cur)   # 确保存在
    return cur


def bump_after(cur: str):
    VERSION_FILE.write_text(next_letter(cur))


def should_skip(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    if path.suffix in EXCLUDE_SUFFIX:
        return True
    if path.name in EXCLUDE_NAMES:
        return True
    return False


def main():
    letter = read_and_bump()
    version = f"v{BASE}{letter}"
    zip_name = f"pdf_workshop-{version}.zip"
    zip_path = ROOT.parent / zip_name

    if zip_path.exists():
        zip_path.unlink()

    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(ROOT.rglob("*")):
            if f.is_dir() or should_skip(f.relative_to(ROOT)):
                continue
            # pack.py 与 VERSION 一并打包，便于你在自己机器上续号重打
            arcname = Path("pdf_workshop") / f.relative_to(ROOT)
            zf.write(f, arcname)
            count += 1

    bump_after(letter)
    print(f"已打包 {count} 个文件 -> {zip_path}")
    print(f"本次版本：{version}    下次版本：v{BASE}{next_letter(letter)}")


if __name__ == "__main__":
    main()

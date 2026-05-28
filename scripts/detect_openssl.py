#!/usr/bin/env python3
"""
通用 OpenSSL 检测脚本

按优先级自动检测系统中可用的 OpenSSL 安装位置，输出 Cargo 编译所需的环境变量。
避免 openssl-sys crate 从源码编译 OpenSSL（需要 perl FindBin 等依赖）。

查找优先级:
  1. 用户已设置的 OPENSSL_DIR 环境变量（最高优先级，尊重用户配置）
  2. pkg-config 检测系统标准 OpenSSL
  3. 常见系统路径:
     Linux:  /usr, /usr/local
     macOS:  /opt/homebrew/opt/openssl@3, /usr/local/opt/openssl@3 (Homebrew)
  4. Conda 环境（$CONDA_PREFIX）
  5. Python 虚拟环境（基于 sys.prefix）

用法:
  # 1) 在 shell 中 eval 输出，导出环境变量
  eval $(python3 scripts/detect_openssl.py --shell)
  cargo build ...

  # 2) 或在 Makefile 中作为前缀使用
  $(shell python3 scripts/detect_openssl.py --shell) cargo build ...

  # 3) 仅打印检测到的路径（用于调试）
  python3 scripts/detect_openssl.py
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


def _has_openssl_headers(prefix: Path) -> bool:
    """检查指定 prefix 下是否有 OpenSSL 头文件和库文件。"""
    if not prefix.is_dir():
        return False
    header = prefix / "include" / "openssl" / "ssl.h"
    if not header.is_file():
        return False
    # 至少要有库文件之一（.so/.dylib/.a/.dll）
    libdir_candidates = [prefix / "lib", prefix / "lib64"]
    lib_patterns = ["libssl.so*", "libssl.dylib", "libssl.a", "libssl*.dll"]
    for libdir in libdir_candidates:
        if not libdir.is_dir():
            continue
        for pattern in lib_patterns:
            if list(libdir.glob(pattern)):
                return True
    return False


def _try_pkg_config() -> Optional[Tuple[str, Optional[str]]]:
    """尝试用 pkg-config 找到 OpenSSL。返回 (OPENSSL_DIR, PKG_CONFIG_PATH)。"""
    if not shutil.which("pkg-config"):
        return None
    try:
        result = subprocess.run(
            ["pkg-config", "--variable=prefix", "openssl"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            prefix = result.stdout.strip()
            if prefix and _has_openssl_headers(Path(prefix)):
                return (prefix, None)
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _try_user_env() -> Optional[Tuple[str, Optional[str]]]:
    """尊重用户已设置的 OPENSSL_DIR。"""
    user_dir = os.environ.get("OPENSSL_DIR", "").strip()
    if user_dir and _has_openssl_headers(Path(user_dir)):
        return (user_dir, os.environ.get("PKG_CONFIG_PATH"))
    return None


def _try_system_paths() -> Optional[Tuple[str, Optional[str]]]:
    """检查常见系统路径。"""
    candidates = []
    system = platform.system()
    if system == "Darwin":
        # macOS: Homebrew 路径优先
        candidates.extend([
            "/opt/homebrew/opt/openssl@3",   # Apple Silicon
            "/opt/homebrew/opt/openssl@1.1",
            "/usr/local/opt/openssl@3",       # Intel Mac
            "/usr/local/opt/openssl@1.1",
        ])
    # Linux 和 macOS 通用
    candidates.extend(["/usr", "/usr/local"])
    for p in candidates:
        path = Path(p)
        if _has_openssl_headers(path):
            pkg_config_path = None
            for sub in ["lib/pkgconfig", "lib64/pkgconfig"]:
                pcdir = path / sub
                if (pcdir / "openssl.pc").is_file():
                    pkg_config_path = str(pcdir)
                    break
            return (str(path), pkg_config_path)
    return None


def _try_conda_env() -> Optional[Tuple[str, Optional[str]]]:
    """检查 conda 环境。"""
    conda_prefix = os.environ.get("CONDA_PREFIX", "").strip()
    if conda_prefix and _has_openssl_headers(Path(conda_prefix)):
        pcdir = Path(conda_prefix) / "lib" / "pkgconfig"
        return (
            conda_prefix,
            str(pcdir) if (pcdir / "openssl.pc").is_file() else None,
        )
    return None


def _try_python_prefix() -> Optional[Tuple[str, Optional[str]]]:
    """检查 Python 解释器所在的 prefix（venv / virtualenv / 系统 Python 都适用）。"""
    prefix = Path(sys.prefix)
    if _has_openssl_headers(prefix):
        pcdir = prefix / "lib" / "pkgconfig"
        return (
            str(prefix),
            str(pcdir) if (pcdir / "openssl.pc").is_file() else None,
        )
    return None


def detect_openssl() -> Optional[Tuple[str, str, Optional[str]]]:
    """
    按优先级查找 OpenSSL，返回 (来源描述, OPENSSL_DIR, PKG_CONFIG_PATH)。
    """
    strategies = [
        ("OPENSSL_DIR (user-provided)", _try_user_env),
        ("pkg-config",                  _try_pkg_config),
        ("system paths",                _try_system_paths),
        ("conda environment",           _try_conda_env),
        ("Python prefix",               _try_python_prefix),
    ]
    for name, fn in strategies:
        result = fn()
        if result is not None:
            openssl_dir, pkg_config_path = result
            return (name, openssl_dir, pkg_config_path)
    return None


def shell_quote(s: str) -> str:
    """简单的 shell 单引号转义。"""
    return "'" + s.replace("'", "'\"'\"'") + "'"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--shell", action="store_true",
                        help="输出可被 shell eval 的 export 语句")
    parser.add_argument("--prefix", action="store_true",
                        help="仅输出检测到的 OPENSSL_DIR")
    args = parser.parse_args()

    found = detect_openssl()
    if found is None:
        # 没找到 OpenSSL: 给出清晰的安装提示并失败
        msg = [
            "Error: 未在系统中找到 OpenSSL 开发文件",
            "",
            "请安装 OpenSSL 开发包后重试:",
            "  Debian/Ubuntu : sudo apt-get install -y libssl-dev pkg-config",
            "  RHEL/CentOS   : sudo yum install -y openssl-devel pkgconfig",
            "  Fedora        : sudo dnf install -y openssl-devel pkgconfig",
            "  Alpine        : apk add --no-cache openssl-dev pkgconf",
            "  macOS         : brew install openssl@3 pkg-config",
            "  Conda         : conda install -c conda-forge openssl pkg-config",
            "",
            "或者手动指定: export OPENSSL_DIR=/path/to/openssl",
        ]
        print("\n".join(msg), file=sys.stderr)
        return 1

    source, openssl_dir, pkg_config_path = found

    if args.prefix:
        print(openssl_dir)
        return 0

    if args.shell:
        # 输出可 eval 的 export 语句
        # 设置 OPENSSL_NO_VENDOR=1 强制使用系统 OpenSSL，避免触发 vendored 编译路径
        lines = [
            f"export OPENSSL_NO_VENDOR=1",
            f"export OPENSSL_DIR={shell_quote(openssl_dir)}",
        ]
        if pkg_config_path:
            existing = os.environ.get("PKG_CONFIG_PATH", "")
            merged = pkg_config_path if not existing else f"{pkg_config_path}:{existing}"
            lines.append(f"export PKG_CONFIG_PATH={shell_quote(merged)}")
        print("\n".join(lines))
        return 0

    # 默认: 人类可读的诊断输出
    print(f"找到 OpenSSL: {openssl_dir}")
    print(f"  来源       : {source}")
    print(f"  OPENSSL_DIR: {openssl_dir}")
    if pkg_config_path:
        print(f"  PKG_CONFIG_PATH: {pkg_config_path}")
    print(f"  OPENSSL_NO_VENDOR=1 (避免从源码编译 OpenSSL)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

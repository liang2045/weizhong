#!/usr/bin/env python3
"""One-click launcher for non-technical users."""

from __future__ import annotations

import socket
import webbrowser
from contextlib import closing

import web_app


def _port_available(host: str, port: int) -> bool:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) != 0


def main() -> None:
    host = "127.0.0.1"
    port = web_app.PORT
    url = f"http://{host}:{port}"

    print("=" * 40)
    print("彩票助手正在启动...")
    print("启动后会自动打开浏览器。")
    print("如果没有自动打开，请手动复制这个地址：")
    print(url)
    print("=" * 40)

    if not _port_available(host, port):
        print(f"端口 {port} 已被占用，可能已有程序在运行。")
        print(f"请直接在浏览器打开：{url}")
        return

    try:
        webbrowser.open(url)
    except Exception:
        pass

    web_app.main()


if __name__ == "__main__":
    main()

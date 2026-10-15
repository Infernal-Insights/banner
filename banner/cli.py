"""Command line for the reference loop."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from banner.roles import demo, status_text
from banner.state import Log


def main(argv: list[str] | None = None) -> None:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data", default="banner-data", help="directory for the local log")

    parser = argparse.ArgumentParser(prog="banner", description="Banner reference loop")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser(
        "demo", parents=[common], help="open a charter, finish every tile, write a mosaic"
    )
    run.add_argument("--grid", type=int, default=2)

    sub.add_parser("status", parents=[common], help="show banners, leases, and sway")

    page = sub.add_parser(
        "serve", parents=[common], help="show status at http://127.0.0.1:8787"
    )
    page.add_argument("--port", type=int, default=8787)

    args = parser.parse_args(argv)
    if args.cmd == "demo":
        log, mosaic = demo(args.data, args.grid)
        print(status_text(log), end="")
        print(f"mosaic   {mosaic}")
    elif args.cmd == "status":
        print(status_text(Log(args.data)), end="")
    elif args.cmd == "serve":
        _serve(Path(args.data), args.port)


def _serve(root: Path, port: int) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = _page(Log(root)).encode()
            self.send_response(200)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"banner status at http://127.0.0.1:{port}")
    server.serve_forever()


def _page(log: Log) -> str:
    blocks = []
    for charter in log.state["charters"].values():
        cid = charter["id"]
        book = log.state["sway"].get(cid) or {}
        rows = "".join(
            f"<li>{_esc(node)} <b>{score}</b></li>"
            for node, score in sorted(book.items(), key=lambda item: -item[1])
        ) or "<li>nobody has finished a tile yet</li>"
        under = [
            node for node, pointed in log.state["allegiance"].items() if pointed == cid
        ]
        blocks.append(
            "<article>"
            f"<p class='flag'>{_esc(charter['name'])}</p>"
            f"<p>{_esc(charter['summary'])}</p>"
            f"<p class='meta'>image {_esc(charter['image'])}"
            f" · under {_esc(', '.join(under) or 'nobody')}</p>"
            f"<ul>{rows}</ul>"
            "</article>"
        )
    body = "\n".join(blocks) or "<p>No charter yet.</p>"
    return (
        "<!doctype html><meta charset=utf-8><title>Banner</title>"
        "<style>"
        "body{margin:0;background:#14120e;color:#efe7d6;font:18px/1.45 Georgia,serif}"
        "main{max-width:36rem;margin:4rem auto;padding:0 1.25rem}"
        ".flag{font-size:2rem;margin:0 0 .25rem}"
        ".meta{color:#b7ab96;font-family:ui-monospace,monospace;font-size:.85rem}"
        "ul{padding-left:1.1rem}"
        "</style>"
        f"<main><p class='meta'>Banner</p>{body}</main>"
    )


def _esc(value: str) -> str:
    amp = "&" + "amp;"
    lt = "&" + "lt;"
    gt = "&" + "gt;"
    quot = "&" + "quot;"
    return (
        value.replace("&", amp)
        .replace("<", lt)
        .replace(">", gt)
        .replace('"', quot)
    )

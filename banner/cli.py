"""Command line for the reference loop."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from banner.roles import (
    attest_all,
    demo,
    ensure_joined,
    open_charter,
    point,
    post_leases,
    status_text,
    work_once,
)
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

    node = sub.add_parser("node", help="create or announce a node key")
    node_sub = node.add_subparsers(dest="node_cmd", required=True)
    created = node_sub.add_parser("new", parents=[common], help="write a private key into the data directory")
    created.add_argument("name")
    joined = node_sub.add_parser("join", parents=[common], help="bind that key to the name in the log")
    joined.add_argument("name")

    charter = sub.add_parser("charter", help="open a banner or post its leases")
    charter_sub = charter.add_subparsers(dest="charter_cmd", required=True)
    opened = charter_sub.add_parser("open", parents=[common])
    opened.add_argument("charter_id")
    opened.add_argument("--node", required=True)
    opened.add_argument("--name", required=True)
    opened.add_argument("--seed", required=True)
    opened.add_argument("--grid", type=int, default=2)
    opened.add_argument("--summary", default="")
    posted = charter_sub.add_parser("post", parents=[common])
    posted.add_argument("charter_id")
    posted.add_argument("--node", required=True)
    posted.add_argument("--verifier", required=True)
    posted.add_argument("--ttl", type=int, default=60)

    pointed = sub.add_parser("point", parents=[common], help="stand a node under one banner")
    pointed.add_argument("node")
    pointed.add_argument("charter_id")

    worked = sub.add_parser("work", parents=[common], help="claim a lease and submit the tile")
    worked.add_argument("node")
    worked.add_argument("--all", action="store_true")

    checked = sub.add_parser("attest", parents=[common], help="recompute submitted tiles")
    checked.add_argument("node")

    args = parser.parse_args(argv)
    data = Path(args.data)
    if args.cmd == "demo":
        log, mosaic = demo(args.data, args.grid)
        print(status_text(log), end="")
        print(f"mosaic   {mosaic}")
    elif args.cmd == "status":
        print(status_text(Log(data)), end="")
    elif args.cmd == "serve":
        _serve(data, args.port)
    elif args.cmd == "node":
        _node(data, args)
    elif args.cmd == "charter":
        _charter(data, args)
    elif args.cmd == "point":
        point(Log(data), args.node, args.charter_id)
        print(f"under    {args.node}  {args.charter_id}")
    elif args.cmd == "work":
        log = Log(data)
        done = 0
        while True:
            lease_id = work_once(log, args.node)
            if lease_id is None:
                break
            done += 1
            print(f"submitted {lease_id}")
            if not args.all:
                break
        if done == 0:
            print("nothing open under this banner")
    elif args.cmd == "attest":
        count = attest_all(Log(data), args.node)
        print(f"checked  {count}")


def _node(data: Path, args: argparse.Namespace) -> None:
    log = Log(data)
    if args.node_cmd == "new":
        pub = log.keys.create(args.name)
        print(f"key      {args.name}")
        print(f"pub      {pub}")
    elif args.node_cmd == "join":
        ensure_joined(log, args.name)
        print(f"joined   {args.name}")


def _charter(data: Path, args: argparse.Namespace) -> None:
    log = Log(data)
    if args.charter_cmd == "open":
        open_charter(
            log,
            args.charter_id,
            args.name,
            args.seed,
            node=args.node,
            grid=args.grid,
            summary=args.summary,
        )
        print(f"opened   {args.charter_id}")
    elif args.charter_cmd == "post":
        posted = post_leases(
            log,
            args.charter_id,
            verifier=args.verifier,
            node=args.node,
            ttl_s=args.ttl,
        )
        print(f"posted   {len(posted)}")


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

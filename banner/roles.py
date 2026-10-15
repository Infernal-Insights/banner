"""Steward, worker, and attestor.

The steward in this cut is a template, not a model. It opens a charter
and posts one lease per tile, naming the attestor before a worker can
claim. The worker only pulls leases for the single banner it is under.
The attestor recomputes the tile and refuses to accept a hash it did
not just produce.
"""

from __future__ import annotations

import time
from pathlib import Path

from banner.state import Log
from banner.tile import IMAGE, SIZE, digest, render


def open_charter(
    log: Log,
    charter_id: str,
    name: str,
    seed: str,
    grid: int = 2,
    summary: str = "",
    at: float | None = None,
) -> dict:
    return log.commit(
        "charter.opened",
        at=at,
        charter_id=charter_id,
        name=name,
        seed=seed,
        grid=grid,
        summary=summary,
        image=IMAGE,
    )


def post_leases(
    log: Log,
    charter_id: str,
    verifier: str,
    ttl_s: int = 60,
    at: float | None = None,
) -> list[dict]:
    charter = log.state["charters"][charter_id]
    posted = []
    for tx in range(charter["grid"]):
        for ty in range(charter["grid"]):
            posted.append(
                log.commit(
                    "lease.posted",
                    at=at,
                    lease_id=f"{charter_id}-{tx}-{ty}",
                    charter_id=charter_id,
                    tx=tx,
                    ty=ty,
                    image=charter["image"],
                    verifier=verifier,
                    ttl_s=ttl_s,
                )
            )
    return posted


def point(log: Log, node: str, charter_id: str, at: float | None = None) -> dict:
    """Stand this node under one banner. Pointing again leaves the previous one."""
    return log.commit("allegiance.set", at=at, node=node, charter_id=charter_id)


def sweep(log: Log, at: float | None = None) -> int:
    now = time.time() if at is None else at
    expired = 0
    for lease in list(log.state["leases"].values()):
        if lease["status"] == "claimed" and now > lease["last_beat"] + lease["ttl_s"]:
            log.commit("lease.expired", at=now, lease_id=lease["id"], node=lease["worker"])
            expired += 1
    return expired


def work_once(log: Log, node: str, at: float | None = None) -> str | None:
    """Claim one open lease under this node's banner and submit its hash."""
    now = time.time() if at is None else at
    sweep(log, now)
    charter_id = log.state["allegiance"].get(node)
    if charter_id is None:
        return None
    for lease in list(log.state["leases"].values()):
        if lease["status"] != "open" or lease["charter_id"] != charter_id:
            continue
        if lease["verifier"] == node:
            continue
        log.commit("lease.claimed", at=now, node=node, lease_id=lease["id"])
        charter = log.state["charters"][charter_id]
        ppm = render(charter["seed"], lease["tx"], lease["ty"])
        log.commit(
            "result.submitted",
            at=now,
            node=node,
            lease_id=lease["id"],
            result_hash=digest(ppm),
        )
        return lease["id"]
    return None


def attest_once(log: Log, node: str, at: float | None = None) -> str | None:
    """Recompute one submitted lease this node was named to verify."""
    now = time.time() if at is None else at
    for lease in list(log.state["leases"].values()):
        if lease["status"] != "submitted" or lease["verifier"] != node:
            continue
        charter = log.state["charters"][lease["charter_id"]]
        got = digest(render(charter["seed"], lease["tx"], lease["ty"]))
        if got == lease["result_hash"]:
            log.commit(
                "result.accepted",
                at=now,
                node=node,
                lease_id=lease["id"],
                result_hash=got,
            )
        else:
            log.commit(
                "result.rejected",
                at=now,
                node=node,
                lease_id=lease["id"],
                result_hash=got,
            )
        return lease["id"]
    return None


def attest_all(log: Log, node: str, at: float | None = None) -> int:
    count = 0
    while attest_once(log, node, at) is not None:
        count += 1
    return count


def stitch(log: Log, charter_id: str, dest: Path | str) -> Path:
    """Write the accepted tiles as one PPM. Missing tiles are black."""
    charter = log.state["charters"][charter_id]
    grid = charter["grid"]
    raw_tiles: dict[tuple[int, int], bytes] = {}
    for lease in log.state["leases"].values():
        if lease["charter_id"] == charter_id and lease["status"] == "accepted":
            ppm = render(charter["seed"], lease["tx"], lease["ty"])
            raw_tiles[(lease["tx"], lease["ty"])] = ppm.split(b"\n255\n", 1)[1]
    width = grid * SIZE
    rows = bytearray()
    for ty in range(grid):
        for py in range(SIZE):
            for tx in range(grid):
                raw = raw_tiles.get((tx, ty))
                if raw is None:
                    rows.extend(bytes(SIZE * 3))
                else:
                    start = py * SIZE * 3
                    rows.extend(raw[start : start + SIZE * 3])
    dest = Path(dest)
    dest.write_bytes(f"P6\n{width} {width}\n255\n".encode() + bytes(rows))
    return dest


def counts(log: Log, charter_id: str) -> dict[str, int]:
    found = {"open": 0, "claimed": 0, "submitted": 0, "accepted": 0}
    for lease in log.state["leases"].values():
        if lease["charter_id"] == charter_id and lease["status"] in found:
            found[lease["status"]] += 1
    return found


def demo(root: Path | str, grid: int = 2) -> tuple[Log, Path]:
    log = Log(root)
    if "reef" not in log.state["charters"]:
        open_charter(
            log,
            "reef",
            "Reef map",
            seed="reef-seed-v1",
            grid=grid,
            summary="A seeded map split into tiles. The picture is the receipt you can see.",
        )
        post_leases(log, "reef", verifier="attestor", ttl_s=60)
        point(log, "worker", "reef")
    while work_once(log, "worker") is not None:
        pass
    attest_all(log, "attestor")
    mosaic = stitch(log, "reef", Path(root) / "reef.ppm")
    return log, mosaic


def status_text(log: Log) -> str:
    if not log.state["charters"]:
        return "no charters yet. run: python -m banner demo"
    lines = []
    for charter in log.state["charters"].values():
        cid = charter["id"]
        done = counts(log, cid)
        lines.append(f"banner   {cid}  {charter['name']}")
        lines.append(f"image    {charter['image']}   grid {charter['grid']}x{charter['grid']}")
        lines.append(
            "leases   "
            + "  ".join(f"{name} {done[name]}" for name in ("open", "claimed", "submitted", "accepted"))
        )
        under = [node for node, pointed in log.state["allegiance"].items() if pointed == cid]
        lines.append("under    " + (", ".join(under) if under else "nobody"))
        book = log.state["sway"].get(cid) or {}
        if book:
            ranked = ", ".join(f"{node} {score}" for node, score in sorted(book.items()))
            lines.append(f"sway     {ranked}")
        else:
            lines.append("sway     none yet")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"

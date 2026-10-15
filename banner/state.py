"""Append-only log. State is always rebuilt from it.

Nothing here transfers sway. Acceptance increments the worker's count
on that charter and no other function writes the counter.
"""

from __future__ import annotations

import copy
import json
import os
import re
import time
from pathlib import Path

from banner.tile import IMAGE

_ID = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
_OPEN = {"open", "claimed", "submitted", "accepted"}


def blank() -> dict:
    return {"seq": 0, "charters": {}, "allegiance": {}, "leases": {}, "sway": {}}


def reduce(state: dict, event: dict) -> dict:
    kind = event["kind"]
    if kind == "charter.opened":
        _open_charter(state, event)
    elif kind == "allegiance.set":
        _set_allegiance(state, event)
    elif kind == "lease.posted":
        _post_lease(state, event)
    elif kind == "lease.claimed":
        _claim(state, event)
    elif kind == "lease.heartbeat":
        lease = _held(state, event)
        lease["last_beat"] = event["at"]
    elif kind == "result.submitted":
        _submit(state, event)
    elif kind == "result.accepted":
        _accept(state, event)
    elif kind == "result.rejected":
        _reject(state, event)
    elif kind == "lease.expired":
        _expire(state, event)
    else:
        raise ValueError(f"unknown event: {kind}")
    state["seq"] = event["seq"]
    return state


def _open_charter(state: dict, event: dict) -> None:
    cid = _ident(event["charter_id"], "charter")
    if cid in state["charters"]:
        raise ValueError(f"charter exists: {cid}")
    if event["image"] != IMAGE:
        raise ValueError(f"unknown image: {event['image']}")
    grid = int(event["grid"])
    if not 1 <= grid <= 16:
        raise ValueError("grid must be from 1 to 16")
    name = str(event["name"]).strip()
    if not name or len(name) > 80:
        raise ValueError("charter name is required")
    seed = str(event["seed"])
    if not seed or len(seed) > 200:
        raise ValueError("seed is required")
    state["charters"][cid] = {
        "id": cid,
        "name": name,
        "summary": str(event.get("summary", ""))[:280],
        "image": event["image"],
        "grid": grid,
        "seed": seed,
    }
    state["sway"][cid] = {}


def _set_allegiance(state: dict, event: dict) -> None:
    node = _ident(event["node"], "node")
    cid = event["charter_id"]
    if cid not in state["charters"]:
        raise ValueError("no such charter")
    state["allegiance"][node] = cid


def _post_lease(state: dict, event: dict) -> None:
    cid = event["charter_id"]
    charter = state["charters"].get(cid)
    if charter is None:
        raise ValueError("no such charter")
    if event["image"] != charter["image"]:
        raise ValueError("image does not match the charter")
    verifier = _ident(event["verifier"], "verifier")
    tx, ty = int(event["tx"]), int(event["ty"])
    if not (0 <= tx < charter["grid"] and 0 <= ty < charter["grid"]):
        raise ValueError("tile is outside the charter grid")
    ttl = int(event["ttl_s"])
    if not 1 <= ttl <= 86400:
        raise ValueError("ttl must be from 1 to 86400 seconds")
    for lease in state["leases"].values():
        if (
            lease["charter_id"] == cid
            and lease["tx"] == tx
            and lease["ty"] == ty
            and lease["status"] in _OPEN
        ):
            raise ValueError(f"tile {tx},{ty} already has a lease")
    lid = event["lease_id"]
    if lid in state["leases"]:
        raise ValueError(f"lease exists: {lid}")
    state["leases"][lid] = {
        "id": lid,
        "charter_id": cid,
        "tx": tx,
        "ty": ty,
        "image": event["image"],
        "verifier": verifier,
        "ttl_s": ttl,
        "status": "open",
        "worker": None,
        "claimed_at": None,
        "last_beat": None,
        "result_hash": None,
    }


def _claim(state: dict, event: dict) -> None:
    lease = _lease(state, event["lease_id"])
    _reopen_if_stale(lease, event["at"])
    if lease["status"] != "open":
        raise ValueError(f"lease is {lease['status']}, not open")
    node = _ident(event["node"], "node")
    if state["allegiance"].get(node) != lease["charter_id"]:
        raise ValueError("node is not under this banner")
    if node == lease["verifier"]:
        raise ValueError("the committed verifier cannot take the lease")
    lease["status"] = "claimed"
    lease["worker"] = node
    lease["claimed_at"] = event["at"]
    lease["last_beat"] = event["at"]


def _submit(state: dict, event: dict) -> None:
    lease = _held(state, event)
    digest = event["result_hash"]
    if not _hex64(digest):
        raise ValueError("result hash must be 64 hex characters")
    lease["status"] = "submitted"
    lease["result_hash"] = digest
    lease["last_beat"] = event["at"]


def _accept(state: dict, event: dict) -> None:
    lease = _lease(state, event["lease_id"])
    if lease["status"] != "submitted":
        raise ValueError("lease is not awaiting verification")
    if event["node"] != lease["verifier"]:
        raise ValueError("only the committed verifier can accept")
    if event["result_hash"] != lease["result_hash"]:
        raise ValueError("acceptance does not match the submitted hash")
    lease["status"] = "accepted"
    book = state["sway"][lease["charter_id"]]
    worker = lease["worker"]
    book[worker] = book.get(worker, 0) + 1


def _reject(state: dict, event: dict) -> None:
    lease = _lease(state, event["lease_id"])
    if lease["status"] != "submitted":
        raise ValueError("lease is not awaiting verification")
    if event["node"] != lease["verifier"]:
        raise ValueError("only the committed verifier can reject")
    if event["result_hash"] == lease["result_hash"]:
        raise ValueError("rejection hash matches the submission")
    _clear_holder(lease)


def _expire(state: dict, event: dict) -> None:
    lease = _lease(state, event["lease_id"])
    if lease["status"] != "claimed":
        raise ValueError("only a claimed lease can expire")
    if event["at"] <= lease["last_beat"] + lease["ttl_s"]:
        raise ValueError("lease has not expired")
    _clear_holder(lease)


def _held(state: dict, event: dict) -> dict:
    lease = _lease(state, event["lease_id"])
    if lease["status"] != "claimed":
        raise ValueError(f"lease is {lease['status']}, not claimed")
    if lease["worker"] != event["node"]:
        raise ValueError("node does not hold this lease")
    if event["at"] > lease["last_beat"] + lease["ttl_s"]:
        raise ValueError("lease expired before this event")
    return lease


def _lease(state: dict, lid: str) -> dict:
    lease = state["leases"].get(lid)
    if lease is None:
        raise ValueError(f"no such lease: {lid}")
    return lease


def _reopen_if_stale(lease: dict, now: float) -> None:
    if lease["status"] == "claimed" and now > lease["last_beat"] + lease["ttl_s"]:
        _clear_holder(lease)


def _clear_holder(lease: dict) -> None:
    lease["status"] = "open"
    lease["worker"] = None
    lease["claimed_at"] = None
    lease["last_beat"] = None
    lease["result_hash"] = None


def _ident(value: str, label: str) -> str:
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise ValueError(f"bad {label} id: {value!r}")
    return value


def _hex64(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


class Log:
    """A directory with one `log.jsonl`. Replay builds the state."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "log.jsonl"
        self.state = blank()
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    reduce(self.state, json.loads(line))

    def commit(self, kind: str, at: float | None = None, **fields: object) -> dict:
        event = {
            "kind": kind,
            "at": time.time() if at is None else at,
            "seq": self.state["seq"] + 1,
            **fields,
        }
        trial = copy.deepcopy(self.state)
        reduce(trial, event)
        line = json.dumps(event, sort_keys=True, separators=(",", ":"))
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.state = trial
        return event

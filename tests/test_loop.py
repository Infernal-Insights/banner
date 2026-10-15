import tempfile
import unittest
from pathlib import Path

from banner.roles import attest_all, open_charter, point, post_leases, sweep, work_once
from banner.state import Log
from banner.tile import digest, render


def _reef(root: Path, ttl_s: int = 60, grid: int = 2) -> Log:
    log = Log(root)
    open_charter(log, "reef", "Reef map", seed="reef-seed-v1", grid=grid)
    post_leases(log, "reef", verifier="attestor", ttl_s=ttl_s)
    point(log, "worker", "reef")
    return log


class LoopTest(unittest.TestCase):
    def test_accepted_work_earns_sway_and_replays(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = _reef(root)
            finished = []
            while True:
                lease_id = work_once(log, "worker")
                if lease_id is None:
                    break
                finished.append(lease_id)
            self.assertEqual(len(finished), 4)
            self.assertEqual(attest_all(log, "attestor"), 4)
            self.assertEqual(log.state["sway"]["reef"]["worker"], 4)
            replayed = Log(root)
            self.assertEqual(replayed.state["sway"], log.state["sway"])
            self.assertEqual(replayed.state["seq"], log.state["seq"])

    def test_verifier_cannot_take_the_lease(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = _reef(Path(tmp))
            point(log, "attestor", "reef")
            self.assertIsNone(work_once(log, "attestor"))
            with self.assertRaises(ValueError):
                log.commit(
                    "lease.claimed",
                    node="attestor",
                    lease_id="reef-0-0",
                    at=1,
                )

    def test_a_node_only_works_the_banner_it_is_under(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = _reef(Path(tmp))
            open_charter(log, "dune", "Dune map", seed="dune-seed-v1", grid=1)
            point(log, "worker", "dune")
            self.assertIsNone(work_once(log, "worker"))
            with self.assertRaises(ValueError):
                log.commit("lease.claimed", node="worker", lease_id="reef-0-0", at=1)

    def test_a_bad_hash_is_rejected_and_the_tile_reopens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = _reef(Path(tmp))
            log.commit("lease.claimed", node="worker", lease_id="reef-0-0", at=10)
            log.commit(
                "result.submitted",
                node="worker",
                lease_id="reef-0-0",
                result_hash="ab" * 32,
                at=10,
            )
            self.assertEqual(attest_all(log, "attestor"), 1)
            lease = log.state["leases"]["reef-0-0"]
            self.assertEqual(lease["status"], "open")
            self.assertEqual(log.state["sway"]["reef"], {})
            self.assertIsNotNone(work_once(log, "worker", at=11))
            charter = log.state["charters"]["reef"]
            honest = digest(render(charter["seed"], 0, 0))
            self.assertEqual(log.state["leases"]["reef-0-0"]["result_hash"], honest)

    def test_a_silent_worker_loses_the_lease(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = _reef(Path(tmp), ttl_s=10)
            log.commit("lease.claimed", node="worker", lease_id="reef-0-0", at=0)
            self.assertEqual(sweep(log, at=11), 1)
            self.assertEqual(log.state["leases"]["reef-0-0"]["status"], "open")
            point(log, "other", "reef")
            self.assertEqual(work_once(log, "other", at=12), "reef-0-0")

    def test_the_worker_cannot_accept_its_own_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = _reef(Path(tmp))
            work_once(log, "worker", at=5)
            with self.assertRaises(ValueError):
                log.commit(
                    "result.accepted",
                    node="worker",
                    lease_id="reef-0-0",
                    result_hash=log.state["leases"]["reef-0-0"]["result_hash"],
                    at=5,
                )

    def test_pointing_at_a_new_banner_leaves_the_old_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = _reef(Path(tmp))
            open_charter(log, "dune", "Dune map", seed="dune-seed-v1")
            point(log, "worker", "dune")
            self.assertEqual(log.state["allegiance"]["worker"], "dune")


if __name__ == "__main__":
    unittest.main()

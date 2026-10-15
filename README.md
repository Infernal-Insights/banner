# banner

Point a machine at a charter. Finish a task another node can recompute. That finished task is your sway on the charter. Sway is not a coin, and this repository does not mint one.

This is the reference loop, small enough to run on a laptop with Python and nothing else. It is not the network yet. The rules it enforces are the ones the network has to keep.

```bash
python -m banner demo
python -m banner status
```

`demo` opens a charter called Reef map, splits it into four tiles, has `worker` render each one, and has `attestor` render them again. On agreement the worker's sway becomes 4, and `banner-data/reef.ppm` is the picture. Run the tests with:

```bash
python -m unittest discover -s tests -v
```

What you can see from a browser on the same machine:

```bash
python -m banner serve
```

Read [docs/LOOP.md](docs/LOOP.md) for the event list and the things this cut deliberately leaves out: signatures, a real container digest, a rollup, escrow, and an election.

# banner

A distributed computer for one project. Members contribute CPU, GPU, and sharded disk. The project has a relational database those machines share, an orchestrator that places work without a model, and AI workers that manage the project by proposing the next tasks. Finished, checked work is the member's say. This repository does not mint a coin.

This is the reference loop. It runs on Python 3.10 and OpenSSL 3, with no packages to install. It is not the network yet. The rules it enforces are the ones the network has to keep: a second machine recomputes, and only that agreement counts.

```bash
python -m banner demo
python -m banner status
```

`demo` makes three keys, opens a charter called Reef map, splits it into four tiles, and writes `banner-data/reef.ppm`. `worker` renders each tile. `attestor` renders them again. On agreement the worker's sway becomes 4. A line in the log that `worker` did not sign is refused, and so is an acceptance signed by anyone but the named attestor.

The same steps by hand:

```bash
python -m banner node new steward
python -m banner node new worker
python -m banner node new attestor
python -m banner node join steward
python -m banner node join worker
python -m banner node join attestor
python -m banner charter open reef --node steward --name "Reef map" --seed reef-seed-v1 --grid 2
python -m banner charter post reef --node steward --verifier attestor
python -m banner point worker reef
python -m banner work worker --all
python -m banner attest attestor
```

Private keys stay in `banner-data/keys/`. The log keeps the public half only.

```bash
python -m unittest discover -s tests -v
python -m banner serve
```

Read [docs/LOOP.md](docs/LOOP.md) for the event list and [docs/ROADMAP.md](docs/ROADMAP.md) for the order of the rest: the desktop shelf, the contract, Vast overflow, and the project AI.

## Site

[`site/`](site/) is a static site for Cloudflare Pages. Set the root directory to `site`. There is no build command. The form on `start.html` only downloads a charter file. It does not upload one.
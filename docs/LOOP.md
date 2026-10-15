# The reference loop

This directory is one machine pretending to be the network. `log.jsonl` is the stand-in for a rollup. Replaying it rebuilds every charter, lease, allegiance, and sway counter. There is no token and no second process you have to trust beyond the rules below.

## Who does what

A **charter** is a banner. It names a pinned image and a grid of tasks. In this cut the image is `banner-tile:1`, a pure function in `banner/tile.py`. Later that string is an OCI digest. The lease rules do not care which it is.

A **steward** opens the charter and posts one lease per tile. Posting names the attestor. A worker cannot claim a lease that has no verifier yet.

A **worker** is under one banner at a time. Pointing at a new banner leaves the old one. It pulls an open lease, renders the tile, and submits the sha256 of the bytes. It never opens a port.

An **attestor** is the node named on the lease. It renders the same tile itself. If the hash matches, the lease is accepted and the worker's sway on that charter goes up by one. If it does not match, the lease goes back to open and sway does not move. The attestor cannot be the worker on that lease.

A claimed lease that misses its ttl goes back to open. Someone else under the same banner can take it.

## Events

`node.joined`, `charter.opened`, `allegiance.set`, `lease.posted`, `lease.claimed`, `lease.heartbeat`, `result.submitted`, `result.accepted`, `result.rejected`, `lease.expired`.

Every event except `lease.expired` is signed by the `node` it names. A node joins by publishing its Ed25519 public key and signing that publication. After that, the log refuses a charter, a lease, a claim, or an acceptance whose signature does not match the key bound to that name. `lease.expired` is unsigned because the clock is the authority: it is accepted only after the ttl, and it only returns the tile to open.

The node that opens a charter is the only one that can post its leases, and the verifier named on a lease has to have joined already. Sway is written only inside `result.accepted`. No event transfers it. Private keys stay in `banner-data/keys/` and are mode `0600`.

## What this cut does not do

A rollup. The signed log is still a file on one machine. The next cut is the same transitions in a contract, checked with `ecrecover` instead of OpenSSL.

An LLM steward. The poster of leases is a loop over the grid.

Containers. The tile function is the pinned image. Docker comes in when a second image id needs to mean an actual digest.

Decay, elections, escrow, and discovery across machines.

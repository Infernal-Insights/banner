# Roadmap

Banner is a way to point spare computers at a project and have that finished work count as a say in the project. The projects are software, models, and campaigns that need computers behind them, including public-record work where the output is a map a second computer can rebuild, not a verdict. The reference loop on `main` already does a thin version of this on one machine. This is the order to build the rest.

## Decisions

These are settled. A later phase does not get to quietly reverse them.

- Sway is not a token. It is a counter, on one charter, earned when a task is accepted. Nothing transfers it. There is no pool, and a rented machine cannot buy a vote by existing.
- MetaMask is a pen, not a wallet full of votes. It signs ballots and sends ETH into an escrow. The vote weight is read from the sway counter at that moment. There is nothing in the wallet to sell.
- A machine may stand under more than one banner. Each banner gets an explicit grant: this many cores, these GPUs, this disk. A GPU granted to one project is not available to another. The reference loop still points a node at one banner. That is a limitation of this cut, not the product.
- An empty queue is allowed. Most projects will be quiet most of the time. Quiet means the devices go back to the owner. The software does not invent work to keep a card busy.
- The project AI proposes. It does not accept results, ban workers, or publish on behalf of the project. Verification stays a recompute. Publishing and new kinds of work stay a vote.
- "Distributed LLM" means many copies of one small model with the same weights and the same instructions. It does not mean one large model sliced across home networks.
- Vast.ai is an overflow valve for a queue that real members cannot drain. Those machines are paid. They do not earn sway.
- Home nodes do not run Kubernetes. One supervisor inside the desktop app is the orchestrator.
- Already-voted work does not need the leader online. Any member may post a lease that uses an image the charter already allows. The keeper publishes drafts and notes. A silent or captured keeper is replaced by a ballot, and that ballot does not need their signature.
- Disk stores files the project named, in the original bytes. Empty space earns nothing. A holder proves possession by answering a random chunk challenge, checked like any other task. Storage sway is capped so a large disk cannot outvote the people who did the work.

## Where a vote lives

Two keys, on purpose.

The **worker key** lives in the desktop app, in an encrypted file on that computer. It signs claims and results. Sway accrues to this key, on that charter. Losing the machine without a backup loses the sway. That is acceptable. Sway is a record of who showed up recently, and it will decay. It is not savings.

The **personal key** is a normal Ethereum account. MetaMask is the right default for the person at a browser. It is the key that funds a bounty and signs a ballot. It does not hold sway, because sway cannot move.

Once, the person links them. The app signs "this worker belongs with this account," and MetaMask signs the same sentence the other way. After that, a ballot signed in the browser carries the sway of every linked worker that is still fresh. Unlinked sway still counts inside the app, where the worker key can sign for itself.

What MetaMask actually stores:

- ETH, if the person wants to pay for a bounty or for Vast overflow.
- Later, optionally, a soulbound receipt that mirrors sway so a wallet can display it. The contract rejects `transfer`. The contract counter remains the source of truth. Do not list it on an exchange. If a market appears, it is a market in a display badge, and the protocol ignores it.

What MetaMask does not store: a balance of votes.

## How a vote is applied

A ballot is a typed message, not a coin transfer.

```
banner-ballot:1
charter: reef
action: adopt-instructions
cid: bafy...
expires: <unix>
```

The weight is the voter's unexpired sway on that charter when the ballot closes. Half-life starts at 30 days once the contract exists. Doing more work refreshes it. Buying ETH does not.

Ballots in the first governance set:

| Action | What it changes |
|---|---|
| `adopt-instructions` | The pinned text the project AI must follow |
| `adopt-model` | The pinned weights of that AI |
| `elect-keeper` | Who may publish a draft. Not required to post a lease |
| `allow-image` | A container digest workers are permitted to run |
| `burst-budget` | The most ETH per day that may be spent on Vast |
| `count-receipts` | Whether paid overflow is even switched on |
| `admit-file` | A hash and a size allowed into the project's storage |
| `storage-budget` | The most bytes the project may hold, and how many files |

A ballot passes by more sway in favor than against, among ballots that arrive before it expires. There is no quorum theater in the first contract. A charter can raise its own threshold later, in the charter, not in a global parameter.

The desktop app and the website both prepare the same message. MetaMask is one way to sign it. The app signing with the worker key is the other. The contract checks the signature and reads sway. It does not move a token.

## The desktop app

One installer. Windows, Linux, then macOS. It registers `banner://` so a project link opens the app instead of a new account somewhere.

Inside, each banner the person has joined is a container on a shelf, not a tab they lose. A container shows the pitch, the queue depth, and the devices granted to it.

Per project, the person sets:

- how many CPU cores it may use
- which GPUs it may touch, one switch each
- whether it may run only while the machine is idle
- whether idle time on that project may be used for steward duty

A GPU switch is exclusive. Turning it on here turns it off everywhere else. Cores may be split. When that project's queue is empty, its cores and GPUs are released even if the switch stays on. The container says `quiet` and the card is the owner's again. A second project with a full queue may use devices that are currently released, if the owner granted them, and it gives them back when the first queue wakes up. The owner can also pin a project so nothing else borrows its devices.

The app does not open a port. It pulls leases from any peer that has them, not from the leader's machine. The first version can be the Python client with a tray and this window. The shell, when it needs to be a real installer, should be Tauri rather than Electron: one bundle, a small runtime, and a protocol handler. Kubernetes is not involved.

## If the leader is cut off

A project lives because other machines already have it, not because the leader's computer is still on. This is not true of the reference loop. That log is one file on one machine, and the site is a Cloudflare page. Both die with the machine or the domain. The phases below are what has to be true before the claim is real.

Every member who joins stores the charter and the signed log. The charter is named by the hash of its bytes. The website is a billboard for people who can reach it. It is not the copy that counts. Seizing the domain, or the leader, does not delete a replica sitting on someone else's disk.

New tasks do not wait on the leader. Once the members have voted the instructions and the allowed images, any of them may post a lease that fits those rules. The steward, when it exists, is those same rules running as a quorum of copies on members' machines. None of those copies has to be the leader's. A keeper who is jailed, offline, or coerced is a missing publisher of notes, not a missing project. The next ballot names another keeper without the old one agreeing.

What a cut-off leader cannot do, even if their key is seized: rewrite an event already in other people's logs. What they can still do until a ballot or until sway decays: sign new work as a member, inside the rules already voted. That is the same power any member has.

A government that cuts one country's internet does not erase the project for anyone outside it. Those people keep pulling leases from each other and from the rollup. People inside the cut keep the last charter they stored. They can keep working on a local network, or by carrying the log file to another machine. When a path to the outside exists again, the outside log wins a conflict: a tile already accepted out there is not accepted a second time, and sway is counted only for results the surviving log takes. If every replica was inside the cut, nothing outside has the project until someone carries a copy out. Replication only helps where a copy already is.

MetaMask and the rollup are unreachable inside that cut, so a ballot cannot close there. Work that only needs the last voted instructions does not need a ballot. Vast does not help. It is a company on the public internet.

## Orchestration

The orchestrator is the supervisor in that app. It is not a cluster control plane.

It watches the queue of each joined charter, starts a lease only if the grant has a free device, runs the pinned container with no host network, heartbeats, and stops the container when the lease ends or the owner hits pause. A lease that outlives its ttl returns to the queue without the app having to be trusted. That rule is already in the log.

A project owner does not SSH into members' machines. They publish work onto the charter. Members' supervisors take it or they do not.

## Making it easy to deploy

A person who wants to help:

1. Install the app.
2. Write down the recovery phrase for the worker key. Once.
3. Open a project link. The container appears, devices default to "idle only, no GPU," and nothing runs until they raise the grant.

A person who wants to start a project:

1. Fill in the bill on the website: name, the line a stranger reads, why a machine should join, the goals, what the work actually is, and how a finished task is recognized.
2. Download the charter file. The website does not upload it.
3. Open that file in the app, which becomes the keeper's first copy. Publishing it is a signed `charter.opened` once the contract exists. Until then the reference client can open it on a local log.

Defaults matter more than settings screens. No GPU until they opt in. Idle-only until they opt out. No steward duty until they opt in. No bounty required to join.

## The website

`site/` is the static site. Cloudflare Pages serves it with no build. Set the project root to `site`.

The site has to sell a banner the way a person actually decides to join: a name, a reason, a picture of the work, and a single link. It is not a dashboard and it does not pretend a wallet is connected. Creating a project in v1 produces a charter file and a `banner://join/<id>` link. It does not write to a chain, because the chain is not there yet.

## Vast.ai

When a charter's queue stays deep and the members' grants are not enough, the keeper may rent overflow. This is a paid valve, not a second kind of member.

- The same worker image, the same benchmark gate, the same verifier-committed-before-claim rule.
- ETH leaves the charter escrow. MetaMask (or the keeper's key, if the ballot already authorized a budget) pays.
- The rented machine earns the receipt it was promised. It earns no sway. If rented work voted, sway would be for sale, and the entire point of the system would be gone.
- The supervisor on the rented box is the same program, started with `BURST=1` so it refuses to sign ballots.
- The burst stops when the queue is shallow or the day's budget is gone. Nobody has to remember to terminate a fleet.

The desktop app does not embed a Vast account. A person at home is not asked to think about it.

## The project AI

Each charter may name a steward. The steward is a small language model, small enough to run on one consumer GPU or, slowly, on CPU. Every machine that has opted into steward duty for that project runs the same weights and the same instruction text. Both are pinned by digest. Changing either is a ballot (`adopt-model`, `adopt-instructions`). The voters are the people with sway on that project, signing from the app or with MetaMask.

Duty runs in the lulls. A project with an empty work queue may still ask opted-in machines to spend idle cores on the steward. It may not touch a GPU the owner did not grant, and it stops when real leases appear.

Replicas read the same public inputs: the charter, the instruction text, the open leases, and the recent accepted and rejected results. They draft at temperature 0. A draft becomes a proposal only when a quorum of replicas produce the same hash. One machine having a creative idea is not the project speaking.

A proposal may:

- slice the next piece of the stated goal into leases, using only container digests the charter already allows
- point at leases that failed recompute, with the lease ids attached
- draft a muster note that mentions only accepted work

A proposal may not:

- mark a result accepted
- ban a worker
- raise the burst budget
- change its own instructions
- post to a social network

Failed recomputes already have a non-AI rule: a worker who is rejected three times on a charter sits out of that charter for a while. The model can highlight the pattern. The rule does the punishing.

The muster note is the recruiting tool. It is a draft on the project page until sway says to publish it, or until the elected keeper publishes it. The page, not the model, is what a new person sees. The join link is on that page.

If the model has nothing honest to add, it stays quiet. An empty queue is not a failure.

## Storage

A project needs its files to outlive the person who started it: the charter, the log, the source files a second computer must rerun, and the model the members voted for. That is the storage problem. Filling a disk with puzzles is not.

The files stay in their original bytes, named by their hash. A member grants this project a number of gigabytes, the same way they grant cores. Compute goes quiet when the queue is empty. The files they promised to hold stay until they revoke the grant, and a revoke waits until enough other members hold them.

Proof of possession, not proof of replication. A file is cut into pieces. Each piece has a hash, and the hash of that list is the file's name. This is a torrent. A download asks several holders for different pieces at once, checks each hash, and throws the piece away if it does not match. A bad peer cannot land trash in the file, and cannot slow the transfer down to a single machine.

The holder also builds a Merkle tree over those pieces and commits the root. A challenge, taken from a public random, names a piece. The holder returns that piece and the path to the root, signed with the worker key. A checker hashes the piece and checks the path. Same rule as any other task. There is no sealing step. Sealing would hide the bytes the next task has to read.

Small files, including the charter and the log, are kept whole on at least three members. A large file is striped. The pieces are spread across holders with two extra parity pieces, the way RAID 6 keeps two disks of parity rather than RAID 5's one. One home machine being offline is normal. One parity piece is not enough. Any missing piece can be rebuilt from the others, and the rebuilt bytes still have to match the piece hash. Parity is for survival. The hash is for integrity. A rebuilt piece that does not hash is a failed holder, not a repaired file.

A file counts as held only while enough members have answered a recent challenge to rebuild it. If that fails, the project posts a store lease and someone with free grant takes the missing pieces. Some challenges are a fetch: a different member has to actually get the piece and confirm the hash. Possession without serving does not count.

Nothing enters that set because someone uploaded it. A file is admitted only as the charter, the log, the inputs or accepted output of a task the project already posted, or by an `admit-file` ballot that names the hash and the size. The project has a `storage-budget`: a maximum number of bytes and a maximum number of files. A proposal over the budget does nothing until a ballot raises it or drops something else. Unadmitted bytes are not seeded, not challenged, and not sway. A member can propose a file, but the proposal is a hash and a size, not the bytes, and a worker key can only propose so many per day so the log itself is not the spam channel.

Answering challenges on admitted pieces earns storage sway on that charter. It decays, it does not transfer, and a charter caps it so a shelf of disks cannot outweigh accepted work. Unused capacity, and disk rented to no project, earns nothing.

Filecoin's newer proof of data possession is the same shape of challenge, and a project may later pay a Filecoin provider in ETH to hold a cold copy. That provider does not earn sway. WindowPoSt, sector sealing, and proof-of-space plots are not used.

## Phases

### 0. Reference loop

Done. A signed log, one charter, a tile any second node can recompute, sway that only acceptance writes, a local status page.

### 1. The bill and the site

In progress. A static site a stranger can read, a specimen banner, and a form that writes a charter file. Cloudflare Pages. No wallet button, no fake installer. The site is not a replica. A project someone joined still has to be stored by their app.

### 2. The shelf

The desktop window: more than one project, core counts, GPU switches, idle-only, a quiet state when the queue is empty. `banner://join/<id>` opens the app and adds the container. The Python client can grow this before a Tauri shell exists. Still one machine, still the local log.

### 3. The contract

The same transitions as the log, on a local Ethereum chain and then on one existing rollup. The rollup orders events for anyone who can reach it. It is not the only copy: every member keeps the charter and the log, and a lease can be fetched from any of them. Worker key earns sway. Personal key, MetaMask included, signs ballots and funds escrow. Linking the two keys. Sway has no `transfer`. Decay can land in this phase once acceptance works on the contract. Ballots for instructions, keeper, allowed images, and burst budget. Posting a lease that matches the voted rules does not require the leader's key. A local log from inside a network cut can be merged later, and an acceptance already in the outside log wins.

### 4. Real work

Replace `banner-tile:1` with an OCI digest. The supervisor runs it rootless, with no host network. A machine gets a short-lived capability certificate from a benchmark before it can take a lease that asks for a GPU. The verifier is still named before the claim.

### 5. The supervisor grows up

Queue depth, exclusive GPUs, borrowing released devices, pause, heartbeat, and the three-reject sit-out. This is the orchestration software. It ships inside the app. A per-project disk grant lands here: admitted files only, piece hashes, parity on large files, Merkle challenges, and a store lease when a file can no longer be rebuilt. Storage sway is capped.

### 6. Overflow

Charter escrow in ETH. A passed `burst-budget` ballot. A rented Vast box boots the worker in burst mode, gets paid, and cannot vote. It is terminated when the queue or the budget says so.

### 7. The steward

Pinned small model, pinned instructions, replicas on opted-in machines during lulls, quorum on the proposal hash. Draft leases, draft fraud notes, draft muster notes. No accept button and no social account.

### 8. Keeping a banner

Elect the keeper. Publish muster notes by vote. The project page becomes the thing a link points at, with the pitch, the goals, the live queue, and the join button. Recruiting is that page plus a note that only mentions work that was actually accepted.

## Not in any phase until the above works

A new L1. A tradeable vote. A Kubernetes cluster for home PCs. A model that judges "good work" without a recompute. A steward that posts to a social network by itself. Slicing one giant model across members' houses. Sector sealing. Proof-of-space plots. Sway for empty disk.

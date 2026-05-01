---
title: "ARM64 on Oracle Ampere: What Worked, What Didn’t, and What I Built Instead"
datePublished: 2026-05-01T06:18:55.958Z
cuid: cmomivb6d00wp2dl73n6o5j7y
slug: arm64-on-oracle-ampere-what-worked-what-didn-t-and-what-i-built-instead

---

If you’ve spent any time evaluating cloud compute for side projects or small production workloads, you’ve probably come across Oracle Cloud’s Always Free tier. The headline offer is genuinely difficult to beat: up to 4 OCPUs and 24 GB of RAM on an Ampere A1 ARM64 VM, plus 200 GB of block storage, free forever. No trial period. No surprise bill at month seven.

I’ve been running one for several months now as the orchestration and automation hub for a small product company — Microsoft 365 backups, a few Docker workloads for internal tooling, and supporting infrastructure for a Next.js + Supabase application. The “free” part has been honest. The “ARM64” part has been… educational.

This post is the version of the ARM64 story I wish I’d had when I started: what actually works, where compatibility quietly fails, and the workarounds I ended up settling on.

## What you actually get

The Always Free Ampere VM is a single shape (`VM.Standard.A1.Flex`) you can configure with up to 4 OCPUs and 24 GB of RAM. The OCPU count matters less than people think — Ampere cores are real cores, not hyperthreaded slices, so 4 OCPUs feels closer to 8 vCPUs on x86 in most real-world workloads. I/O is fine. Network is generous.

The VM runs Oracle Linux or Ubuntu (I went with Ubuntu). Docker installs cleanly. systemd works. The kernel is recent enough that nothing modern complains.

If your mental model is “this is just a Linux box with an unusual CPU,” you’re about 80% right. The remaining 20% is where this post lives.

## What works beautifully on ARM64

Most modern, container-first software runs without modification:

*   **Docker and docker-compose** — Every official image I’ve needed (Postgres, Redis, NGINX, Caddy, Node, Python) ships multi-arch manifests. `docker pull` just does the right thing.
    
*   **Node.js / Next.js workloads** — Native ARM64 builds, no performance surprises.
    
*   **Standard Linux tooling** — rsync, cron, systemd timers, certbot, fail2ban — all unchanged.
    
*   **Modern automation agents** — GitHub Actions self-hosted runner, Tailscale, Cloudflare Tunnel daemon — all ship aarch64 binaries.
    

If you’re building something net-new and choosing your stack today, you can comfortably assume ARM64 is a non-issue.

## Where ARM64 quietly bites

The pain shows up when you reach for an established commercial tool — especially anything in the backup, enterprise database, or legacy integration space. These vendors built their distribution channels around x86, and many haven’t followed the architecture shift.

Three concrete examples from my own setup:

**Microsoft 365 backup tools.** I evaluated CubeBackup and Veeam for Microsoft 365 — both look great on paper, both ship x86 Linux binaries, neither offers an ARM64 build. CubeBackup’s installer fails the architecture check on first run. Veeam doesn’t even try. I checked their roadmaps; ARM64 wasn’t on either.

**SQL Server.** Microsoft does not ship ARM64 Linux images for SQL Server, and the official images won’t run under emulation in any way I’d trust for actual data. If you need SQL Server on this VM, you can’t have it. Postgres is your friend instead.

**Various Windows-adjacent agents.** A handful of monitoring tools and integration agents I won’t name — same story. Linux builds exist, but they’re x86-only, and the vendors haven’t responded to ARM64 requests.

The frustrating part isn’t that these tools don’t exist on ARM64. It’s that you usually find out *after* you’ve provisioned the VM, configured networking, set up the user, and gone looking for the install doc. The architecture check at install time is the first time the issue surfaces.

## What I built or substituted

Instead of fighting the gaps, I ended up with two practical substitutions for the M365 backup case:

**For Exchange / mailbox backups: Mail-Archiver.** It’s a Docker-based tool that pulls mail via IMAP/EWS and writes to local disk in a queryable format. Multi-arch image, runs as a container, boring and reliable.

**For SharePoint / OneDrive:** `driveone/onedrive`**.** A Docker image wrapping the open-source `abraunegg/onedrive` CLI client. Bidirectional sync to local disk, ARM64 image available. Not as polished as Veeam’s GUI, but it does the actual job — files end up on disk, encrypted at the volume level, recoverable.

Neither was my first choice. Both turned out to be the right choice, because they’re architecture-agnostic by design — containers wrapping open-source CLI tools — rather than binary-distributed enterprise products.

## The mental model that actually helps

After a few cycles of “evaluate, install, hit the wall, find a substitute,” I’ve settled on a simple rule: **for any new tool, the architecture check happens first, before reading the docs.**

In practice:

1.  Look at the vendor’s download page or official Docker image. If you see `aarch64` or `arm64` listed, you’re good.
    
2.  If only `x86_64` / `amd64` is listed, check the GitHub repo or release page for any ARM64 build at all. Don’t assume it’s coming.
    
3.  If nothing exists, decide *now* whether you’ll wait, run a separate x86 VM (defeating the point of the free tier), or pick a substitute.
    

This sounds obvious. It is obvious. But it’s the step you skip when a tool looks promising and you want to start playing with it. Half an hour saved at the start saves a day of rebuild later.

## Would I do it again?

Yes — but with eyes open. The Always Free Ampere VM is a remarkable resource for the right kind of workload. If your stack is container-native and modern, you’ll barely notice the architecture. If it leans on traditional commercial backup, database, or enterprise tools, you’re going to be doing substitution work — and you should plan for that before you commit, not after.

The short version for anyone evaluating it:

*   **Run on it**: anything containerized, anything modern, anything open-source.
    
*   **Don’t run on it**: SQL Server, Veeam, CubeBackup, x86-only commercial agents.
    
*   **Substitute, don’t fight**: Mail-Archiver for Exchange backup, `driveone/onedrive` for SharePoint, Postgres instead of SQL Server.
    

If you’re just starting to look at Oracle Ampere, hopefully this saves you a few of the rabbit holes I went down.
# Blog: srinivasans.hashnode.dev

This repo is the source for **srinivasans.hashnode.dev**. Posts are synced to Hashnode by a GitHub Actions workflow (`.github/workflows/publish-to-hashnode.yml`) that calls Hashnode's GraphQL API on every push to `main`. The Hashnode "GitHub Backup" integration is also installed on the publication — that's a one-way push *from* Hashnode *to* GitHub for backup, and is unrelated to the publishing path used here.

You (Claude Code) are expected to act as both the **writing partner** and the **publishing pipeline**: brainstorming, outlining, drafting, refining, and finally committing the post. The author drives strategy and tone; you handle the mechanics.

-----

## How Hashnode publishing works

- Posts are Markdown files at the **root of the repo** (no `posts/` folder). The workflow ignores `CLAUDE.md`, `IDEAS.md`, and `README.md`.
- The filename should match the slug (e.g., `my-post-slug.md` ↔ `slug: my-post-slug`).
- A push to `main` triggers `.github/workflows/publish-to-hashnode.yml`, which runs `scripts/sync-to-hashnode.py` for each changed `.md` file.
- The script looks the post up in Hashnode by `slug`:
  - If a published post exists → `updatePost` (edits in place).
  - Else if a draft exists → `updateDraft`.
  - Else → `createDraft`.
  - If `saveAsDraft: false` and the post isn't yet published → `publishDraft`.
- A `workflow_dispatch` trigger is also wired up: run the workflow manually from the **Actions** tab to (a) re-sync every post when no input is given, or (b) sync a single file when the `file` input is set.
- **Iteration only happens on pushes to `main`.** Edits on a feature branch don't sync until merged. Each round-trip (draft → review → publish) = one commit on `main`.
- **Edits made directly in the Hashnode editor will be overwritten** by the next push, since the script treats the repo as the source of truth. Iterate by committing, not by editing on Hashnode.
- Slug + filename together identify the post. Renaming a file = new post on Hashnode. **Don't rename committed files unless that's intentional.**
- The script requires the `HASHNODE_TOKEN` repo secret (a Hashnode personal access token) and the `HASHNODE_HOST` env var (set in the workflow to `srinivasans.hashnode.dev`). If a workflow run fails, the GitHub Actions log shows the exact GraphQL error — there is no Hashnode-side "View logs" panel for this path.

-----

## Required frontmatter

Every post must begin with:

```yaml
---
title: <Post title>
slug: <unique-url-slug-matching-filename>
tags: <up-to-5-comma-separated-tag-slugs>
saveAsDraft: true    # default for new posts; flip to false to publish
---
```

### Optional fields supported by the sync script today

- `subtitle:` — recommended; shown below the title on the post page.

### Optional fields not yet wired up in the sync script

These are accepted by Hashnode in principle, but `scripts/sync-to-hashnode.py` does not currently send them. Adding one means extending the script's `build_input()`. Don't include them in posts until they're wired up — they'll just be silently ignored.

- `enableToc: true` — table of contents.
- `seoTitle:` / `seoDescription:` — search-engine overrides.
- `canonical:` — original URL when cross-posting.
- `coverImage:` — must be uploaded to Hashnode's CDN first via https://hashnode.com/uploader.
- `domain:` — historically used by Hashnode's "Publish from GitHub" integration. Ignored by the script (host comes from `HASHNODE_HOST` in the workflow).

### Tag slug rules

- Maximum 5 tags.
- Tag slugs must be valid Hashnode tags. The canonical list lives at https://github.com/Hashnode/support/blob/main/misc/tags.json — when in doubt, check it. Common safe ones for this blog: `aws`, `azure`, `oracle-cloud`, `docker`, `devops`, `self-hosting`, `arm64`, `ai`, `machine-learning`, `software-engineering`, `automation`, `nextjs`, `vercel`, `aspnet`, `vbnet`, `sql-server`. (Note: `rag`, `embeddings`, `voyage-ai`, `supabase`, `llm`, and `llms` are *not* in the canonical list as of the last check — verify before using.)
- The sync script converts the comma-separated slug list into Hashnode's expected `[{slug, name}]` shape. Names are derived from slugs with a small override table for known acronyms (AI, ML, AWS, etc.) — see `_TAG_NAME_OVERRIDES` in `scripts/sync-to-hashnode.py`.
- If a workflow run fails, an invalid tag slug is the most common reason — check the GitHub Actions run log.

-----

## Voice, audience, and structure

**Audience.** Software developers and architects, mid- to senior-level. People who’d Google a specific problem and want an honest, concrete answer rather than a marketing post.

**Voice.**

- First-person, pragmatic, dry-humored.
- Lead with the concrete problem, not abstract framing.
- Honest about what didn’t work and what tradeoffs were taken.
- Code blocks when they clarify, not to pad length.
- No filler intros (“In today’s fast-paced world…”). Get to the point in the first sentence.
- Avoid hype. The reader is a peer, not a customer.

**Length.** 800–1,500 words. Readable in one sitting, substantive enough to be worth ranking for.

**Structure that tends to work for this blog:**

1. **The hook** — the practical problem in one paragraph.
1. **What I tried first / why it didn’t work** — short, honest.
1. **What actually worked** — specifics: numbers, code, tradeoffs.
1. **What I’d do differently today** (when applicable) — keeps posts honest as the ecosystem moves.
1. **The takeaway** — short, scannable, 3–5 bullets.

-----

## Generating ideas for new posts

When the author asks for topic ideas, or when you’re choosing a topic for the next post, **do not just read from IDEAS.md and pick**. Generate ideas dynamically each session by combining several inputs.

### The standard idea-generation flow

1. **Start by asking what’s recent.** Ask a short, specific question like: *“What’s been occupying you this week — anything thorny, surprising, or interesting that came up in the work?”* The most authentic, traffic-pulling posts come from problems the author actually wrestled with in the last 7–14 days. If the author has already volunteered current context in the conversation, skip this step.
1. **Survey what’s already in the repo.** List the published `.md` files at the root and skim their frontmatter (titles, tags). Use this to:
- Avoid duplicating a topic.
- Spot natural follow-ups, deeper dives, or companion pieces (e.g., an “ARM64 backups deep-dive” follows naturally from a general “ARM64 on Ampere” post).
- Identify “what I’d do differently now” angles for older posts as the ecosystem moves.
1. **Read IDEAS.md as inspiration, not a fixed menu.** Treat its entries as starting points — they may need a fresher angle, or may have been overtaken by what the author is working on now.
1. **Optionally web-search for current developments** in this blog’s specific stack (ARM64 cloud, Voyage AI, Supabase, Next.js, Hashnode, AI features in enterprise software). Only do this when looking for *timely* angles tied to recent ecosystem changes — don’t search for “trending dev topics” generally.
1. **Filter for authenticity.** This blog’s defensible angle is the author’s specific perspective: small enterprise software shop, on-prem deployments for banks/NBFCs, ARM64 self-hosting, AI features built by a tiny team without a dedicated ML org. Reject ideas that any larger publication could write better — favor ideas that only the author can write credibly.
1. **Propose 2–3 distinct options.** Each option gets a working title and one sentence on the angle. Briefly note why each fits this blog. Let the author pick.
1. **Capture unused good ideas.** When the author picks one option, append the *other* viable proposals to IDEAS.md (under “Backlog” or “Bigger ideas” depending on shape) before drafting. This way every session contributes to the parking lot, even when only one idea ships that week.
1. **Prune as you go.** When publishing a post, move it from IDEAS.md (if it was there) to the “Published” list with the URL and date. If you notice a backlog item that’s been overtaken by reality (e.g., a tool you wanted to write about no longer exists), surface that to the author and offer to remove it.

### Anti-patterns to avoid

- **Don’t propose generic dev topics.** “10 tips for clean code” — no. “How to learn React” — no. The blog’s value is specificity.
- **Don’t propose ideas without an authentic anchor.** If you can’t tie it to something the author has actually built, debugged, or thought hard about, it’s the wrong topic.
- **Don’t lead with web-search results.** Use search to enrich an idea, not to source the idea.

-----

## Standard workflow per post

1. **Pick a topic** — using the idea-generation flow above, or an explicit topic from the author. Confirm angle and rough scope before drafting.
1. **Outline first** — 4–6 section headings. Get author approval before writing the body. Saves rewriting later.
1. **Draft** — full Markdown with frontmatter (`saveAsDraft: true`). Filename = slug.
1. **Commit and push** to `main` with a clear message (e.g., `Add post: <title>`).
1. **Wait for author review** — Hashnode picks up the file within ~60s; the author reviews the draft in the Hashnode editor.
1. **Iterate if needed** — edits go via further commits to the same file.
1. **Publish** — when the author confirms, change `saveAsDraft: true` → `saveAsDraft: false` (or delete the line) and commit again. Post goes live.
1. **Update `IDEAS.md`** — move the topic from Backlog to Published with the post URL and date. Append any new ideas surfaced during the session.

-----

## Constraints to respect

- **Public repo.** Never commit: customer-identifying information, unreleased product details, internal API keys, employee names, or specific client mentions. When in doubt, generalize (“a financial-services client” not the actual name).
- **No secrets in commits ever** — even temporarily. If a draft accidentally includes one, scrub it before pushing.
- **Don’t bulk-edit** more than 10 files in a single commit (Hashnode limit).
- **Don’t rename published post files** — it creates a duplicate post and breaks the original URL.

-----

## Author context (for tone consistency)

The author runs a small product company in Mumbai building on-premises compliance and financial software for banks and NBFCs. Primary stack: ASP.NET Framework 4.8 + SQL Server. Newer work: Next.js + Supabase + Voyage AI embeddings + Groq inference. Self-hosts on Oracle Cloud Ampere ARM64 (Always Free tier) and Azure. Posts should draw from real production work — that authenticity is the differentiator. The blog isn’t a tutorial site; it’s a working architect’s notebook.

-----

## Files in this repo

- `CLAUDE.md` — this file (the spec).
- `IDEAS.md` — accumulating parking lot of topic ideas and the published-post log. Read for inspiration, write to capture, never treat as the only source of ideas.
- `<slug>.md` — individual posts at the repo root.

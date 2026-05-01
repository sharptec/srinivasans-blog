# Topic Parking Lot & Post Log

This file is a *living parking lot* — a place where ideas land between sessions, not the canonical source of what to write next. Topics are generated dynamically each session per the idea-generation flow in `CLAUDE.md`. Entries here are inspiration, starting points, and accumulated thinking from past sessions.

When publishing, move the post from below to “Published” with its URL and date. When new ideas surface during a session that aren’t picked, append them to “Parking lot” so they’re not lost.

-----

## Published

- **ARM64 on Oracle Ampere: What Worked, What Didn’t, and What I Built Instead** — April 2026
  https://srinivasans.hashnode.dev/arm64-on-oracle-ampere-what-worked-what-didnt

-----

## Drafted / awaiting review or publish

- **Embedding 67,000 Support Emails with Voyage AI — Batching, Pacing, and What I’d Do Differently Today**
  Slug: `embedding-67k-support-emails-with-voyage-ai`
  Status: drafted, sitting as a Hashnode draft awaiting publish.

-----

## Parking lot

Half-formed and well-formed ideas that haven’t been picked yet. Entries here may have been generated in past sessions but didn’t make the cut, or may be seeds the author dropped in passing. **Refresh angles before drafting** — the world moves.

### Reasonably well-shaped (could be drafted in one session)

- **Replacing Mondor’s MS-CAPTCHA with a 200-line VB.NET control.** Build-vs-buy story; the `System.Drawing`-only zero-dependency approach. Why the custom control was simpler than the licensing path.
- **Supabase Edge Function gotchas in production.** `onConflict` requiring an explicit unique constraint; service role key bypassing REST permission issues that persist with RLS off; the `files: []` parameter requiring actual file content for new function deployments.
- **AI email triage with a precision gate before automation.** Three-phase architecture (classify → review → auto-acknowledge). Why a 90% precision threshold over 200+ reviewed emails before activating auto-response. How the confusion matrix shaped the design.
- **The Vercel + GitHub committer-email gotcha that breaks Hobby tier deploys.** Short, sharp post: commits authored with an email not linked to the GitHub account silently fail to deploy.

### Bigger ideas (need shape before drafting)

- The architecture of a custom KB chat app for an enterprise support team — probably too broad as one post; might split into 2–3 (architecture / embedding strategy / retrieval tuning).
- Why I chose Voyage AI over OpenAI embeddings — could be a sharper standalone post if framed as a benchmark/decision story.
- Self-hosting Microsoft 365 backups on a free ARM64 VM — companion to the published ARM64 post, deeper on Mail-Archiver and `driveone/onedrive` setup.
- The phased-rollout pattern for AI features (human-in-loop → assisted → automated) — opinion piece, would benefit from at least two concrete examples.
- Bastion host architecture for a small support team accessing dozens of client servers — useful but currently aspirational; revisit once implemented.

-----

## Stale / archive candidates

(If a parking-lot item gets overtaken by the world — tool deprecated, problem solved by ecosystem, no longer interesting — move it here with a one-line note. Periodically prune.)

- (none yet)

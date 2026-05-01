---
title: Why I Waited for 90% Precision Over 200 Emails Before Letting the Bot Auto-Reply
subtitle: Building an LLM eval without an ML org — and why precision, not accuracy, was the gate that actually mattered.
slug: precision-gate-before-auto-reply-email-triage
tags: ai, machine-learning, software-engineering, automation
domain: srinivasans.hashnode.dev
enableToc: true
saveAsDraft: true
---

The product team I run handles support email triage for our compliance product. A client — typically a co-operative bank or a small NBFC — sends in a query at 9 PM. By the time it lands in our queue the next morning, the model has already classified it: routine onboarding question, urgent transaction issue, regulatory clarification, and so on. That part has been live for months.

The next step was the obvious one: when the model is confident the email is a routine acknowledgement-type query, send the auto-reply directly. No human in the loop. Save the support team an hour a day.

I sat on that switch for four months.

The reason: a wrong auto-reply to a client is a public miss. We can't take it back. Once an email leaves our outbound MTA with the wrong tone, the wrong assumption, or — worst case — the wrong factual content, it's in the client's inbox forever. Screenshots in WhatsApp groups, awkward calls, escalations to compliance. The client doesn't care that we shipped 99% of the auto-replies correctly. They care about the one wrong one we sent *them*.

So I built a precision gate. This post is what it looked like, what it cost to build, and why the threshold landed where it did.

## What I tried first, and why it didn't work

The first instinct — and the one most teams stop at — was to track aggregate accuracy on a held-out test set. We had a few hundred emails the model had classified, the support team agreed-or-disagreed, and we computed accuracy. It came in around 88%.

88% sounds fine until you sit with what it actually means.

Two problems showed up immediately:

1. **Class imbalance.** Most support emails are routine. If 70% of incoming queries are "I forgot my password" or "send me last month's report," a classifier that always predicts the most common class gets 70% accuracy without doing any work.
2. **Asymmetric cost.** A false negative — the model says "this isn't routine, route to a human" when it actually is — costs us nothing. A human reads it and routes it correctly. A false positive — the model says "routine query, send the canned reply" when it isn't — sends a wrong email to a client.

Aggregate accuracy treats both errors as equal. They aren't. Not even close.

I knew this in the abstract. What I didn't know, until I built a confusion matrix and stared at it, was *how* unequal it was for our specific data. The 88% accuracy hid a precision-on-the-positive-class number that was meaningfully lower.

## The eval set: 200+ manually reviewed emails

The thing that finally worked was boring: we built an eval set by hand.

The setup was a spreadsheet with one row per email — anonymised, sender names redacted to a synthetic ID — and columns for the email body, the model's predicted class, the model's confidence score, the support team's correct label, and a free-text notes column for the reviewer. The support team labelled emails over about two weeks, in 30-minute batches, around 20 emails per batch.

We capped the first round at 200 because that was the smallest set where the precision number stopped wobbling between batches. Below 150 the number swung 5–10% from sample variance alone; by 200 it was stable to within a couple of percent. That isn't a rigorous power calculation — it was eyeballed — but it was enough to make a decision.

Some things that mattered more than I expected:

- **The free-text notes column was the most valuable artefact.** Half the post-mortem on every model change was just re-reading the notes from the previous round. "This one was technically a routine query but the client was angry, model didn't pick that up." That's a class of failure aggregate metrics will never surface.
- **The labellers had to disagree with each other sometimes.** When two reviewers labelled the same email differently, that was a sign the *category itself* was fuzzy. The fix was usually a clearer category definition, not a better model.
- **We did not use BLEU, ROUGE, or any string-similarity metric.** This is a classification task, not a generation task. Most of what's written about LLM eval is benchmark noise that doesn't apply when you're shipping a feature.

## Why 90% precision specifically

Once we had the eval set, the question was: where do we set the gate?

Precision on the "send auto-reply" class is the right metric here for one reason: it's the only metric that tells you what fraction of auto-replies the client receives are wrong. At 90% precision, for every 100 emails the bot auto-replies to, 10 clients get a wrong response. At 95%, 5 do. At 99%, 1 does.

Then it's arithmetic from business reality:

- We were processing roughly 400 routine-class emails a week.
- At 90% precision, ~40 clients/week receive a wrong reply.
- At 95%: ~20 wrong replies/week.
- At 99%: ~4 wrong replies/week.

40 wrong replies a week was unshippable — the support team would spend more time apologising than they saved. 4 was acceptable. So the natural temptation was to set the threshold at 99%.

We didn't, for two reasons:

1. **At 99% precision the model only auto-replies on a thin slice of very-high-confidence emails** — maybe 15% of routine queries. The rest still go to a human. The labour-saving was negligible.
2. **The confusion matrix told us 90% precision was achievable on a *narrower* class definition.** Instead of "any routine query," we redefined the auto-reply class to "password reset and report-resend requests only." On that narrower class, 90% precision corresponded to roughly 60% of total volume going to auto-reply, with about 6 wrong replies a week.

That was the trade we shipped. Less ambition on what got automated, more confidence on each one that did.

The threshold isn't a magic number. It's a function of (a) how many wrong outputs your business can absorb per unit time and (b) how many correct outputs you give up to get there. Anyone quoting an absolute precision target without those two numbers is guessing.

## The three phases: classify → human-in-loop → auto-acknowledge

Even with the gate set, we didn't flip auto-reply on.

**Phase 1 (3 weeks): classify-only.** The model classified every incoming email and added a label to the support queue. No automated action — the model was just decorating the queue. We used this period to expand the eval set from 200 to ~500 emails, by having the team flag any classification they disagreed with as it came past them.

**Phase 2 (4 weeks): human-in-loop.** The model drafted the auto-reply, but the draft sat in a "Suggested reply" panel in the support tool. The human reviewer either clicked Send or rewrote and sent. Two useful things came out of this phase:

- We caught a class of failure we hadn't seen in the eval set: emails that *looked* like routine queries but contained a second, urgent, unrelated question buried in paragraph three. The model would draft a reply to the routine part and silently miss the urgent one.
- We measured the click-through rate on "Send as drafted." That number — what fraction of human-reviewed drafts went out unchanged — turned out to be a better real-world precision proxy than the eval-set number, because it was computed against live traffic and current model behaviour, not a static set.

**Phase 3 (where we are now): auto-acknowledge.** Auto-reply is on, but only for the narrow class. There's a daily report flagging any auto-reply where the model's confidence was within 5% of the threshold, and a weekly review of any client who replied to an auto-reply within 10 minutes — a rough proxy for "the auto-reply was wrong, here's the actual question."

We've been in Phase 3 for about six weeks. Two wrong replies in that window. Both caught by the daily report before the client escalated.

## What I'd do differently

If I were starting again I'd do two things sooner. First, I'd build the eval set in week one rather than week six. We spent the early weeks on prompt engineering against vibes, and most of that work was thrown away once the eval surfaced what was actually breaking. Second, I'd track the "click-through rate on suggested reply" metric from the very first day of Phase 2 — not at the end of it. That number was more honest than anything else we measured, and we left it on the table for almost a month.

## The takeaway

- **Build the eval set before you build the feature.** It changes which metric you optimise, and that changes which model you ship.
- **Pick the metric that matches the failure cost.** Accuracy is rarely it. For client-facing automation, precision on the positive class is usually closer.
- **Phased rollout buys you trust capital** — from your support team, who have to live with the mistakes, and from your clients, who don't know an LLM is involved and don't need to.
- **Tiny teams can do real eval.** No annotators, no MLOps platform, no eval framework. A spreadsheet, two weeks, and the willingness to argue about category definitions is enough.
- **The threshold is product-specific.** "90% precision" was right for our class, our volume, and our cost-of-wrong. It's almost certainly wrong for yours. Do the arithmetic.

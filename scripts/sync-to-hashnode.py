#!/usr/bin/env python3
"""Sync a single Markdown post to Hashnode via the GraphQL API.

Reads frontmatter compatible with the spec in CLAUDE.md, then either
creates a draft, updates an existing draft, updates a published post,
or publishes a draft, depending on (a) whether the slug already exists
in Hashnode and (b) the value of `saveAsDraft` in the frontmatter.

Env: HASHNODE_TOKEN, HASHNODE_HOST.
Usage: sync-to-hashnode.py <path-to-post.md>
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import requests
import yaml

GQL = "https://gql.hashnode.com/"


def gql(query: str, variables: dict, token: str) -> dict:
    r = requests.post(
        GQL,
        json={"query": query, "variables": variables},
        headers={"Authorization": token, "Content-Type": "application/json"},
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()
    if payload.get("errors"):
        raise RuntimeError("GraphQL errors:\n" + json.dumps(payload["errors"], indent=2))
    return payload["data"]


def parse_post(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n+(.*)\Z", text, re.DOTALL)
    if not m:
        raise ValueError(f"{path}: missing or malformed frontmatter")
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


_TAG_NAME_OVERRIDES = {
    "ai": "AI",
    "ml": "ML",
    "aws": "AWS",
    "azure": "Azure",
    "devops": "DevOps",
    "nextjs": "Next.js",
    "aspnet": "ASP.NET",
    "vbnet": "VB.NET",
    "sql-server": "SQL Server",
    "oracle-cloud": "Oracle Cloud",
    "arm64": "ARM64",
}


def tag_input(slug: str) -> dict:
    slug = slug.strip()
    name = _TAG_NAME_OVERRIDES.get(slug) or slug.replace("-", " ").title()
    return {"slug": slug, "name": name}


def parse_tags(value) -> list[dict]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        slugs = [str(s).strip() for s in value]
    else:
        slugs = [s.strip() for s in str(value).split(",")]
    return [tag_input(s) for s in slugs if s]


def truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes"}


def get_publication_id(host: str, token: str) -> str:
    data = gql(
        "query($host: String!) { publication(host: $host) { id } }",
        {"host": host},
        token,
    )
    pub = data.get("publication")
    if not pub:
        raise RuntimeError(f"No Hashnode publication found for host '{host}'")
    return pub["id"]


def find_published_post_id(host: str, slug: str, token: str) -> str | None:
    data = gql(
        """
        query($host: String!, $slug: String!) {
          publication(host: $host) {
            post(slug: $slug) { id }
          }
        }
        """,
        {"host": host, "slug": slug},
        token,
    )
    return ((data.get("publication") or {}).get("post") or {}).get("id")


def find_draft_id(publication_id: str, slug: str, token: str) -> str | None:
    """Page through the publication's drafts looking for one with this slug."""
    cursor: str | None = None
    while True:
        data = gql(
            """
            query($id: ObjectId!, $after: String) {
              publication(id: $id) {
                drafts(first: 50, after: $after) {
                  edges { node { id slug } }
                  pageInfo { hasNextPage endCursor }
                }
              }
            }
            """,
            {"id": publication_id, "after": cursor},
            token,
        )
        conn = (data.get("publication") or {}).get("drafts") or {}
        for edge in conn.get("edges") or []:
            node = edge.get("node") or {}
            if node.get("slug") == slug:
                return node.get("id")
        info = conn.get("pageInfo") or {}
        if not info.get("hasNextPage"):
            return None
        cursor = info.get("endCursor")


def build_input(fm: dict, body: str) -> dict:
    inp: dict = {
        "title": fm["title"],
        "slug": fm["slug"],
        "contentMarkdown": body,
    }
    if fm.get("subtitle"):
        inp["subtitle"] = fm["subtitle"]
    tags = parse_tags(fm.get("tags"))
    if tags:
        inp["tags"] = tags
    return inp


def create_draft(publication_id: str, fm: dict, body: str, token: str) -> str:
    inp = build_input(fm, body) | {"publicationId": publication_id}
    data = gql(
        "mutation($input: CreateDraftInput!) { createDraft(input: $input) { draft { id } } }",
        {"input": inp},
        token,
    )
    return data["createDraft"]["draft"]["id"]


def update_draft(draft_id: str, fm: dict, body: str, token: str) -> None:
    inp = build_input(fm, body) | {"id": draft_id}
    gql(
        "mutation($input: UpdateDraftInput!) { updateDraft(input: $input) { draft { id } } }",
        {"input": inp},
        token,
    )


def update_post(post_id: str, fm: dict, body: str, token: str) -> None:
    inp = build_input(fm, body) | {"id": post_id}
    gql(
        "mutation($input: UpdatePostInput!) { updatePost(input: $input) { post { id } } }",
        {"input": inp},
        token,
    )


def publish_draft(draft_id: str, token: str) -> str:
    data = gql(
        "mutation($input: PublishDraftInput!) { publishDraft(input: $input) { post { id url } } }",
        {"input": {"draftId": draft_id}},
        token,
    )
    return data["publishDraft"]["post"]["url"]


def sync_one(path: Path, host: str, token: str) -> None:
    fm, body = parse_post(path)
    for required in ("title", "slug"):
        if not fm.get(required):
            raise ValueError(f"{path}: frontmatter missing required field '{required}'")
    slug = fm["slug"]
    save_as_draft = truthy(fm.get("saveAsDraft", True))

    pub_id = get_publication_id(host, token)
    post_id = find_published_post_id(host, slug, token)

    if post_id:
        if save_as_draft:
            print(
                f"  [{slug}] already published; updating in place "
                f"(saveAsDraft=true is ignored once a post is live)."
            )
        else:
            print(f"  [{slug}] published post exists; updating.")
        update_post(post_id, fm, body, token)
        return

    draft_id = find_draft_id(pub_id, slug, token)

    if save_as_draft:
        if draft_id:
            print(f"  [{slug}] draft exists ({draft_id}); updating.")
            update_draft(draft_id, fm, body, token)
        else:
            new_id = create_draft(pub_id, fm, body, token)
            print(f"  [{slug}] created draft {new_id}.")
        return

    if not draft_id:
        draft_id = create_draft(pub_id, fm, body, token)
        print(f"  [{slug}] created draft {draft_id} (will publish next).")
    else:
        update_draft(draft_id, fm, body, token)
        print(f"  [{slug}] updated draft {draft_id} (will publish next).")
    url = publish_draft(draft_id, token)
    print(f"  [{slug}] published: {url}")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: sync-to-hashnode.py <path-to-post.md>", file=sys.stderr)
        return 2

    token = os.environ.get("HASHNODE_TOKEN")
    host = os.environ.get("HASHNODE_HOST")
    if not token or not host:
        print("HASHNODE_TOKEN and HASHNODE_HOST env vars are required.", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    sync_one(path, host, token)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

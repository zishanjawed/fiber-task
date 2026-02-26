#!/usr/bin/env python3
"""
Sync model_a.txt and model_b.txt from local TASK_* folders to Notion child pages.
Creates child pages under each TASK page, skipping if they already exist.
"""

import os
import sys
import requests
import time
from pathlib import Path

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

TASK_IDS = {
    1: "3132484b-84ae-81b8-a2cb-deff086bb4d0",
    2: "3132484b-84ae-8156-8da3-d147e36748ea",
    3: "3132484b-84ae-8195-a5a4-e4a232609ec5",
    4: "3132484b-84ae-8194-90ab-fa7c630def92",
    5: "3132484b-84ae-81d3-b976-f8b42819c43d",
    6: "3132484b-84ae-81eb-a9bc-e1470415bb2f",
    7: "3132484b-84ae-81df-abee-e9203676ade7",
    8: "3132484b-84ae-8139-87c6-d49a95e78121",
    9: "3132484b-84ae-812d-9350-c1b871d01b2e",
    10: "3132484b-84ae-811b-a59d-e3e596559c4d",
    11: "3132484b-84ae-81be-a7f8-c7b133653018",
    12: "3132484b-84ae-8184-849a-c4b411dd45c5",
    13: "3132484b-84ae-8194-8a34-f0f133932a0b",
    14: "3132484b-84ae-819b-a6d9-f54aab756169",
    15: "3132484b-84ae-812b-9f1a-fd53b993a1e8",
    16: "3132484b-84ae-81a3-a79d-dbdaa16d24fa",
    17: "3132484b-84ae-8139-904f-c718fcffdbdc",
    18: "3132484b-84ae-81d5-80b3-cd809f4c7578",
    19: "3132484b-84ae-81d4-9e09-cc17e43d99a7",
    20: "3132484b-84ae-8173-a8a1-f4fcc34cb8fe",
}


def get_headers():
    token = os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_KEY")
    if not token:
        raise SystemExit("Error: NOTION_API_KEY or NOTION_KEY environment variable required")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def split_rich_text(content: str, chunk_size: int = 2000):
    """Split content into chunks for Notion rich_text (2000 char limit per object)."""
    chunks = []
    for i in range(0, len(content), chunk_size):
        chunk = content[i : i + chunk_size]
        chunks.append({"type": "text", "text": {"content": chunk}})
    return chunks


def get_existing_children(page_id: str) -> set[str]:
    """List child pages of a Notion page and return their titles."""
    existing = set()
    url = f"{NOTION_API}/blocks/{page_id}/children"
    params = {"page_size": 100}
    while True:
        r = requests.get(url, headers=get_headers(), params=params)
        if r.status_code != 200:
            return existing
        data = r.json()
        for block in data.get("results", []):
            if block.get("type") == "child_page":
                title_val = block.get("child_page", {}).get("title", "")
                if isinstance(title_val, str):
                    existing.add(title_val)
                elif isinstance(title_val, list):
                    parts = [t.get("plain_text", "") for t in title_val if isinstance(t, dict)]
                    existing.add("".join(parts))
                else:
                    existing.add(str(title_val))
        if not data.get("has_next"):
            break
        params["start_cursor"] = data.get("next_cursor")
    return existing


def create_child_page(parent_id: str, title: str, content: str) -> tuple[dict | None, str | None]:
    """Create a child page with content. Returns (page_dict, None) or (None, error_msg)."""
    # Use code block for fidelity - split content into 2000-char rich_text chunks
    rich_text_chunks = split_rich_text(content)
    children = [
        {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": rich_text_chunks,
                "language": "plain text",
            },
        }
    ]
    payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}],
            }
        },
        "children": children,
    }
    r = requests.post(f"{NOTION_API}/pages", headers=get_headers(), json=payload)
    if r.status_code in (200, 201):
        return (r.json(), None)
    err_body = r.text
    try:
        j = r.json()
        err_body = j.get("message", j.get("code", err_body))
    except Exception:
        pass
    return (None, f"{r.status_code}: {err_body}")


def main():
    workspace = Path("/workspace")
    created = 0
    skipped = 0
    errors = []
    sample_urls = []

    for task_num in range(1, 21):
        parent_id = TASK_IDS.get(task_num)
        if not parent_id:
            errors.append(f"TASK_{task_num}: No page ID")
            continue

        task_dir = workspace / f"TASK_{task_num}"
        existing = get_existing_children(parent_id)
        time.sleep(0.35)  # Rate limit

        for filename in ["model_a.txt", "model_b.txt"]:
            if filename in existing:
                skipped += 1
                continue
            filepath = task_dir / filename
            if not filepath.exists():
                errors.append(f"TASK_{task_num}/{filename}: File not found")
                continue
            content = filepath.read_text(encoding="utf-8", errors="replace")
            result, err = create_child_page(parent_id, filename, content)
            time.sleep(0.35)
            if result:
                created += 1
                url = result.get("url", "")
                if url and len(sample_urls) < 5:
                    sample_urls.append(url)
            else:
                errors.append(f"TASK_{task_num}/{filename}: {err or 'Create failed'}")

    print(f"Created: {created}")
    print(f"Skipped (already exist): {skipped}")
    print(f"Errors: {len(errors)}")
    for e in errors:
        print(f"  - {e}")
    print("Sample URLs:")
    for u in sample_urls:
        print(f"  {u}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

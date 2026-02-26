# Notion Sync: model_a.txt and model_b.txt to TASK Pages

This script creates child pages `model_a.txt` and `model_b.txt` under each Notion TASK page (TASK_1 through TASK_20), pasting the full content from local files.

## Prerequisites

1. **Notion Integration**: Create an integration at https://www.notion.so/my-integrations
2. **Share pages**: In Notion, open each TASK page (or the parent MercTask page) and use "Add connections" to connect your integration
3. **API Key**: Copy the "Internal Integration Secret" from your integration

## Usage

```bash
export NOTION_API_KEY="your_integration_secret_here"
pip install -r requirements-notion.txt
python3 sync_notion_pages.py
```

## Behavior

- **Skips** creating `model_a.txt` or `model_b.txt` if a child page with that exact title already exists
- **Creates** child pages with full file content in a code block (plain text) for fidelity
- **Rate limits**: ~0.35s between API calls to respect Notion limits

## Output

The script prints:
- Number of child pages created
- Number skipped (already exist)
- Any errors
- Sample URLs of created pages

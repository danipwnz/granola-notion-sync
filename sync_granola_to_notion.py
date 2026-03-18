import json
import logging
import os
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Optional: pip install -r requirements.txt (requests python-dotenv)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def get_granola_token():
    """Extracts the access token from Granola's supabase.json on Windows."""
    creds_path = Path(os.getenv('APPDATA')) / "Granola" / "supabase.json"
    if not creds_path.exists():
        logger.error(f"Granola credentials not found at {creds_path}")
        return None
    try:
        with open(creds_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # The token is buried inside a JSON string under workos_tokens
            workos_tokens = json.loads(data.get('workos_tokens', '{}'))
            token = workos_tokens.get('access_token')
            if token:
                return token
            logger.error("access_token not found inside workos_tokens")
            return None
    except Exception as e:
        logger.error(f"Error reading {creds_path}: {e}")
        return None

def fetch_granola_docs(token, limit=10):
    """Fetches the latest documents from Granola's internal API."""
    url = "https://api.granola.ai/v2/get-documents"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": "Granola/5.354.0",
        "X-Client-Version": "5.354.0"
    }
    data = {
        "limit": limit,
        "offset": 0,
        "include_last_viewed_panel": True
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get('docs', [])
    except Exception as e:
        logger.error(f"Failed to fetch Granola documents: {e}")
        return []

def prosemirror_to_notion_blocks(node):
    """
    Recursively converts a ProseMirror JSON node (Granola's format)
    into a list of Notion API Block objects.
    """
    blocks = []
    if not isinstance(node, dict):
        return blocks
    
    node_type = node.get('type')
    content = node.get('content', [])

    # Text node (Leaf)
    if node_type == 'text':
        # Handled by parent block parsers usually, 
        # but Notion expects rich_text arrays
        return [{
            "type": "text",
            "text": { "content": node.get('text', '') }
        }]

    # Paragraph
    if node_type == 'paragraph':
        rich_text = []
        for child in content:
            if child.get('type') == 'text':
                rich_text.append({
                    "type": "text",
                    "text": { "content": child.get('text', '') }
                })
        # If empty paragraph, just put a space to avoid Notion API errors
        if not rich_text:
            rich_text.append({"type":"text", "text": {"content": " "}})
            
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": { "rich_text": rich_text }
        })

    # Heading
    elif node_type == 'heading':
        level = node.get('attrs', {}).get('level', 1)
        # Notion only supports heading_1, heading_2, heading_3
        heading_type = f"heading_{min(level, 3)}"
        
        rich_text = []
        for child in content:
            if child.get('type') == 'text':
                rich_text.append({
                    "type": "text",
                    "text": { "content": child.get('text', '') }
                })
        
        if rich_text:
            blocks.append({
                "object": "block",
                "type": heading_type,
                heading_type: { "rich_text": rich_text }
            })

    # Bullet List
    elif node_type == 'bulletList':
        # To handle nested lists in Notion, we technically should attach them as "children"
        # of the bulleted_list_item. But to keep it simple and flat, we process items recursively.
        # It's better to pass a 'depth' param if we wanted flat indentation, or just construct
        # nested blocks. Notion supports children inside a bulleted_list_item.
        
        for item in content:
            if item.get('type') == 'listItem':
                item_content = item.get('content', [])
                
                # First extract the main text for this bullet
                rich_text = []
                nested_children = []
                
                for child in item_content:
                    if child.get('type') == 'paragraph':
                        for text_node in child.get('content', []):
                            if text_node.get('type') == 'text':
                                rich_text.append({
                                    "type": "text",
                                    "text": { "content": text_node.get('text', '') }
                                })
                    elif child.get('type') in ['bulletList', 'orderedList']:
                        # This is a nested list inside the bullet
                        nested_children.extend(prosemirror_to_notion_blocks(child))
                
                if rich_text:
                    block = {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": { "rich_text": rich_text }
                    }
                    if nested_children:
                        block["bulleted_list_item"]["children"] = nested_children
                    
                    blocks.append(block)

    # Other Nodes (e.g., doc root)
    else:
        for child in content:
            blocks.extend(prosemirror_to_notion_blocks(child))
            
    return blocks

SYNCED_FILE = ".synced_notes.json"

def get_synced_ids():
    """Reads the previously synced note IDs from a local JSON file."""
    if not os.path.exists(SYNCED_FILE):
        return []
    try:
        with open(SYNCED_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Could not read {SYNCED_FILE}: {e}")
        return []

def mark_as_synced(note_id, current_synced):
    """Adds a note ID to the local synced file."""
    if note_id not in current_synced:
        current_synced.append(note_id)
        try:
            with open(SYNCED_FILE, "w", encoding='utf-8') as f:
                json.dump(current_synced, f, indent=2)
        except Exception as e:
            logger.error(f"Could not write {SYNCED_FILE}: {e}")

def push_to_notion(doc, blocks, database_id, token):
    """Creates a new page in a Notion database with the parsed blocks."""
    url = 'https://api.notion.com/v1/pages'
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    title = doc.get("title", "Untitled Granola Note")
    created_at = doc.get("created_at") # e.g. "2024-05-08T10:00:00Z"
    
    # We enforce maximum 100 blocks per request due to Notion API limits.
    # If a document is huge, we truncate for this script version.
    truncated_blocks = blocks[:100]

    # Map to Notion Properties (You may need to adjust property names to match your DB)
    data = {
        "parent": { "database_id": database_id },
        "properties": {
            # Assuming 'Name' is your Title column
            "Name": {
                "title": [
                    {
                        "text": { "content": title }
                    }
                ]
            }
        },
        "children": truncated_blocks
    }
    
    # Map Date property (Assumes Notion property is named "Data" or "Date")
    # Change "Data" to your exact Notion column name if different!
    if created_at:
        try:
            # Simple ISO 8601 formatting usually accepted by Notion
            data["properties"]["Data"] = {
                "date": { "start": created_at }
            }
        except Exception:
            pass

    # Optionally, se un giorno avremo la categoria, si potrà mappare qui.
    # Per ora lasciamo che sia l'utente a compilarla su Notion.

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info(f"Successfully pushed '{title}' to Notion.")
        return True
    except Exception as e:
        logger.error(f"Failed to push '{title}' to Notion: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(e.response.json())
        return False

def main():
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        logger.error("Missing Notion credentials. Set NOTION_TOKEN and NOTION_DATABASE_ID in .env")
        return

    logger.info("Starting Granola to Notion Sync...")
    granola_token = get_granola_token()
    if not granola_token:
        return

    # Limite alzato a 200 per prendere uno storico molto ampio
    docs = fetch_granola_docs(granola_token, limit=200)
    logger.info(f"Fetched {len(docs)} documents from Granola.")

    synced_ids = get_synced_ids()

    for doc in reversed(docs): # Process oldest first to keep Notion order logical
        doc_id = doc.get("id")
        title = doc.get("title", "Untitled")
        logger.info(f"Processing: {title}")
        
        if doc_id in synced_ids:
            logger.info(f"Skipping '{title}': Already synced previously.")
            continue
        
        # Navigate Granola's JSON to find the actual note content
        content_to_parse = None
        last_panel = doc.get("last_viewed_panel")
        if last_panel and isinstance(last_panel, dict):
            panel_content = last_panel.get("content")
            if panel_content and isinstance(panel_content, dict) and panel_content.get("type") == "doc":
                content_to_parse = panel_content

        if not content_to_parse:
            logger.warning(f"Skipping '{title}': No parseable content found.")
            continue

        blocks = prosemirror_to_notion_blocks(content_to_parse)
        if not blocks:
            logger.warning(f"Skipping '{title}': Conversion resulted in 0 Notion blocks.")
            continue
            
        success = push_to_notion(doc, blocks, NOTION_DATABASE_ID, NOTION_TOKEN)
        if success:
            mark_as_synced(doc_id, synced_ids)

if __name__ == "__main__":
    main()

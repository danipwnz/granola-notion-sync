import json
import logging
import os
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def get_granola_token():
    creds_path = Path(os.getenv('APPDATA')) / "Granola" / "supabase.json"
    if not creds_path.exists():
        logger.error(f"Granola credentials not found at {creds_path}")
        return None
    try:
        with open(creds_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            workos_tokens = json.loads(data.get('workos_tokens', '{}'))
            return workos_tokens.get('access_token')
    except Exception as e:
        logger.error(f"Error reading {creds_path}: {e}")
        return None

def fetch_granola_docs(token, limit=2):
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
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json().get('docs', [])

def main():
    token = get_granola_token()
    if not token:
        logger.error("Could not get Granola token.")
        return
        
    logger.info("Token retrieved successfully. Fetching notes...")
    docs = fetch_granola_docs(token, limit=3)
    
    logger.info(f"Retrieved {len(docs)} documents.")
    for idx, doc in enumerate(docs):
        title = doc.get("title", "Untitled")
        logger.info(f"[{idx+1}] {title}")
        
        # Dump the first document to a file for analysis
        if idx == 0:
            with open('sample_doc.json', 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2)
            logger.info("Saved sample_doc.json for inspection.")
            
    logger.info("Extraction from Granola works perfectly!")

if __name__ == "__main__":
    main()

import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("NOTION_TOKEN")
db_id = os.getenv("NOTION_DATABASE_ID")

print("Checking Notion DB Access...")
print(f"Token (first 10 chars): {token[:10]}...")
print(f"DB ID: {db_id}")

url = f"https://api.notion.com/v1/databases/{db_id}"
headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28"
}

response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")
try:
    print("Response JSON:")
    print(response.json())
except Exception:
    print(response.text)

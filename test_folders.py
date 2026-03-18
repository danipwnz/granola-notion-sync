import os
import json

def explore_local_files():
    appdata = os.environ.get('APPDATA')
    granola_dir = os.path.join(appdata, 'Granola')
    
    preferences = os.path.join(granola_dir, 'user-preferences.json')
    if os.path.exists(preferences):
        print("--- user-preferences.json ---")
        try:
            print(json.dumps(json.loads(open(preferences, encoding='utf-8').read()), indent=2)[:500])
        except Exception as e:
            print(e)
            
    cache = os.path.join(granola_dir, 'cache-v3.json')
    if os.path.exists(cache):
        print("\n--- cache-v3.json ---")
        try:
            c = json.loads(open(cache, encoding='utf-8').read())
            cache_data = json.loads(c['cache'])
            docs = cache_data.get('documents', {})
            print(f"Found {len(docs)} documents in cache.")
            if docs:
                first_doc_key = list(docs.keys())[0]
                first_doc = docs[first_doc_key]
                print(f"--- Doc {first_doc_key} ---")
                print(json.dumps(first_doc, indent=2)[:1000])
                print("\nAll Keys in Doc:", list(first_doc.keys()))
                
            meetings = cache_data.get('meetingsMetadata', {})
            if meetings:
                first_meet_key = list(meetings.keys())[0]
                print(f"\n--- Meeting {first_meet_key} ---")
                print(json.dumps(meetings[first_meet_key], indent=2)[:500])
        except Exception as e:
            print(e)

if __name__ == '__main__':
    explore_local_files()

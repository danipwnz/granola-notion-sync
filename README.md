# Granola to Notion Sync

This project allows you to automatically synchronize your notes taken via [Granola](https://granola.ai/) directly into a [Notion](https://www.notion.so/) database.

The script reads your Granola authentication token from the local files on your machine (Windows), fetches your notes, converts them into a block-based format (ProseMirror -> Notion), and inserts them into a Notion table.

## How it works
- **Automatic Token Retrieval:** The script retrieves the access token from the native Granola application installed on Windows.
- **Incremental Synchronization:** It keeps track of previously synced notes by saving their IDs in a local `.synced_notes.json` file, preventing duplicates in Notion.
- **Supported Formatting:** Paragraphs, plain text, headings (H1, H2, H3), and bulleted/numbered lists are supported.

---

## 🛠️ Requirements
- **Operating System:** Windows (the script looks for Granola credentials in the `%APPDATA%\Granola` path).
- **Python:** Version 3.8 or higher.

---

## ⚙️ Notion Setup

To allow the script to write to your Notion, you must create an Integration and configure the destination database.

### 1. Create the Notion Integration (To get the `NOTION_TOKEN`)
1. Go to [Notion My Integrations](https://www.notion.so/my-integrations).
2. Click on **"New integration"**.
3. Choose the workspace, name the integration (e.g., "Granola Sync"), and save.
4. Go to the **"Secrets"** tab and copy the **Internal Integration Secret**. This will be your `NOTION_TOKEN`.

### 2. Create the Notion Database (To get the `NOTION_DATABASE_ID`)
Create a new page in Notion and select **"Table"** (or create an "Inline" / "Full page" database).

**Required Column Structure (Case Sensitive):**
- The first column (type **Title**) must be named exactly: **`Name`**
- The second column (type **Date**) must be named exactly: **`Data`** (or "Date" if you renamed the variable inside the python script). You can add other empty columns if you wish (e.g., Category), which you can fill out manually later.

### 3. Connect the Database to the Integration
1. Open the database page you just created.
2. Click on the three dots `...` menu in the top right corner of the page.
3. Click on **Add connections** (or "Connections" > "Connect to").
4. Search for the integration you created ("Granola Sync") and hit enter to add it. Now the API has write permissions!

### 4. Find the Database ID
The Database ID can be found in the URL of your Notion database page.
The URL will look something like this:
`https://www.notion.so/workspace/`**`1234567890abcdef1234567890abcdef`**`?v=...`
The 32-character alphanumeric string before the question mark `?v=` is your `NOTION_DATABASE_ID`.

---

## 🚀 Project Setup

1. Clone this repository to your computer.
2. Rename the `.env.example` file to **`.env`**.
3. Edit the `.env` file by inserting the two keys obtained in the previous steps:
   ```env
   NOTION_TOKEN="secret_..."
   NOTION_DATABASE_ID="your_database_id_string_here"
   ```
4. Open a terminal in the project folder and install the necessary libraries:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🏃‍♂️ How to Run

There are two main ways to run the synchronization script:

1. **Via Command Line:**
   Run the following command in your terminal from the project folder:
   ```bash
   python sync_granola_to_notion.py
   ```
   
2. **Via Batch File (Windows):**
   You can create an executable `.bat` file to run the script with a double click.
   - Rename the `sync_notion.bat.example` file to `sync_notion.bat`
   - Open it with any text editor (like Notepad) and change the path to point to your cloned repository folder on your machine:
     ```bat
     cd /d "C:\your\absolute\path\here"
     ```
   - Double click the newly created `sync_notion.bat` file to run the sync!

Successfully downloaded notes will log their IDs in a `.synced_notes.json` file (ignored by git) to keep track of the process.

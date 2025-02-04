import subprocess
import json
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from utils import call_llm
import sqlite3
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer, util

def execute_task(task: str) -> str:
    # Use an LLM to parse the task and determine the steps
    parsed_task = call_llm(f"Parse the following task and return the steps in JSON format: {task}")
    steps = json.loads(parsed_task)

    # Execute each step
    for step in steps:
        if step["action"] == "install_uv_and_run_script":
            install_uv_and_run_script(task)
        elif step["action"] == "format_markdown_file":
            format_markdown_file()
        elif step["action"] == "count_wednesdays":
            count_wednesdays()
        elif step["action"] == "sort_contacts":
            sort_contacts()
        elif step["action"] == "extract_recent_logs":
            extract_recent_logs()
        elif step["action"] == "create_markdown_index":
            create_markdown_index()
        elif step["action"] == "extract_email_sender":
            extract_email_sender()
        elif step["action"] == "extract_credit_card_number":
            extract_credit_card_number()
        elif step["action"] == "find_similar_comments":
            find_similar_comments()
        elif step["action"] == "calculate_gold_ticket_sales":
            calculate_gold_ticket_sales()
        else:
            raise ValueError(f"Unknown action: {step['action']}")

    return "Task executed successfully"

def install_uv_and_run_script(task: str) -> str:
    # Extract the user email from the task description
    user_email = os.environ.get("USER_EMAIL")
    if not user_email:
        raise ValueError("USER_EMAIL environment variable is not set")

    # Step 1: Install uv if not already installed
    try:
        subprocess.run(["uv", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("uv not found. Installing uv...")
        subprocess.run(["pip", "install", "uv"], check=True)

    # Step 2: Download the script
    script_url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"
    script_path = "/tmp/datagen.py"
    response = requests.get(script_url)
    if response.status_code != 200:
        raise ValueError(f"Failed to download script from {script_url}")
    with open(script_path, "w") as file:
        file.write(response.text)

    # Step 3: Run the script with user.email as the argument
    try:
        subprocess.run(["python", script_path, user_email], check=True)
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Script execution failed: {e}")

    return "Task 1 executed successfully"

def format_markdown_file() -> str:
    # Step 1: Install prettier@3.4.2 if not already installed
    try:
        subprocess.run(["prettier", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("prettier not found. Installing prettier@3.4.2...")
        subprocess.run(["npm", "install", "-g", "prettier@3.4.2"], check=True)

    # Step 2: Format the markdown file
    markdown_file = "/data/format.md"
    if not os.path.exists(markdown_file):
        raise ValueError(f"File {markdown_file} does not exist")
    subprocess.run(["prettier", "--write", markdown_file], check=True)

    return "Task 2 executed successfully"

def count_wednesdays() -> str:
    dates_file = "/data/dates.txt"
    if not os.path.exists(dates_file):
        raise ValueError(f"File {dates_file} does not exist")

    # Read the dates and count Wednesdays
    wednesday_count = 0
    with open(dates_file, "r") as file:
        for line in file:
            date_str = line.strip()
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                if date.weekday() == 2:  # 2 corresponds to Wednesday
                    wednesday_count += 1
            except ValueError:
                continue

    # Write the count to the output file
    output_file = "/data/dates-wednesdays.txt"
    with open(output_file, "w") as file:
        file.write(str(wednesday_count))

    return "Task 3 executed successfully"

def sort_contacts() -> str:
    contacts_file = "/data/contacts.json"
    if not os.path.exists(contacts_file):
        raise ValueError(f"File {contacts_file} does not exist")

    # Read and sort the contacts
    with open(contacts_file, "r") as file:
        contacts = json.load(file)
    contacts_sorted = sorted(contacts, key=lambda x: (x["last_name"], x["first_name"]))

    # Write the sorted contacts to the output file
    output_file = "/data/contacts-sorted.json"
    with open(output_file, "w") as file:
        json.dump(contacts_sorted, file, indent=2)

    return "Task 4 executed successfully"

def extract_recent_logs() -> str:
    logs_dir = "/data/logs"
    if not os.path.exists(logs_dir):
        raise ValueError(f"Directory {logs_dir} does not exist")

    # Find all .log files and sort by modification time
    log_files = list(Path(logs_dir).glob("*.log"))
    log_files_sorted = sorted(log_files, key=os.path.getmtime, reverse=True)

    # Extract the first line of the 10 most recent files
    recent_lines = []
    for log_file in log_files_sorted[:10]:
        with open(log_file, "r") as file:
            first_line = file.readline().strip()
            recent_lines.append(first_line)

    # Write the lines to the output file
    output_file = "/data/logs-recent.txt"
    with open(output_file, "w") as file:
        file.write("\n".join(recent_lines))

    return "Task 5 executed successfully"

def create_markdown_index() -> str:
    docs_dir = Path("/data/docs")
    index = {}
    
    for md_file in docs_dir.rglob("*.md"):
        with open(md_file, "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith("# "):
                    index[str(md_file.relative_to(docs_dir))] = line[2:].strip()
                    break
    
    with open("/data/docs/index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    
    return "Task 6 executed successfully"

def extract_email_sender() -> str:
    email_file = "/data/email.txt"
    if not os.path.exists(email_file):
        raise ValueError(f"File {email_file} does not exist")
    
    with open(email_file, "r", encoding="utf-8") as file:
        email_content = file.read()
    
    sender_email = call_llm(f"Extract the sender's email from this text: {email_content}")
    
    with open("/data/email-sender.txt", "w", encoding="utf-8") as file:
        file.write(sender_email.strip())
    
    return "Task 7 executed successfully"

def extract_credit_card_number() -> str:
    image_path = "/data/credit-card.png"
    if not os.path.exists(image_path):
        raise ValueError(f"File {image_path} does not exist")
    
    image = Image.open(image_path)
    card_number = pytesseract.image_to_string(image, config='--psm 6').replace(" ", "").strip()
    
    with open("/data/credit-card.txt", "w", encoding="utf-8") as file:
        file.write(card_number)
    
    return "Task 8 executed successfully"

def find_similar_comments() -> str:
    comments_file = "/data/comments.txt"
    if not os.path.exists(comments_file):
        raise ValueError(f"File {comments_file} does not exist")
    
    with open(comments_file, "r", encoding="utf-8") as file:
        comments = [line.strip() for line in file if line.strip()]
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(comments, convert_to_tensor=True)
    
    max_sim = -1
    most_similar = (None, None)
    
    for i in range(len(comments)):
        for j in range(i + 1, len(comments)):
            sim = util.pytorch_cos_sim(embeddings[i], embeddings[j]).item()
            if sim > max_sim:
                max_sim = sim
                most_similar = (comments[i], comments[j])
    
    with open("/data/comments-similar.txt", "w", encoding="utf-8") as file:
        file.write("\n".join(most_similar))
    
    return "Task 9 executed successfully"

def calculate_gold_ticket_sales() -> str:
    db_path = "/data/ticket-sales.db"
    if not os.path.exists(db_path):
        raise ValueError(f"Database {db_path} does not exist")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
    result = cursor.fetchone()[0] or 0
    conn.close()
    
    with open("/data/ticket-sales-gold.txt", "w", encoding="utf-8") as file:
        file.write(str(result))
    
    return "Task 10 executed successfully"

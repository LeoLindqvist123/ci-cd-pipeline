import json
import subprocess

# Load the issues from the JSON file
with open("issues.json", encoding="utf-8") as file:  # noqa: UP015
    issues = json.load(file)

print(f"Found {len(issues)} issues to create. Starting...")

for issue in issues:
    title = issue["title"]
    body = issue["body"]
    labels = issue["labels"]

    # Construct the GitHub CLI command
    command = ["gh", "issue", "create", "--title", title, "--body", body, "--label", labels]

    # Run the command
    print(f"Creating: {title}")
    subprocess.run(command)

print("All issues created successfully!")

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from agent.agent import run_agent


app = Flask(__name__)

CORS(app)


@app.get("/")
def index():
    return "Hello, World!"


@app.route("/api/", methods=["POST"])
def handle_request():

    file_list = []
    for _, value in request.files.items():
        content = value.read()  # read once
        files = {
            "name": value.filename,
            "size": len(content),
            "content": content,
            "mimetype": value.mimetype,
        }
        file_list.append(files)

    # Extract question and CSV contents
    question_content = None
    question_file_name = None
    csv_content = None
    csv_file_name = None

    for file in file_list:
        if file["mimetype"] == "text/plain":
            question_content = file["content"]
            question_file_name = file["name"]
        elif file["mimetype"] in ("text/csv", "application/octet-stream"):
            csv_content = file["content"]
            csv_file_name = file["name"]

    # Save to disk
    if question_content:
        with open(f"{question_file_name.split('.')[0]}.txt", "wb") as f:
            f.write(question_content)

    if csv_content:
        with open(f"{csv_file_name.split('.')[0]}.csv", "wb") as f:
            f.write(csv_content)

    # Run the agent

    response = run_agent(question_file_name)

    print("\n\nResponse:", response, "\n\n")

    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

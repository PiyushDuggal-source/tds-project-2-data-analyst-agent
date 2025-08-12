import os
from flask import Flask, request, jsonify

from agent.agent import run_agent


app = Flask(__name__)


@app.route("/api/", methods=["POST"])
def handle_request():
    # Check that questions.txt is present
    # if "questions" not in request.files:
    #     return jsonify({"error": "questions.txt file is required"}), 400
    #
    # Get the required file
    questions_file = request.files["questions.txt"]

    file_list = []
    for key, value in request.files.items():
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
        with open(f"{question_file_name.split('.')[0]}_save.txt", "wb") as f:
            f.write(question_content)

    if csv_content:
        with open(f"{csv_file_name.split('.')[0]}_save.csv", "wb") as f:
            f.write(csv_content)

    # Run the agent

    response = run_agent()

    print("\n\nResponse:", response, "\n\n")

    return jsonify({"response": response})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("tds_project:app", host="0.0.0.0", port=8000, reload=True)

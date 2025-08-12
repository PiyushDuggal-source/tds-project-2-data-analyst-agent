from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
import pandas as pd
import subprocess
import json
import traceback
import os


# tools
@tool("compute_total_tool", parse_docstring=True)
def compute_total(column: str, df: pd.DataFrame) -> float:
    """
    Compute total (sum) of a numeric column in the dataset.

    Args:
      column: Column name
      df: Dataframe

    Returns:
      Total

    """
    return df[column].sum()


@tool("create_file_tool", parse_docstring=True)
def create_file(filename: str, content: str, filetype: str = "python") -> str:
    """
    Create a file with the given content and filetype.

    Args:
      filename: Name of the file (with extension if not Python).
      content: Content of the file.
      filetype: Type of file (e.g., "python", "txt", "json"). Defaults to "python".

    Returns:
      Full path to the created file.
    """
    try:
        if filetype.lower() == "python" and not filename.endswith(".py"):
            filename += ".py"

        # Decode escaped sequences like \n, \t
        decoded = content.encode("utf-8").decode("unicode_escape")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(decoded)

        return f"File created at: {os.path.abspath(filename)}"
    except Exception as e:
        return f"Error creating file: {str(e)}"


@tool("execute_file_tool", parse_docstring=True)
def execute_file(filename: str, filetype: str = "python") -> str:
    """
    Execute a file and return structured JSON output.

    Args:
      filename: File name.
      filetype: File type ("python" preferred).

    Returns:
      JSON string:
        - status: "success" or "error"
        - output: stdout or stderr
        - error_type: name of the exception
        - can_fix_in_code: boolean indicating if error is likely fixable by editing
    """
    try:
        # Choose command based on file type
        if filetype.lower() == "python":
            cmd = ["python", filename]
        else:
            return json.dumps(
                {
                    "status": "error",
                    "output": f"Execution for filetype '{filetype}' not implemented.",
                    "error_type": "UnsupportedFileType",
                    "can_fix_in_code": False,
                },
                ensure_ascii=False,
            )

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return json.dumps(
                {
                    "status": "success",
                    "output": result.stdout.strip(),
                    "error_type": None,
                    "can_fix_in_code": False,
                },
                ensure_ascii=False,
            )

        error_output = result.stderr.strip()
        error_type = None
        can_fix = True

        if "ModuleNotFoundError" in error_output:
            error_type = "ModuleNotFoundError"
            can_fix = False
        elif "FileNotFoundError" in error_output:
            error_type = "FileNotFoundError"
            can_fix = False
        elif any(
            err in error_output
            for err in ["KeyError", "TypeError", "SyntaxError", "NameError"]
        ):
            error_type = error_output.split(":")[0]
            can_fix = True
        else:
            error_type = error_output.split(":")[0]

        return json.dumps(
            {
                "status": "error",
                "output": error_output,
                "error_type": error_type,
                "can_fix_in_code": can_fix,
            },
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps(
            {
                "status": "error",
                "output": str(e) + "\n" + traceback.format_exc(),
                "error_type": e.__class__.__name__,
                "can_fix_in_code": False,
            },
            ensure_ascii=False,
        )


@tool("read_file_tool", parse_docstring=True)
def read_file(filename: str) -> str:
    """
    Read a file and return its content.

    Args:
      filename: File name

    Returns:
      Content of the file

    """
    with open(filename, "r") as f:
        return f.read()


@tool("edit_file_tool", parse_docstring=True)
def edit_file(filename: str, content: str) -> str:
    """
    Edit a file with the given content.

    Args:
      filename: File name
      content: Content of the file

    Returns:
      File path

    """
    with open(filename, "w") as f:
        f.write(content)
    return filename


@tool("extract_table_from_url_tool", parse_docstring=True)
def extract_table_from_url(url: str, table_index: int = 0) -> dict[str, str]:
    """
    Extracts a table from the given URL (like Wikipedia) using pandas.read_html() and stores it in csv with name 'table.csv'.
    Returns a cleaned preview of the table as a string (head of DataFrame).

    Args:
        url (str): The web URL to extract the table from.
        table_index (int): Which table to extract (default is 0, the first one).

    Returns:
        table (str): A cleaned preview of the table as a string (head of DataFrame).
        csv_path (str): The path to the CSV file containing the extracted table.
        error (str): An error message if the table could not be extracted.

    """
    try:
        tables = pd.read_html(url)
        df = tables[table_index]
        df.to_csv("table.csv", index=False)
        return {
            "table": df.head().to_string(),
            "csv_path": "table.csv",
        }
    except Exception as e:
        return {"error": f"Error extracting table from {url}: {e}"}



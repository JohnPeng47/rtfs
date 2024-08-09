import os
import sys
import fnmatch
import argparse

from rtfs.models import OpenAIModel, ModelArguments

api_key = os.getenv("OPENAI_API_KEY")


def print_python_files_content(directory, exclude_patterns=None):
    if exclude_patterns is None:
        exclude_patterns = []

    matched = 0
    files_content = ""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if any(
                    fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns
                ):
                    continue
                matched += 1

                files_content += f"File: {file_path}\n"
                with open(file_path, "r", encoding="utf-8") as f:
                    files_content += f.read()
                    files_content += "\n" + "=" * 40 + "\n"

    return files_content


def invoke(prompt, model="gpt4", dry_run=False):
    try:
        model = OpenAIModel(
            ModelArguments(
                model_name="gpt4",
                api_key=api_key,
            )
        )
        if dry_run:
            return None, model.calc_input_cost(prompt)

        response = model.query_sync(prompt)
        return response, model.stats.total_cost
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        return None, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Print content of all Python files in a given directory."
    )
    parser.add_argument("repo_path", type=str, help="Path to the repository directory")
    parser.add_argument(
        "--output",
        choices=["cost", "content"],
        default="cost",
        help="Output type: 'cost' to show estimated cost, 'content' to print file contents",
    )
    args = parser.parse_args()

    content = print_python_files_content(args.repo_path, exclude_patterns=["alembic"])

    if args.output == "content":
        print(content)
    else:  # args.output == "cost"
        _, cost = invoke(content, dry_run=True)
        print("Total cost: ", cost)

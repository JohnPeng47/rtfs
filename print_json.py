import json


def print_node(node, indent=0):
    title = node.get("title", "No title")
    summary = node.get("summary", "No summary")
    chunks = node.get("chunks", [])
    children = node.get("children", [])

    print(f"{'  ' * indent}Title: {title}")
    # print(f"{'  ' * indent}Summary: {summary}")
    # print(f"{'  ' * indent}Chunks:")
    for chunk in chunks:
        chunk_id = chunk.get("id", "No ID")
        print(f"{'  ' * indent}- {chunk_id}")

    for child in children:
        # print()  # Empty line before each child
        print_node(child, indent + 1)


def parse_and_print_json(json_list):
    for data in json_list:
        try:
            print_node(data)
            print()  # Empty line for separation between top-level items
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in item: {data}")
        except Exception as e:
            print(f"Error processing item: {e}")


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Parse and print JSON from a file.")
    parser.add_argument("file", help="Path to the JSON file")
    args = parser.parse_args()

    try:
        with open(args.file, "r") as f:
            json_list = f.read()

        parse_and_print_json(json.loads(json_list))
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied when trying to read '{args.file}'.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

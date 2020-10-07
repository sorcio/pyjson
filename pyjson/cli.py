import argparse
import json

from .parser import Parser, BuildObjectHandler
from .scanner import Scanner


def main():
    parser = argparse.ArgumentParser(
        description="Extract JSON documents from a source file."
    )
    parser.add_argument(
        "script", type=argparse.FileType("rt"), help="a source file to parse"
    )
    args = parser.parse_args()
    parse_file(args.script)


def parse_file(file):
    text = file.read()
    file.close()
    parse(text)


def parse(source):
    scanner = Scanner(source)
    handler = BuildObjectHandler()
    parser = Parser(scanner, handler)
    parser.parse()
    for doc in handler.top_level:
        print("\n--- found json ---\n")
        print(json.dumps(doc))


if __name__ == "__main__":
    main()

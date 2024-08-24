def get_md_help():
    os.environ["COLUMNS"] = "70"
    sys.argv = ["aider"]
    parser = get_parser([], None)

    # This instantiates all the action.env_var values
    parser.parse_known_args()

    parser.formatter_class = MarkdownHelpFormatter # fails to resolve MarkdownHelpFormatter

    return argparse.ArgumentParser.format_help(parser)
    return parser.format_help()

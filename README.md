# How it works
1. Chunk code using custom code chunker (stolen from Moatless)
2. Generate dep graph (partly stolen from Bloop)
3. Cluster chunks together using multi-level graph clustering algo (basically identifies local communities that are more related amongst each other than they are with outside nodes)
4. Recursively generate summaries from leaf to root

What the clusters represent are functional groupings of code that inter-depend on each other (ie. Web Content Scraping and Integration Feature).

Generation is relatively cheap, fraction of the cost of the ingesting the whole repo

# Install

OPENAI_API_KEY must be set in the env to use 
```
pip install rtfs
```

# Get text output to console
```
rtfs chunk-graph tests\cowboy-server\

...
# accept the summarization charge (we are not summarizing over every single file)
The summarization will cost $0.023670999999999998 and use 23671 tokens. Do you want to proceed? (yes/no): yes
```

# Get json output
```
rtfs chunk-graph tests\cowboy-server\ --output-format json --output-file json- 
```

# Sample output
```
Chat Interaction and Summarization Handler 0:12
Keywords: Coder, ChatSummary
Summary: This set of code is responsible for managing chat interactions with AI models, including sending messages, handling responses, and summarizing chat content. The `Coder` class handles the flow of sending messages to the models, managing partial responses, logging the interactions, and processing interruptions. It also checks for file mentions within the messages and handles them appropriately. The `ChatSummary` class focuses on summarizing chat content by compiling user and assistant messages and then interacting with AI models to generate a concise summary. Utility functions like `send_with_retries` and `simple_send_with_retries` ensure robust and retriable communication with the AI models.
  ChunkNode: coders/base_coder.py#38.63
  ChunkNode: aider/history.py#167.25
  ChunkNode: aider/sendchat.py#249.48
File Content Replacement and Editing 0:17
Keywords: do_replace, EditBlockFunctionCoder
Summary: This feature provides functionality for text replacements and bulk edits within files. The `do_replace` function handles the core logic of replacing text within a file, either by creating a new file if it doesn't exist or updating the content by replacing a specified text chunk with new content. The `EditBlockFunctionCoder` class manages bulk edit operations by parsing arguments, validating edit requests, and invoking the `do_replace` function to perform the content replacements. It ensures that file paths are allowed for editing and handles exceptions for missing or incorrect parameters using the `get_arg` function. This feature is primarily used for automating text updates in multiple files while maintaining file integrity.
  ChunkNode: coders/editblock_coder.py#60.19
  ChunkNode: coders/editblock_func_coder.py#69.47
Chat History Analysis and Patch Application 0:4
Keywords: main, map_patches
Summary: This feature encompasses several utility functions and classes to analyze chat history markdown to generate diffs and apply patches to texts. The `main` function reads a markdown file containing chat history and identifies patches by analyzing diffs between the states. Functions like `map_patches`, `dmp_apply`, and `dmp_lines_apply` manage the application of these patches to ensure accurate mapping and transformation of text changes. There are also utility functions for dealing with general patch management, such as `find_diffs`, and `show_stats` for statistical analysis and visualization. Additional code sections cover the creation of graphical representations of the results and handling exceptions during such operations
```

from setuptools import Extension, find_packages, setup

# TODO: figure out how to run npm run build
setup(
    name="rtfs",
    version="0.0.27",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "rtfs": [
            "languages/**/*.so",
            "languages/**/*.json",
            "languages/**/*.scm",
            "moatless/**/*.scm",
        ],
    },
    description="Code Repo Summary Generator",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    author="John Peng",
    author_email="kongyijipeng@gmail.com",
    install_requires=[
        "anthropic==0.32.0",
        "infomap==2.8.0",
        "intervaltree==3.1.0",
        "llama_index==0.10.59",
        "networkx==3.3",
        "openai==1.38.0",
        "pydantic==2.8.2",
        "python-dotenv==1.0.1",
        "PyYAML==6.0.1",
        "setuptools==70.1.1",
        "simple_parsing==0.1.5",
        "starlette==0.38.2",
        "tenacity==8.5.0",
        "tiktoken==0.7.0",
        "tree_sitter==0.22.3",
        "tree_sitter_java==0.21.0",
        "tree_sitter_python==0.21.0",
        "typing_extensions==4.12.2",
    ],
    entry_points={
        "console_scripts": [
            "rtfs = rtfs.cli:cli",
        ],
    },
    python_requires=">=3.8",
)

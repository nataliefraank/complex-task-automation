# Web browsing automation loop example

This is an example of a program that uses guidance from an LLM to navigate a website according to a defined goal, keeping track of the actions it took to get there.
It uses [Playwright](https://playwright.dev/) for browser automation and interfaces with any supported LLM through the [llm library](https://llm.datasette.io/).

## Setup

### Dependencies

Use the [uv Python package manager](https://docs.astral.sh/uv/) to install the right dependencies and correct version of Python:

```sh
uv sync
```

### LLM

To run the script, you'll need to configure the LLM model via the [llm library](https://llm.datasette.io/).
By default, it currently hard-codes Gemini 2.5 Flash because it's [cheap](https://llm-prices.com/) and seems to work okay (at least in my very simple tests). If you want to stick with it, you'll need to [configure the keys](https://llm.datasette.io/en/stable/setup.html#api-key-management), for example by running:

```sh
uv run llm keys set gemini
```

If you'd like to switch to another provider, you'll want to install the appropriate plugin then set up its keys.
For example, [for Anthropic](https://github.com/simonw/llm-anthropic):

```sh
uv add llm-anthropic
uv run llm keys set anthropic
```

Then, don't forget to update the model name in the code.


## Run

There are two primary ways to run the code.

### VS Code (Jupyter Cells)

The script is formatted with `# %%` cell separators to allow interactive execution using the [Jupyter code cells feature](https://code.visualstudio.com/docs/python/jupyter-support-py#_jupyter-code-cells) in Visual Studio Code.
This allows you to run the script interactively, debugging as necessary.
To do this, you will need the Python and Jupyter extensions for VS Code.

### Command-line runner

Because the script uses top-level `await`, it cannot be run directly. A helper script, `async_run.py`, is provided to wrap the code in an `async` function and execute it.

To run the script from your terminal, use `uv run`:

```sh
uv run async_run.py browse.py
```

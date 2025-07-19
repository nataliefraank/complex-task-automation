"""
Given a Python file that has top-level async code, executes it by first wrapping it in a main function.

The use case is that VS Code has Jupyter cells, which let you run top-level async code. But then running that source file directly from CLI doesn't work because Python doesn't support top-level await.
This hacks around that by automatically wrapping all of the code in a main function that is then run in an asyncio loop.
"""

import sys
import textwrap
import asyncio
import traceback

# Template structure
template = """
import asyncio
import sys

# Make sure the embedded code uses the correct event loop context
# sys.stdout and sys.stderr should be inherited from the parent process

async def main():
{indented_code}

if __name__ == "__main__":
    try:
        # Use the already running loop if available, otherwise create a new one.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError: # No running loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Execute the main coroutine from the embedded script
        loop.run_until_complete(main())

    except Exception as e_exec:
        print(f"Error during execution of embedded script:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
"""

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <target_script.py>", file=sys.stderr)
        sys.exit(1)

    target_script_path = sys.argv[1]

    try:
        with open(target_script_path, "r", encoding="utf-8") as f:
            target_code = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {target_script_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file {target_script_path}: {e}", file=sys.stderr)
        sys.exit(1)

    indented_code = textwrap.indent(target_code, "    ")

    final_code = template.format(indented_code=indented_code)

    # Define globals for execution, setting __name__ to '__main__'
    # This also makes modules imported here (like asyncio) available if needed,
    # though the template re-imports them for clarity within the exec scope.
    exec_globals = {
        "__name__": "__main__",
        "__file__": target_script_path,  # Mimic script environment
        # Include builtins and potentially other necessary globals
        "asyncio": asyncio,
        "sys": sys,
        "traceback": traceback,
    }

    try:
        exec(final_code, exec_globals)
    except SystemExit:
        # Allow sys.exit() within the executed code to function correctly
        raise
    except Exception:
        print(
            f"Error preparing or executing generated code for {target_script_path}:",
            file=sys.stderr,
        )
        traceback.print_exc()
        sys.exit(1)

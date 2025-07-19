# type: ignore
# ruff: noqa: F704
# %%

import llm
from playwright.async_api import async_playwright
from sclog import getLogger

logger = getLogger(__name__)

# %%
# Set up Playwright
playwright = async_playwright()
p = await playwright.__aenter__()
browser = await p.chromium.launch(channel="chrome", headless=False)
context = await browser.new_context(viewport={"width": 1440, "height": 1700})
await context.tracing.start(screenshots=True, snapshots=True, sources=True)
page = await context.new_page()
page.set_default_timeout(8000)


async def get_html() -> str:
    return await page.locator("body").inner_html()


# %%
await page.goto("https://www.example.com/")

# %%
MODEL = "gemini-2.5-flash"
model = llm.get_async_model(MODEL)

# %%

history: list[tuple[str, str]] = []


async def click(selector: str, description: str = "") -> str:
    """
    Given a CSS or XPATH selector, clicks on that element.

    **If multiple elements match the selector, this will error, so it's crucial to be unambiguous!**
    For extra clarity, prefix `css=` or `xpath=`.
    Examples: `css=button`, `xpath=//button`

    :param selector: The CSS or XPATH selector to click.
    :param description: A plain-language description of the selector for logging.
    :return: The new HTML content of the page after the click.
    """
    logger.debug(f"Clicking on {description} ({selector})")
    try:
        await page.locator(selector).click()

        history.append(("click", selector))

        await page.screenshot(path=f"screenshots/screenshot-{len(history)}.png")
    except TimeoutError as e:
        logger.warning(f"Clicking on {selector} failed. Will tell LLM about it..")
        raise e

    return await get_html()


async def go_back() -> str:
    """
    Go back to the previous page in the browser history.

    :return: The new HTML content of the page after going back.
    """
    logger.debug("Going back in browser history")
    await page.go_back()
    history.append(("back", ""))
    return await get_html()


def should_continue(skip_count: int) -> tuple[bool, int]:
    """
    Asks the user for confirmation to continue, with an option to skip confirmations.

    :param skip_count: The number of confirmations to skip.
    :return: A tuple containing a boolean (True to continue, False to exit)
             and the updated skip count.
    """
    if skip_count > 0:
        logger.info(f"Skipping confirmation ({skip_count - 1} left)...")
        return True, skip_count - 1

    try:
        confirm = (
            input("Continue? (Y/n or number of prompts to skip) > ").lower().strip()
        )
        if confirm.startswith("n"):
            print("Exiting.")
            return False, 0
        elif confirm.isdigit():
            return True, int(confirm)
        elif confirm != "" and not confirm.startswith("y"):
            print("Invalid input, exiting.")
            return False, 0
    except EOFError:
        print("\nExiting.")
        return False, 0

    return True, 0


tools = [click, go_back]
conversation = model.conversation(tools=tools)

SYSTEM_PROMPT = """You are an AI-enabled program with excellent understanding of HTML/CSS and no personality.

I am providing you with the HTML of the page I'm currently on.
Using the tools available, navigate the website.
(You will need to click on things to leave the first page!)

YOUR GOAL is to find and return to me the authors of the RFC ending in 61 that you find.

At the end, output only your answer.

This is not an interactive session, so do not try to ask me questions or expect responses.
Don't forget that you can navigate the website using the tools I provide.
"""

response = await conversation.prompt(
    prompt=await get_html(),
    system=SYSTEM_PROMPT,
    tools=tools,  # this shouldn't be necessary, but there's a bug in the llm library in AsyncConversation
)
logger.debug(f"Initial response: {await response.text()}")

skip_confirmation_for = 0
while True:
    tool_calls = await response.tool_calls()
    logger.debug(f"Tool calls: {tool_calls}")
    if not tool_calls:
        break

    tool_results = await response.execute_tool_calls()

    do_continue, skip_confirmation_for = should_continue(skip_confirmation_for)
    if not do_continue:
        break

    response = conversation.prompt(
        system=SYSTEM_PROMPT,
        tool_results=tool_results,
        tools=tools,  # again, this is here because of a bug in llm
    )

    logger.debug(f"Response: {await response.text()}")

print(f"Final response: {await response.text()}")

print("\nSteps:")
for action, value in history:
    print(f"- {action}: {value}")

# %%
# Clean up Playwright context
await page.close()
await context.tracing.stop(path="trace.zip")
await context.close()
await browser.close()
await playwright.__aexit__()

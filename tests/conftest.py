"""
conftest.py — shared Playwright fixtures for F1 login tests.

The `authenticated_page` fixture logs in ONCE per test session and
stores the browser storage state in a temp file. Every test that
needs an authenticated page re-uses that state without re-logging in.
"""

import os
import json
import tempfile
import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

load_dotenv()

F1_LOGIN_URL = "https://account.formula1.com/#/en/login"
F1_HOME_URL  = "https://www.formula1.com/"

EMAIL    = os.getenv("F1_EMAIL")
PASSWORD = os.getenv("F1_PASSWORD")


# ── Helpers ────────────────────────────────────────────────────────────────────

def dismiss_popups(page: Page) -> None:
    """Dismiss any overlay that might block interaction.

    Handles:
    - Cookie consent banner  (Accept / Agree button)
    - Survey / feedback modal (Close / X button)
    - Generic overlay close buttons
    """
    selectors = [
        "button:has-text('Accept')",
        "button:has-text('Accept All')",
        "button:has-text('Agree')",
        "button:has-text('Close')",
        "button[aria-label='Close']",
        "button[aria-label='close']",
        "[data-cy='close-button']",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=1500):
                btn.click()
                page.wait_for_timeout(500)
        except Exception:
            pass


def do_login(page: Page) -> None:
    """Fill in credentials and submit the login form."""
    assert EMAIL and PASSWORD, (
        "Credentials not found. Did you create a .env file? "
        "See .env.example for the format."
    )
    page.goto(F1_LOGIN_URL)
    page.wait_for_selector("input[name='Login']", timeout=10_000)

    dismiss_popups(page)

    page.locator("input[name='Login']").fill(EMAIL)
    page.locator("input[name='Password']").fill(PASSWORD)
    page.get_by_role("button", name="Sign In").click()

    # Wait for redirect back to formula1.com after successful login
    page.wait_for_url("**/formula1.com/**", timeout=15_000)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_session():
    """Single browser instance shared across the whole test session."""
    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch(headless=False)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def auth_state_file(browser_session: Browser):
    """Log in once, save storage state to a temp file, yield its path."""
    context: BrowserContext = browser_session.new_context()
    page: Page = context.new_page()

    do_login(page)

    # Persist cookies + localStorage so other tests skip re-login
    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w"
    ) as f:
        state = context.storage_state()
        json.dump(state, f)
        state_path = f.name

    context.close()
    yield state_path

    os.unlink(state_path)   # cleanup after session


@pytest.fixture()
def authenticated_page(browser_session: Browser, auth_state_file: str):
    """Fresh page with pre-authenticated state loaded from storage."""
    context: BrowserContext = browser_session.new_context(
        storage_state=auth_state_file
    )
    page: Page = context.new_page()
    yield page
    context.close()

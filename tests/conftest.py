"""
conftest.py — shared fixtures for F1 login tests.

Run tests with:  python -m pytest tests/test_login_flow.py -v
No --browser flag needed.
"""

import os
import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page

load_dotenv()

F1_LOGIN_URL = "https://account.formula1.com/#/en/login"
F1_HOME_URL  = "https://www.formula1.com/"
EMAIL        = os.getenv("F1_EMAIL")
PASSWORD     = os.getenv("F1_PASSWORD")


def dismiss_popups(page: Page) -> None:
    """Dismiss cookie/consent popups.

    The F1 consent banner lives inside an iframe (id starts with
    'sp_message_iframe'). We use frame_locator to reach inside it.
    Also handles the survey dialog that appears on some page loads.
    """
    # 1. Iframe-based consent popup (SP Consent Message)
    try:
        frame = page.frame_locator('iframe[id^="sp_message_iframe"]')
        for btn_name in ["Accept all", "Accept All", "Essential only cookies"]:
            btn = frame.get_by_role("button", name=btn_name)
            if btn.is_visible(timeout=2_000):
                btn.click()
                page.wait_for_timeout(600)
                return
    except Exception:
        pass

    # 2. Survey / alertdialog on the main page
    try:
        close_btn = page.locator('button[aria-label="Close"], button:has-text("Close")')
        if close_btn.first.is_visible(timeout=1_000):
            close_btn.first.click()
            page.wait_for_timeout(400)
    except Exception:
        pass


def wait_for_login_success(page: Page, timeout: int = 20_000) -> None:
    """Wait until the page navigates away from the login URL.

    After successful login F1 redirects to account.formula1.com/#/en/
    (NOT www.formula1.com), so we just check the hash fragment changes.
    """
    page.wait_for_function(
        "window.location.hash !== '#/en/login'",
        timeout=timeout,
    )


# ── Session-scoped browser (one instance for all tests) ───────────────────────

@pytest.fixture(scope="session")
def _browser():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=150)
        yield browser
        browser.close()


# ── page fixture ──────────────────────────────────────────────────────────────

@pytest.fixture
def page(_browser):
    """Fresh browser page for each test."""
    context = _browser.new_context()
    p = context.new_page()
    yield p
    context.close()


# ── authenticated_page — logs in once, reuses state ───────────────────────────

@pytest.fixture(scope="session")
def _auth_state(_browser):
    """Login once per session, capture storage state for reuse."""
    assert EMAIL and PASSWORD, (
        "Credentials missing! Create a .env file based on .env.example\n"
        "F1_EMAIL=\"your@email.com\"\n"
        "F1_PASSWORD=\"yourpassword\""
    )
    context = _browser.new_context()
    p = context.new_page()

    p.goto(F1_LOGIN_URL)
    p.wait_for_selector("input[name='Login']", timeout=15_000)
    dismiss_popups(p)

    p.locator("input[name='Login']").fill(EMAIL)
    p.locator("input[name='Password']").fill(PASSWORD)
    p.get_by_role("button", name="Sign In").click()

    # Wait for redirect away from login page (goes to account.formula1.com/#/en/)
    wait_for_login_success(p, timeout=20_000)

    state = context.storage_state()
    context.close()
    return state


@pytest.fixture
def authenticated_page(_browser, _auth_state):
    """Page pre-loaded with logged-in session — no re-login per test."""
    context = _browser.new_context(storage_state=_auth_state)
    p = context.new_page()
    yield p
    context.close()

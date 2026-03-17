"""
conftest.py — shared fixtures for F1 login tests.

DESIGN: All fixtures use sync_playwright directly so tests can be run
with a plain:  python -m pytest tests/test_login_flow.py -v
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

    The F1 consent banner lives inside an iframe — we must use
    frame_locator to reach inside it.
    """
    # 1. Iframe-based consent popup (most common on formula1.com)
    try:
        frame = page.frame_locator('iframe[id^="sp_message_iframe"]')
        btn = frame.get_by_role("button", name="Accept All")
        if btn.is_visible(timeout=3_000):
            btn.click()
            page.wait_for_timeout(500)
            return
    except Exception:
        pass

    # 2. Fallback — regular page-level buttons
    for text in ["Accept All", "Accept", "Agree", "OK"]:
        try:
            btn = page.get_by_role("button", name=text)
            if btn.first.is_visible(timeout=1_000):
                btn.first.click()
                page.wait_for_timeout(400)
                return
        except Exception:
            pass


# ── Session-scoped browser (launched once for all tests) ──────────────────────

@pytest.fixture(scope="session")
def _browser():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        yield browser
        browser.close()


# ── page fixture — replaces pytest-playwright's built-in one ──────────────────

@pytest.fixture
def page(_browser):
    """Fresh browser page for each test. No --browser flag needed."""
    context = _browser.new_context()
    p = context.new_page()
    yield p
    context.close()


# ── authenticated_page — logs in once, reuses state ──────────────────────────

@pytest.fixture(scope="session")
def _auth_state(_browser):
    """Login once per session and save storage state (cookies + localStorage)."""
    assert EMAIL and PASSWORD, (
        "Credentials missing! Create a .env file based on .env.example"
    )
    context = _browser.new_context()
    p = context.new_page()

    p.goto(F1_LOGIN_URL)
    p.wait_for_selector("input[name='Login']", timeout=15_000)
    dismiss_popups(p)

    p.locator("input[name='Login']").fill(EMAIL)
    p.locator("input[name='Password']").fill(PASSWORD)
    p.get_by_role("button", name="Sign In").click()
    p.wait_for_url("**/formula1.com/**", timeout=20_000)

    state = context.storage_state()
    context.close()
    return state


@pytest.fixture
def authenticated_page(_browser, _auth_state):
    """Page pre-loaded with logged-in cookies — no re-login per test."""
    context = _browser.new_context(storage_state=_auth_state)
    p = context.new_page()
    yield p
    context.close()

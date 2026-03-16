"""
test_login_flow.py

Tests the F1 account login journey:
  - Popup handling (cookie banner, survey modal)
  - Successful login with valid credentials
  - Failed login with wrong password
  - Redirect after login lands on formula1.com
"""

import os
import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page, expect

from conftest import F1_LOGIN_URL, dismiss_popups

load_dotenv()

EMAIL    = os.getenv("F1_EMAIL")
PASSWORD = os.getenv("F1_PASSWORD")


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_login_page_loads(page: Page):
    """Login page must load with the Sign In heading and both input fields."""
    page.goto(F1_LOGIN_URL)
    dismiss_popups(page)

    expect(page.get_by_role("heading", name="Sign In")).to_be_visible()
    expect(page.locator("input[name='Login']")).to_be_visible()
    expect(page.locator("input[name='Password']")).to_be_visible()
    expect(page.get_by_role("button", name="Sign In")).to_be_visible()


def test_login_with_valid_credentials(page: Page):
    """Successful login should redirect to formula1.com."""
    page.goto(F1_LOGIN_URL)
    page.wait_for_selector("input[name='Login']", timeout=10_000)
    dismiss_popups(page)

    page.locator("input[name='Login']").fill(EMAIL)
    page.locator("input[name='Password']").fill(PASSWORD)
    page.get_by_role("button", name="Sign In").click()

    # After login, F1 redirects back to the main site
    page.wait_for_url("**/formula1.com/**", timeout=15_000)
    assert "formula1.com" in page.url, (
        f"Expected redirect to formula1.com after login, got: {page.url}"
    )


def test_login_with_wrong_password(page: Page):
    """Wrong password should show an error — not log in."""
    page.goto(F1_LOGIN_URL)
    page.wait_for_selector("input[name='Login']", timeout=10_000)
    dismiss_popups(page)

    page.locator("input[name='Login']").fill(EMAIL)
    page.locator("input[name='Password']").fill("WrongPassword999!")
    page.get_by_role("button", name="Sign In").click()

    # Should stay on the login page and show an error message
    page.wait_for_timeout(3_000)
    assert "account.formula1.com" in page.url, (
        "Expected to stay on login page after wrong password"
    )
    error = page.locator("text=Invalid").or_(
        page.locator("text=incorrect")
    ).or_(
        page.locator("text=error")
    )
    expect(error.first).to_be_visible(timeout=5_000)


def test_popup_dismissed_before_login(page: Page):
    """Any popup/overlay on the login page must be dismissible before interacting."""
    page.goto(F1_LOGIN_URL)
    page.wait_for_selector("input[name='Login']", timeout=10_000)

    dismiss_popups(page)

    email_input = page.locator("input[name='Login']")
    expect(email_input).to_be_visible()
    expect(email_input).to_be_enabled()

"""
test_login_flow.py — F1 login journey tests.

Run with:  python -m pytest tests/test_login_flow.py -v
"""

import os
from dotenv import load_dotenv
from playwright.sync_api import expect
from conftest import F1_LOGIN_URL, dismiss_popups, wait_for_login_success

load_dotenv()
EMAIL    = os.getenv("F1_EMAIL")
PASSWORD = os.getenv("F1_PASSWORD")


def test_login_page_loads(page):
    """Login page loads with heading and both input fields visible."""
    page.goto(F1_LOGIN_URL)
    page.wait_for_selector("input[name='Login']", timeout=10_000)
    dismiss_popups(page)

    expect(page.get_by_role("heading", name="Sign In")).to_be_visible()
    expect(page.locator("input[name='Login']")).to_be_visible()
    expect(page.locator("input[name='Password']")).to_be_visible()
    expect(page.get_by_role("button", name="Sign In")).to_be_visible()


def test_login_with_valid_credentials(page):
    """Valid credentials should navigate away from the login page."""
    page.goto(F1_LOGIN_URL)
    page.wait_for_selector("input[name='Login']", timeout=10_000)
    dismiss_popups(page)

    page.locator("input[name='Login']").fill(EMAIL)
    page.locator("input[name='Password']").fill(PASSWORD)
    page.get_by_role("button", name="Sign In").click()

    # F1 redirects to account.formula1.com/#/en/ after login
    # (NOT www.formula1.com) — we just check the hash changes
    wait_for_login_success(page, timeout=20_000)
    assert "/en/login" not in page.url, (
        f"Still on login page after valid credentials — URL: {page.url}"
    )


def test_login_with_wrong_password(page):
    """Wrong password must keep user on login page and show an error."""
    page.goto(F1_LOGIN_URL)
    page.wait_for_selector("input[name='Login']", timeout=10_000)
    dismiss_popups(page)

    page.locator("input[name='Login']").fill(EMAIL)
    page.locator("input[name='Password']").fill("WrongPassword999!")
    page.get_by_role("button", name="Sign In").click()

    page.wait_for_timeout(4_000)
    assert "/en/login" in page.url, (
        "Should stay on login page after wrong password"
    )
    error = (
        page.locator("text=Invalid")
        .or_(page.locator("text=incorrect"))
        .or_(page.locator("text=wrong"))
        .or_(page.locator("text=error"))
    )
    expect(error.first).to_be_visible(timeout=5_000)


def test_popup_dismissed_before_login(page):
    """Cookie popup must be dismissed before login form is interactable."""
    page.goto(F1_LOGIN_URL)
    page.wait_for_selector("input[name='Login']", timeout=10_000)
    dismiss_popups(page)

    email_input = page.locator("input[name='Login']")
    expect(email_input).to_be_visible()
    expect(email_input).to_be_enabled()

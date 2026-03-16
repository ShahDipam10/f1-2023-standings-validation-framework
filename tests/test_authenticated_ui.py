"""
test_authenticated_ui.py

Tests UI elements that are ONLY visible to a logged-in user.
Uses the `authenticated_page` fixture from conftest.py which
loads pre-saved login state — no re-login needed per test.
"""

import pytest
from playwright.sync_api import Page, expect

from conftest import F1_HOME_URL, dismiss_popups


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_sign_in_button_gone_after_login(authenticated_page: Page):
    """'Sign In' link in the nav should NOT be visible when logged in."""
    authenticated_page.goto(F1_HOME_URL)
    dismiss_popups(authenticated_page)

    sign_in = authenticated_page.locator("a:has-text('Sign In')").first
    assert not sign_in.is_visible(timeout=3_000), (
        "'Sign In' link is still visible — user may not be logged in"
    )


def test_user_account_element_visible_after_login(authenticated_page: Page):
    """An account-related element (avatar, name, or 'Sign Out') must appear when logged in."""
    authenticated_page.goto(F1_HOME_URL)
    dismiss_popups(authenticated_page)

    account_indicator = (
        authenticated_page.locator("[aria-label='My Account']")
        .or_(authenticated_page.locator("text=My Account"))
        .or_(authenticated_page.locator("text=Sign Out"))
        .or_(authenticated_page.locator("[data-cy='user-avatar']"))
    )
    expect(account_indicator.first).to_be_visible(timeout=8_000)


def test_logout_flow(authenticated_page: Page):
    """Clicking Sign Out should return the user to a logged-out state."""
    authenticated_page.goto(F1_HOME_URL)
    dismiss_popups(authenticated_page)

    try:
        authenticated_page.locator("[aria-label='My Account']").first.click()
        authenticated_page.wait_for_timeout(1_000)
    except Exception:
        pass

    sign_out = authenticated_page.get_by_role("link", name="Sign Out").or_(
        authenticated_page.get_by_role("button", name="Sign Out")
    )
    expect(sign_out.first).to_be_visible(timeout=5_000)
    sign_out.first.click()

    authenticated_page.wait_for_timeout(3_000)
    expect(
        authenticated_page.locator("a:has-text('Sign In')").first
    ).to_be_visible(timeout=8_000)

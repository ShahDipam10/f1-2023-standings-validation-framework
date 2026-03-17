"""
test_authenticated_ui.py — UI tests for logged-in state.

Run with:  python -m pytest tests/test_authenticated_ui.py -v
"""

from playwright.sync_api import expect
from conftest import F1_HOME_URL, dismiss_popups


def test_sign_in_button_gone_after_login(authenticated_page):
    """'Sign In' link should NOT be visible when logged in."""
    authenticated_page.goto(F1_HOME_URL)
    authenticated_page.wait_for_timeout(3_000)
    dismiss_popups(authenticated_page)

    sign_in = authenticated_page.locator("a:has-text('Sign In')").first
    assert not sign_in.is_visible(timeout=3_000), (
        "'Sign In' still visible — user may not be logged in"
    )


def test_user_account_visible_after_login(authenticated_page):
    """A user account element must appear when logged in."""
    authenticated_page.goto(F1_HOME_URL)
    authenticated_page.wait_for_timeout(3_000)
    dismiss_popups(authenticated_page)

    account = (
        authenticated_page.locator("a:has-text('Sign Out')")
        .or_(authenticated_page.locator("button:has-text('Sign Out')"))
        .or_(authenticated_page.locator("[aria-label='My Account']"))
        .or_(authenticated_page.locator("text=My Account"))
    )
    expect(account.first).to_be_visible(timeout=8_000)


def test_logout_flow(authenticated_page):
    """Sign Out should return user to logged-out state."""
    authenticated_page.goto(F1_HOME_URL)
    authenticated_page.wait_for_timeout(3_000)
    dismiss_popups(authenticated_page)

    # Try to open account menu first (in case Sign Out is inside a dropdown)
    try:
        menu = authenticated_page.locator("[aria-label='My Account']").first
        if menu.is_visible(timeout=2_000):
            menu.click()
            authenticated_page.wait_for_timeout(1_000)
    except Exception:
        pass

    sign_out = (
        authenticated_page.get_by_role("link", name="Sign Out")
        .or_(authenticated_page.get_by_role("button", name="Sign Out"))
    )
    expect(sign_out.first).to_be_visible(timeout=5_000)
    sign_out.first.click()

    authenticated_page.wait_for_timeout(3_000)
    expect(
        authenticated_page.locator("a:has-text('Sign In')").first
    ).to_be_visible(timeout=8_000)

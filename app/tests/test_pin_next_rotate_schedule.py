from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch


def test_pin_rotates_when_next_rotate_at_due_and_auto_rotate_enabled():
    from src.auth import get_or_rotate_pin

    fixed_now = datetime(2026, 1, 24, 12, 0, 0)
    cfg = {
        'view_pin': '111111',
        'pin_auto_rotate': True,
        'pin_rotate_hours': 24,
        'pin_last_rotate': fixed_now - timedelta(days=2),
        'pin_next_rotate_at': (fixed_now - timedelta(minutes=1)).isoformat(),
    }

    with (
        patch('src.auth.secrets.randbelow', return_value=2),
        patch('src.auth._warsaw_now', return_value=fixed_now),
        patch('src.auth.get_config', return_value=cfg),
        patch('src.auth.update_config') as upd,
    ):
        new_pin = get_or_rotate_pin()

    assert new_pin == '222222'
    upd.assert_called()


def test_pin_does_not_rotate_when_next_rotate_at_in_future():
    from src.auth import get_or_rotate_pin

    fixed_now = datetime(2026, 1, 24, 12, 0, 0)
    cfg = {
        'view_pin': '111111',
        'pin_auto_rotate': True,
        'pin_rotate_hours': 24,
        'pin_last_rotate': fixed_now - timedelta(hours=1),
        'pin_next_rotate_at': (fixed_now + timedelta(hours=1)).isoformat(),
    }

    with (
        patch('src.auth._warsaw_now', return_value=fixed_now),
        patch('src.auth.get_config', return_value=cfg),
        patch('src.auth.update_config') as upd,
    ):
        pin = get_or_rotate_pin()

    assert pin == '111111'
    upd.assert_not_called()


def test_pin_rotates_by_legacy_last_rotate_when_no_next_rotate_at():
    from src.auth import get_or_rotate_pin

    fixed_now = datetime(2026, 1, 24, 12, 0, 0)
    cfg = {
        'view_pin': '111111',
        'pin_auto_rotate': True,
        'pin_rotate_hours': 24,
        'pin_last_rotate': (fixed_now - timedelta(hours=25)).isoformat(),
        'pin_next_rotate_at': None,
    }

    with (
        patch('src.auth.secrets.randbelow', return_value=3),
        patch('src.auth._warsaw_now', return_value=fixed_now),
        patch('src.auth.get_config', return_value=cfg),
        patch('src.auth.update_config') as upd,
    ):
        pin = get_or_rotate_pin()

    assert pin == '333333'
    upd.assert_called()

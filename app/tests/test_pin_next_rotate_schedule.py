from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault(
    'GOOGLE_APPLICATION_CREDENTIALS',
    os.path.join(os.path.dirname(__file__), '..', '..', 'credentials', 'service-account.json'),
)

from src import create_app


class TestPinRotateSchedule(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True

    def test_pin_rotates_when_next_rotate_at_due_and_auto_rotate_enabled(self):
        from src.auth import rotate_pin_if_due

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
            rotate_pin_if_due()

        upd.assert_called_once()
        call_kw = upd.call_args[1]
        assert call_kw['view_pin'] == '222222'

    def test_pin_does_not_rotate_when_next_rotate_at_in_future(self):
        from src.auth import rotate_pin_if_due

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
            rotate_pin_if_due()

        upd.assert_not_called()

    def test_pin_rotates_by_legacy_last_rotate_when_no_next_rotate_at(self):
        from src.auth import rotate_pin_if_due

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
            rotate_pin_if_due()

        upd.assert_called_once()
        call_kw = upd.call_args[1]
        assert call_kw['view_pin'] == '333333'

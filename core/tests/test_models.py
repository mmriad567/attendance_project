from accounts.tests.base import BaseTestCase
from core.models import SystemSetting


class SystemSettingTests(BaseTestCase):
    def test_get_returns_default_when_missing(self):
        self.assertEqual(SystemSetting.get("missing", "fallback"), "fallback")

    def test_set_creates_then_updates(self):
        SystemSetting.set("attendance_threshold", "60", "min %")
        self.assertEqual(SystemSetting.get("attendance_threshold"), "60")

        SystemSetting.set("attendance_threshold", "75")
        self.assertEqual(SystemSetting.get("attendance_threshold"), "75")
        self.assertEqual(SystemSetting.objects.filter(key="attendance_threshold").count(), 1)

    def test_str_is_key(self):
        setting = SystemSetting.set("institute_name", "Demo Poly")
        self.assertEqual(str(setting), "institute_name")

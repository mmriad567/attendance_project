from django.test import TestCase, override_settings

# MD5 is far faster than PBKDF2 and is only used inside tests.
FAST_PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=FAST_PASSWORD_HASHERS)
class BaseTestCase(TestCase):
    """Shared test case that keeps password hashing cheap."""

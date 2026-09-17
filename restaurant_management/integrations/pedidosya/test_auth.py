import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import jwt

from restaurant_management.integrations.pedidosya.auth import authenticate_inbound


class TestPedidosYaAuthentication(unittest.TestCase):
    def setUp(self):
        self.secret = "a-test-secret-that-is-not-used-outside-this-test-and-is-long-enough-for-hs512"
        self.settings = SimpleNamespace(
            jwt_algorithm="HS512",
            jwt_leeway_seconds=0,
            jwt_audience=None,
            jwt_issuer=None,
            get_password=lambda field: self.secret,
        )

    def test_valid_bearer_jwt(self):
        token = jwt.encode(
            {"sub": "middleware", "service": "middleware", "exp": int(time.time()) + 60},
            self.secret,
            algorithm="HS512",
        )
        claims = authenticate_inbound(self.settings, f"Bearer {token}")
        self.assertEqual(claims["sub"], "middleware")

    @patch("restaurant_management.integrations.pedidosya.auth._", side_effect=lambda value: value)
    @patch("frappe.throw", side_effect=ValueError("blocked"))
    def test_expired_jwt_is_rejected(self, throw, translate):
        token = jwt.encode(
            {"service": "middleware", "exp": int(time.time()) - 60},
            self.secret,
            algorithm="HS512",
        )
        with self.assertRaisesRegex(ValueError, "blocked"):
            authenticate_inbound(self.settings, f"Bearer {token}")

    @patch("restaurant_management.integrations.pedidosya.auth._", side_effect=lambda value: value)
    @patch("frappe.throw", side_effect=ValueError("blocked"))
    def test_wrong_service_claim_is_rejected(self, throw, translate):
        token = jwt.encode({"service": "other"}, self.secret, algorithm="HS512")
        with self.assertRaisesRegex(ValueError, "blocked"):
            authenticate_inbound(self.settings, f"Bearer {token}")


if __name__ == "__main__":
    unittest.main()

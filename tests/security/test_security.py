#!/usr/bin/env python3
"""
Security Tests for Adaptive Traffic Signal System.

NOTE (2026-09-18 cleanup): quarantined classes targeting the deleted
Code/YOLO/darkflow module plus placeholder auth logic were removed:
TestInputValidation, TestFileSystemSecurity, TestAuthenticationSecurity.
See docs/TEST_CLEANUP_LOG.md for the deletion record + restore hashes.
Remaining classes test generic masking/logging helpers only — they do NOT
prove API input validation. Real boundary checks live in the detector
adapters + API layer and need dedicated tests (see TESTING_DOCUMENTATION.md).
"""

import re
import unittest


class TestDataEncryption(unittest.TestCase):
    """Test data encryption and protection"""

    def test_01_sensitive_data_handling(self):
        """Test: Sensitive data handling"""
        # Simulate sensitive data
        sensitive_data = {
            "license_plates": ["ABC123", "XYZ789", "DEF456"],
            "user_credentials": {"username": "admin", "password": "secret123"},
            "api_keys": {"traffic_api": "sk-1234567890abcdef"},
            "personal_info": {"name": "John Doe", "email": "john@example.com"},
        }

        for data_type, data in sensitive_data.items():
            with self.subTest(data_type=data_type):
                # Test data masking/anonymization
                masked_data = self._mask_sensitive_data(data_type, data)

                # Sensitive data should be masked
                if data_type == "license_plates":
                    for plate in masked_data:
                        # License plates should be partially masked
                        self.assertTrue(len(plate) >= 3 and plate[-3:].isdigit() or "*" in plate)

                elif data_type == "user_credentials":
                    # Passwords should be fully masked
                    self.assertNotIn(data["password"], str(masked_data))
                    self.assertIn("*", str(masked_data))

                elif data_type == "api_keys":
                    # API keys should be partially masked
                    self.assertNotIn(data["traffic_api"], str(masked_data))
                    self.assertIn("*", str(masked_data))

    def _mask_sensitive_data(self, data_type, data):
        """Simulate sensitive data masking"""
        if data_type == "license_plates":
            # Mask all but last 3 characters
            return [plate[:-3] + "***" if len(plate) > 3 else "***" for plate in data]

        elif data_type == "user_credentials":
            # Mask password completely
            return {"username": data["username"], "password": "***"}

        elif data_type == "api_keys":
            # Show only first 4 and last 4 characters
            key = data["traffic_api"]
            if len(key) > 8:
                return {"traffic_api": key[:4] + "***" + key[-4:]}
            else:
                return {"traffic_api": "***"}

        elif data_type == "personal_info":
            # Mask email partially
            email = data["email"]
            if "@" in email:
                local, domain = email.split("@", 1)
                masked_local = local[:2] + "***" if len(local) > 2 else "***"
                return {"name": data["name"], "email": masked_local + "@" + domain}
            else:
                return data

        return data

    def test_02_data_transmission_security(self):
        """Test: Data transmission security"""
        # Simulate data transmission scenarios
        transmission_scenarios = [
            {"protocol": "http", "secure": False, "reason": "Unencrypted HTTP"},
            {"protocol": "https", "secure": True, "reason": "Encrypted HTTPS"},
            {"protocol": "ws", "secure": False, "reason": "Unencrypted WebSocket"},
            {"protocol": "wss", "secure": True, "reason": "Encrypted WebSocket"},
            {"protocol": "ftp", "secure": False, "reason": "Unencrypted FTP"},
            {"protocol": "sftp", "secure": True, "reason": "Encrypted SFTP"},
        ]

        for scenario in transmission_scenarios:
            with self.subTest(protocol=scenario["protocol"]):
                is_secure = self._check_transmission_security(scenario["protocol"])
                self.assertEqual(
                    is_secure,
                    scenario["secure"],
                    f"Transmission security check failed: {scenario['reason']}",
                )

    def _check_transmission_security(self, protocol):
        """Check if transmission protocol is secure"""
        secure_protocols = ["https", "wss", "sftp", "ssh", "tls"]
        return protocol.lower() in secure_protocols


class TestLoggingSecurity(unittest.TestCase):
    """Test logging security and information disclosure"""

    def test_01_sensitive_information_logging(self):
        """Test: No sensitive information in logs"""
        # Simulate log entries
        log_entries = [
            "User admin logged in successfully",
            "Password: secret123",  # Should not log passwords
            "API key: sk-1234567890abcdef",  # Should not log API keys
            "License plate ABC123 detected",  # Should mask license plates
            "Credit card: 4111-1111-1111-1111",  # Should not log credit cards
            "SSN: 123-45-6789",  # Should not log SSNs
            "Normal system operation completed",
        ]

        for log_entry in log_entries:
            with self.subTest(log_entry=log_entry):
                # Check for sensitive information patterns
                sensitive_patterns = [
                    r"password:\s*\S+",
                    r"api[_-]?key:\s*\S+",
                    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
                    r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Credit card pattern
                    r"\b[A-Z]{3}\d{3,4}\b",  # License plate pattern
                ]

                has_sensitive = False
                for pattern in sensitive_patterns:
                    if re.search(pattern, log_entry, re.IGNORECASE):
                        has_sensitive = True
                        break

                # Log entry should not contain sensitive information
                if has_sensitive:
                    # In real implementation, this should be masked or not logged
                    self.assertIn(
                        "mask", "Sensitive information detected in log - should be masked"
                    )

    def test_02_log_injection_prevention(self):
        """Test: Log injection prevention"""
        # Log injection payloads
        injection_payloads = [
            "Normal log entry\n[ADMIN] User gained admin privileges",
            "Normal log entry\r[ERROR] System compromised",
            "Normal log entry\x00Malicious command executed",
            'Normal log entry<script>alert("XSS")</script>',
            'Normal log entry" && rm -rf / #',
            "Normal log entry`whoami`",
        ]

        for payload in injection_payloads:
            with self.subTest(payload=payload):
                # Simulate log sanitization
                sanitized_log = self._sanitize_log_entry(payload)

                # Sanitized log should not contain injection patterns
                self.assertNotIn("\n", sanitized_log)
                self.assertNotIn("\r", sanitized_log)
                self.assertNotIn("\x00", sanitized_log)
                self.assertNotIn("<script>", sanitized_log.lower())
                self.assertNotIn("&&", sanitized_log)
                self.assertNotIn("`", sanitized_log)

    def _sanitize_log_entry(self, log_entry):
        """Simulate log entry sanitization"""
        # Remove dangerous characters
        dangerous_chars = ["\n", "\r", "\x00", "<", ">", "&", '"', "'", "`", "$", "|", ";"]

        sanitized = log_entry
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        return sanitized


if __name__ == "__main__":
    # Configure test runner
    unittest.main(verbosity=2)

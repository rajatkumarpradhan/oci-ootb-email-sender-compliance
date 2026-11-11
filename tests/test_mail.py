import unittest

from oci_ootb_email_sender_compliance.mail import check_compliance


def sender(email, approved=True, spf=True, dkim=True):
    return {"email": email, "approved": approved, "spf": spf, "dkim": dkim}


def ids(findings):
    return {f.rule_id for f in findings}


class TestCompliance(unittest.TestCase):
    def test_compliant_set_has_no_findings(self):
        doc = {"senders": [sender("a@x.example")],
               "wiring": {"suppression_event_rule": True, "bounce_alarm": True}}
        self.assertEqual(check_compliance(doc), [])

    def test_mail001_missing_spf(self):
        findings = check_compliance({"senders": [sender("a@x.example", spf=False)]})
        mail001 = [f for f in findings if f.rule_id == "MAIL001"]
        self.assertEqual(len(mail001), 1)
        self.assertEqual(mail001[0].severity, "HIGH")

    def test_mail002_missing_dkim(self):
        self.assertIn("MAIL002", ids(check_compliance({"senders": [sender("a@x.example", dkim=False)]})))

    def test_unapproved_sender_skipped(self):
        findings = check_compliance({"senders": [sender("a@x.example", approved=False, spf=False, dkim=False)]})
        self.assertEqual(findings, [])

    def test_unapproved_senders_do_not_require_wiring(self):
        findings = check_compliance({"senders": [sender("a@x.example", approved=False, spf=False)]})
        self.assertNotIn("MAIL003", ids(findings))
        self.assertNotIn("MAIL004", ids(findings))

    def test_mail003_no_suppression_rule(self):
        findings = check_compliance({"senders": [sender("a@x.example")]})
        self.assertIn("MAIL003", ids(findings))

    def test_mail004_no_bounce_alarm(self):
        findings = check_compliance({"senders": [sender("a@x.example")],
                                     "wiring": {"suppression_event_rule": True}})
        self.assertIn("MAIL004", ids(findings))

    def test_mail005_duplicate_sender(self):
        findings = check_compliance({"senders": [sender("a@x.example"), sender("a@x.example")]})
        self.assertIn("MAIL005", ids(findings))

    def test_findings_sorted_high_first(self):
        doc = {"senders": [sender("a@x.example", spf=False, dkim=False),
                           sender("b@x.example", spf=False, dkim=False)]}
        findings = check_compliance(doc)
        self.assertEqual(findings[0].severity, "HIGH")

    def test_missing_senders_list_rejected(self):
        with self.assertRaises(ValueError):
            check_compliance({"items": []})

    def test_sender_missing_email_rejected(self):
        with self.assertRaises(ValueError):
            check_compliance({"senders": [{"spf": True}]})

    def test_invalid_email_rejected(self):
        with self.assertRaises(ValueError):
            check_compliance({"senders": [{"email": "not-an-email"}]})


if __name__ == "__main__":
    unittest.main()

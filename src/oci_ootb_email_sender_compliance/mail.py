"""Compliance checks for OCI Email Delivery sender configurations.

OCI Email Delivery is the built-in OCI email service; deliverability depends
on SPF and DKIM being set up per domain, and sender reputation depends on
watching the suppression list and bounce rates. This module reads a static
JSON description of approved senders and the surrounding wiring (event rule,
bounce alarm) and flags gaps. All analysis is offline; no OCI calls.
"""

from dataclasses import dataclass

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    subject: str
    message: str


def _senders(document):
    senders = document.get("senders")
    if not isinstance(senders, list):
        raise ValueError("document must contain a top-level 'senders' list")
    for sender in senders:
        if not isinstance(sender, dict):
            raise ValueError("each sender entry must be an object")
        if not sender.get("email"):
            raise ValueError(f"sender entry missing 'email': {sender}")
        if "@" not in sender["email"]:
            raise ValueError(f"sender email looks invalid: {sender['email']!r}")
    return senders


def check_compliance(document):
    senders = _senders(document)
    findings = []
    seen = set()

    for sender in senders:
        email = sender["email"]
        if email in seen:
            findings.append(Finding("MAIL005", "LOW", email, "duplicate sender entry"))
        seen.add(email)
        if not sender.get("approved", True):
            continue  # not yet approved; nothing to deliverability-check
        if not sender.get("spf"):
            findings.append(Finding("MAIL001", "HIGH", email,
                                    "approved sender without SPF; recipient servers will junk or reject its mail"))
        if not sender.get("dkim"):
            findings.append(Finding("MAIL002", "MEDIUM", email,
                                    "approved sender without DKIM signing; spoofing and spam-folder risk"))

    approved = [s for s in senders if s.get("approved", True)]
    if approved:
        wiring = document.get("wiring") or {}
        if not wiring.get("suppression_event_rule"):
            findings.append(Finding("MAIL003", "MEDIUM", "suppression-list",
                                    "no event rule watching the suppression list; bounced addresses pile up silently and hurt reputation"))
        if not wiring.get("bounce_alarm"):
            findings.append(Finding("MAIL004", "LOW", "bounce-rate",
                                    "no monitoring alarm on bounce rate; a deliverability drop would go unnoticed"))

    return sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.rule_id, f.subject, f.message))

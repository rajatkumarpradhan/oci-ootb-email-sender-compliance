# oci-ootb-email-sender-compliance

**Built-in services project (OOTB): OCI Email Delivery + OCI Events + OCI Notifications + OCI Monitoring**, with a custom offline checker on top. Deliverability for OCI Email Delivery depends on SPF and DKIM per approved sender, and sender reputation depends on watching the suppression list and bounce rate. This repo ships the Terraform template for that wiring plus a checker that verifies a sender inventory actually meets it.

## What is custom code vs native service configuration

- **Native (OCI built-in features):** the email domain, DKIM, approved sender, suppression-list event rule, and bounce-rate monitoring alarm in `infra/main.tf`. That is configuration of OCI's own services, via Terraform.
- **Custom:** the Python checker in `src/` that reads a static JSON sender inventory and flags missing SPF/DKIM, unwatched suppression lists, and missing bounce alarms.
- **What ran:** the checker and its 16 unit tests executed locally and in CI (Python 3.10/3.11/3.12), plus the seeded demo below.
- **What is template-only:** the Terraform in `infra/` has NOT been plan/apply validated against a tenancy. It is a structural template only; validate against the current OCI provider docs before any real apply. Nothing here talks to a live tenancy.

## What it is NOT (more honest limits)

- The checker works on a static JSON inventory. It does not call the OCI API to enumerate senders, and it does not verify DNS records actually published - `spf`/`dkim` flags are assertions in the input, not looked-up facts.
- SPF/DKIM syntax validation, alignment (DMARC), and content reputation are out of scope.

## Rules

| Rule | Severity | Finding |
| --- | --- | --- |
| MAIL001 | HIGH | Approved sender without SPF; recipients will junk or reject its mail |
| MAIL002 | MEDIUM | Approved sender without DKIM signing |
| MAIL003 | MEDIUM | No event rule watching the suppression list |
| MAIL004 | LOW | No monitoring alarm on bounce rate |
| MAIL005 | LOW | Duplicate sender entry |

Exit code 2 when any MAIL001 fires; 1 on unreadable or malformed input; 0 otherwise. Unapproved (pending) senders are skipped - there is nothing to deliverability-check yet.

## Run the local checker

Requires Python 3.10+, no third-party dependencies.

```sh
PYTHONPATH=src python3 -m oci_ootb_email_sender_compliance samples/noncompliant-senders.json
PYTHONPATH=src python3 -m oci_ootb_email_sender_compliance samples/compliant-senders.json
```

Or the end-to-end demo:

```sh
sh demo.sh
```

Expected demo output: the noncompliant set flags the SPF-less approved sender (HIGH), two DKIM gaps, the unwatched suppression list, the missing bounce alarm and a duplicate entry, and exits 2; the compliant set reports zero findings and exits 0.

## Terraform wiring (template)

```sh
cd infra
cp terraform.tfvars.example terraform.tfvars   # fill in the OCIDs and domain
terraform init && terraform plan
```

This is a template - do NOT apply without reviewing against the current OCI provider docs. It was not validated against a live tenancy.

## Test

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

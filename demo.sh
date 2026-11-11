#!/bin/sh
# Checks the noncompliant sender set (missing SPF -> exit 2), then the compliant set.
set -u
export PYTHONPATH="$(dirname "$0")/src"

echo "=== Checking samples/noncompliant-senders.json ==="
python3 -m oci_ootb_email_sender_compliance samples/noncompliant-senders.json
echo "exit code: $? (2 = approved sender without SPF, expected for the noncompliant set)"
echo
echo "=== Checking samples/compliant-senders.json ==="
python3 -m oci_ootb_email_sender_compliance samples/compliant-senders.json
echo "exit code: $? (0 = compliant, expected)"

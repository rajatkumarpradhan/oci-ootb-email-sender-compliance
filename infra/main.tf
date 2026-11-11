# OCI Email Delivery sender wiring (template; NOT applied).
#
# OCI Email Delivery is the built-in OCI email service; deliverability needs
# SPF and DKIM per domain, and sender reputation needs the suppression list
# and bounce rate watched. This template creates the email domain and
# approved sender, wires a suppression-list event to an ONS topic, and adds a
# bounce-rate alarm. The local checker in src/ verifies a sender inventory
# against this posture.
#
# This file has NOT been plan/apply validated against a tenancy - it is a
# structural template. Review against the current provider docs before any
# real apply.

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

variable "compartment_ocid" {
  type        = string
  description = "OCID of the compartment that owns the email resources"
}

variable "sender_domain" {
  type        = string
  description = "Domain to send from, e.g. shop.example"
}

variable "notification_topic_ocid" {
  type        = string
  description = "OCID of the ONS topic for suppression and alarm notifications"
}

resource "oci_email_email_domain" "sender" {
  compartment_id = var.compartment_ocid
  name           = var.sender_domain
}

resource "oci_email_dkim" "sender" {
  email_domain_id = oci_email_email_domain.sender.id
  description     = "DKIM signing for ${var.sender_domain}"
}

resource "oci_email_sender" "alerts" {
  compartment_id = var.compartment_ocid
  email_address  = "alerts@${var.sender_domain}"
}

# Notify when Email Delivery adds an address to the suppression list.
resource "oci_events_rule" "suppression_watch" {
  compartment_id = var.compartment_ocid
  display_name   = "email-suppression-watch"
  is_enabled     = true
  condition      = "{\"eventType\": [\"com.oraclecloud.emaildelivery.createsuppression\"]}"

  actions {
    action_type = "ONS"
    topic_id    = var.notification_topic_ocid
  }
}

# Page when the bounce rate crosses 5% over five minutes.
resource "oci_monitoring_alarm" "bounce_rate" {
  compartment_id        = var.compartment_ocid
  display_name          = "email-bounce-rate"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_emaildelivery"
  query                 = "BounceRate[5m].mean() > 5"
  severity              = "CRITICAL"
  destinations          = [var.notification_topic_ocid]
}

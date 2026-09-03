"""Daraja (M-Pesa) configuration, read from environment variables only.

Set these on Render's dashboard (Settings -> Environment), never in code:
  MPESA_ENV               "sandbox" (default) or "production"
  MPESA_CONSUMER_KEY      from your Daraja app
  MPESA_CONSUMER_SECRET   from your Daraja app
  MPESA_SHORTCODE         test shortcode (sandbox) or your paybill (production)
  MPESA_PASSKEY           sandbox passkey (shared/public for sandbox) or your production passkey
  MPESA_CALLBACK_URL      e.g. https://global-rails.onrender.com/api/mpesa/callback

If any of these are unset, initiate_stk_push() returns a clear
MPESA_NOT_CONFIGURED error rather than failing confusingly deeper in the
request - see mpesa_daraja._configured().
"""
import os

ENV = os.environ.get("MPESA_ENV", "sandbox")
BASE_URL = "https://sandbox.safaricom.co.ke" if ENV == "sandbox" else "https://api.safaricom.co.ke"

CONSUMER_KEY = os.environ.get("MPESA_CONSUMER_KEY", "")
CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET", "")
SHORTCODE = os.environ.get("MPESA_SHORTCODE", "")
PASSKEY = os.environ.get("MPESA_PASSKEY", "")
CALLBACK_URL = os.environ.get("MPESA_CALLBACK_URL", "")

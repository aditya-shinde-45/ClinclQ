"""
AWS Time Synchronization & Clock Skew Calibrator

Automatically detects and corrects clock skew between the local host system
and AWS infrastructure (Amazon S3 and Amazon Bedrock).

When local clock skew exceeds 2 seconds (common when local timezone offsets,
hardware clocks, or hypervisor clocks drift), AWS Signature Version 4 (SigV4)
rejects requests with 'RequestTimeTooSkewed' or 'InvalidSignatureException: Signature expired'.

This module queries an authoritative AWS HTTP endpoint, measures the exact time delta,
and patches botocore's internal datetime provider so all AWS boto3 calls sign requests
with the correct server timestamp.
"""

import email.utils
import logging
import urllib.request
import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_skew_delta: Optional[datetime.timedelta] = None
_sync_attempted: bool = False


def sync_aws_clock_skew(target_endpoint: str = "https://aws.amazon.com", timeout: float = 4.0) -> Optional[datetime.timedelta]:
    """
    Measures clock skew against an authoritative AWS endpoint and applies
    in-memory calibration to botocore if skew exceeds 2 seconds.
    """
    global _skew_delta, _sync_attempted

    try:
        req = urllib.request.Request(
            target_endpoint,
            headers={"User-Agent": "ClinIQ-Clock-Sync/1.0"},
            method="HEAD"
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            server_date_header = response.headers.get("Date")

        if not server_date_header:
            logger.debug("No Date header received from AWS sync endpoint.")
            _sync_attempted = True
            return None

        server_utc_dt = email.utils.parsedate_to_datetime(server_date_header)
        local_utc_dt = datetime.datetime.now(datetime.timezone.utc)
        skew = server_utc_dt - local_utc_dt
        _skew_delta = skew
        _sync_attempted = True

        skew_seconds = skew.total_seconds()
        if abs(skew_seconds) >= 2.0:
            logger.warning(
                f"[AWS Time Sync] Local system clock skew detected: {skew_seconds:+.1f}s ({skew_seconds/3600:+.2f}h). "
                "Applying botocore SigV4 runtime timestamp calibration."
            )
            _apply_botocore_patch(skew)
        else:
            logger.info(f"[AWS Time Sync] Local clock is accurate within {skew_seconds:+.2f}s of AWS. No calibration needed.")

        return _skew_delta

    except Exception as exc:
        logger.warning(f"[AWS Time Sync] Could not probe AWS server time ({exc}). Relying on standard system clock.")
        _sync_attempted = True
        return None


def _apply_botocore_patch(skew: datetime.timedelta) -> None:
    """Patches botocore datetime providers to incorporate the measured clock skew delta."""
    try:
        import botocore.auth
        import botocore.utils

        orig_auth_dt = getattr(botocore.auth, "_orig_get_current_datetime", botocore.auth.get_current_datetime)
        orig_utils_dt = getattr(botocore.utils, "_orig_get_current_datetime", botocore.utils.get_current_datetime)

        botocore.auth._orig_get_current_datetime = orig_auth_dt
        botocore.utils._orig_get_current_datetime = orig_utils_dt

        def _calibrated_auth_dt(remove_tzinfo: bool = True):
            dt = orig_auth_dt(False) + skew
            return dt.replace(tzinfo=None if remove_tzinfo else datetime.timezone.utc)

        def _calibrated_utils_dt(remove_tzinfo: bool = True):
            dt = orig_utils_dt(False) + skew
            return dt.replace(tzinfo=None if remove_tzinfo else datetime.timezone.utc)

        botocore.auth.get_current_datetime = _calibrated_auth_dt
        botocore.utils.get_current_datetime = _calibrated_utils_dt
        logger.info("[AWS Time Sync] Successfully calibrated botocore.auth and botocore.utils datetime providers.")
    except Exception as e:
        logger.error(f"[AWS Time Sync] Failed to patch botocore datetime providers: {e}")


# Run initial sync upon module load
sync_aws_clock_skew()

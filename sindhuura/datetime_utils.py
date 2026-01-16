from datetime import datetime
import pytz

IST_TZ = pytz.timezone("Asia/Kolkata")


def to_ist(dt, fmt="%d %b %Y, %I:%M %p"):
    """
    Convert datetime to IST and format it.

    :param dt: datetime object (aware or naive)
    :param fmt: output format string
    :return: formatted IST datetime string
    """

    if not dt:
        return None

    # If naive datetime, assume UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    ist_dt = dt.astimezone(IST_TZ)
    return ist_dt.strftime(fmt)

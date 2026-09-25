import re
from datetime import datetime
from typing import Optional


class ParseError(ValueError):
    """Raised when an EXIF date-time string cannot be parsed.

    Subclass of ValueError so callers can catch either the specific error
    or the broad category.
    """
    pass


class ExifTimeParser:
    """Parses and normalizes EXIF date-time strings from image metadata.

    EXIF stores the image capture timestamp in two common tags:
    - DateTimeOriginal (tag 0x9003)
    - DateTime (tag 0x0132)

    Both use the format "YYYY:MM:DD HH:MM:SS" (colon between date parts).
    Some cameras also store sub-second precision in SubSecTimeOriginal
    (tag 0x9292) as a string of up to 6 digits representing a fractional
    second. When present, the parser merges it into the result.

    Design decisions:
    - We intentionally do NOT attempt timezone offset parsing. EXIF 2.3
      does not carry a timezone; the OffsetTimeOriginal tag (0x9011) is
      optional and rarely populated. Calling code is responsible for any
      timezone interpretation.
    - We return naive datetime objects because the source carries no
      timezone. Treating them as UTC would be a silent, incorrect assumption.
    - If sub-seconds are fewer than 6 digits we right-pad with zeros.
      If more than 6, we truncate. This matches the EXIF spec's loose
      definition: "the number of digits after the decimal point is one or more".
    - We accept either a space or 'T' as the separator between date and time,
      because some tools emit 'T'. We do NOT accept other separators.
    """

    # EXIF canonical: 2013:04:24 12:34:56
    _FULL_RE = re.compile(
        r"^(\d{4}):(\d{2}):(\d{2})[ T](\d{2}):(\d{2}):(\d{2})$"
    )
    # Date-only appears in some malformed files; we parse it and set time to midnight.
    _DATE_ONLY_RE = re.compile(r"^(\d{4}):(\d{2}):(\d{2})$")

    @classmethod
    def parse(cls, value: str, sub_seconds: Optional[str] = None) -> datetime:
        """Parse an EXIF date-time string into a naive datetime.

        Args:
            value: The raw EXIF date-time string, e.g. "2013:04:24 12:34:56".
            sub_seconds: Optional sub-second string from SubSecTime* tags.
                May be None, empty, or 1-6+ digits. Padded/truncated to 6.

        Returns:
            A naive datetime with microsecond precision if sub_seconds
            was provided and non-empty, otherwise microsecond=0.

        Raises:
            ParseError: If the string doesn't match a known EXIF format or
                the resulting date is invalid (e.g. month 13).
        """
        if not isinstance(value, str):
            raise ParseError(f"Expected str, got {type(value).__name__}")

        value = value.strip()
        if not value:
            raise ParseError("Empty date-time string")

        m = cls._FULL_RE.match(value)
        date_only = False
        if m is None:
            m = cls._DATE_ONLY_RE.match(value)
            if m is None:
                raise ParseError(f"Unrecognized EXIF date-time format: {value!r}")
            date_only = True

        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if date_only:
            h = mi = s = 0
        else:
            h, mi, s = int(m.group(4)), int(m.group(5)), int(m.group(6))

        micros = cls._parse_sub_seconds(sub_seconds)

        try:
            return datetime(y, mo, d, h, mi, s, micros)
        except ValueError as e:
            raise ParseError(str(e)) from e

    @staticmethod
    def _parse_sub_seconds(sub_seconds: Optional[str]) -> int:
        """Normalize a SubSecTime value into microseconds (0-999999).

        EXIF SubSecTime is a free-form string of digits representing a
        fractional second. "12" means 0.12 seconds = 120000 microseconds.
        We right-pad to 6 digits and truncate excess. Non-digit characters
        raise ParseError so callers don't silently get garbage precision.
        """
        if sub_seconds is None:
            return 0
        if not isinstance(sub_seconds, str):
            raise ParseError(
                f"sub_seconds must be str or None, got {type(sub_seconds).__name__}"
            )
        s = sub_seconds.strip()
        if not s:
            return 0
        if not s.isdigit():
            raise ParseError(f"Invalid sub-second value: {sub_seconds!r}")
        # Pad to 6 digits (microseconds), truncate beyond 6.
        padded = (s + "000000")[:6]
        return int(padded)

    @classmethod
    def normalize(cls, value: str, sub_seconds: Optional[str] = None) -> str:
        """Parse then re-emit in ISO 8601 form.

        Output: "YYYY-MM-DDTHH:MM:SS.ffffff" when sub-seconds present,
        otherwise "YYYY-MM-DDTHH:MM:SS".

        We use 'T' as the separator (ISO 8601 basic) rather than a space,
        because a space in ISO 8601 is ambiguous and some parsers reject it.
        """
        dt = cls.parse(value, sub_seconds)
        iso = dt.isoformat()
        # datetime.isoformat() emits microseconds only when nonzero; align with that.
        return iso

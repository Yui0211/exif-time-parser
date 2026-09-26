# Exif Time Parser

Parses EXIF date-time strings (the `YYYY:MM:DD HH:MM:SS` format found in image metadata) into Python `datetime` objects, with optional sub-second merging.

```python
from datetime import datetime
from exif_time_parser import ExifTimeParser, ParseError

dt = ExifTimeParser.parse("2013:04:24 12:34:56")
print(dt)  # 2013-04-24 12:34:56

with_sub = ExifTimeParser.parse("2013:04:24 12:34:56", sub_seconds="12")
print(with_sub)  # 2013-04-24 12:34:56.120000

iso = ExifTimeParser.normalize("2013:04:24 12:34:56")
print(iso)  # 2013-04-24T12:34:56
```

## Why

EXIF date strings use colons as date separators and don't carry timezone information. This library does the one job of turning those strings into `datetime` objects and merging the separately-stored `SubSecTimeOriginal` fractional-second field when present.

The trade-off: we return **naive** datetimes and do not guess a timezone. EXIF 2.3 has no reliable timezone field. If your pipeline needs UTC or local time, apply the offset yourself after parsing.

## Edge cases

- Sub-second strings shorter than 6 digits are right-padded (`"12"` becomes `120000` microseconds). Strings longer than 6 digits are truncated, not rounded.
- A date-only string (`"2013:04:24"`) parses to midnight. Some cameras emit this when the time tag is missing.
- The parser accepts a space or `T` between date and time. Other separators are rejected.

"""Separate editorial housekeeping from substantive user-facing text."""
import re

SERVICE = re.compile(r'^\s*(?:Часть\s*\d+|Ч\d+)\s*:\s*незакрытые поля\s*:',re.I)


def split_service(value):
    if not isinstance(value,str):return value,[]
    parts=re.split(r'\s*\|\s*',value)
    notes=[p.strip() for p in parts if SERVICE.search(p)]
    return ' | '.join(p.strip() for p in parts if not SERVICE.search(p)).strip(),notes

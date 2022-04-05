import re
from typing import Literal

from load import TranscriptionTables


def parse_text(text: str, tables: TranscriptionTables, _type: str):
    _type = _type.lower()
    
    if _type not in tables.available:
        raise ValueError('The given translation type is not available in the current transcription tables')
    table = tables.tables[_type]

    for regex, replacement in table:
        text = re.sub(regex, replacement, text)
    
    return text

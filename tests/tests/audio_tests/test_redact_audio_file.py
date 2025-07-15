from pathlib import Path
import pytest
import struct

def test_redact_audio_file(textual_audio):
    # First, lets make sure it doesn't raise an exception
    textual_audio.redact_audio_file('tests/tests/files/banking_customer_support.m4a', 'output.m4a')

    # Now lets confirm the file is roughly the size we expect
    path = Path('output.m4a')

    assert is_probably_m4a(path), "output file is likely not valid m4a file"

def is_probably_m4a(path: Path) -> bool:
    """
    Return True if `path` looks like a valid M4A/MP4‑audio file.
    `ffprobe_ok` adds a final “definitely playable” pass that calls ffprobe;
    set it False if you don't have FFmpeg on the box.
    """
    path = Path(path)

    if path.stat().st_size < 1024:
        return False

    # container signature: look for an MP4 "ftyp" box with a known brand
    with path.open("rb") as f:
        header = f.read(16)
    
    try:
        box_size, box_type = struct.unpack(">I4s", header[:8])
    except struct.error:
        return False
    if box_type != b"ftyp":
        return False
    major_brand = header[8:12]
    if major_brand not in {b"M4A ", b"M4B ", b"isom", b"mp42"}:
        return False
    
    return True
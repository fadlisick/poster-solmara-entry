#!/usr/bin/env python3
"""Solmara poster entrypoint (make.fun: The Poster for a Place That Isn't There).

Validates the rendered poster (entry.png, shipped beside this file) and copies
it to the output directory as /output/entry.png.

Stdlib only: the grader runs this in a python:3.13-slim sandbox with no
network and no Pillow, so the image itself is pre-rendered and only checked
and copied here.

Rules honoured:
- Output dir comes from MAKEFUN_OUTPUT_DIR (default /output).
- Never chmod the output directory itself (the grader runs as uid 65534 on a
  root-owned writable /output, so chmod there raises PermissionError).
- Only files this program creates are chmod-ed, to 0644.
"""
import os
import shutil
import struct
import sys

MAX_BYTES = 1_048_576
WANT_W = 1024
WANT_H = 1024

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")


def fail(msg):
    print("error: " + msg, file=sys.stderr)
    sys.exit(1)


def check_png(path):
    """Validate a PNG: magic, size, dimensions, IHDR sanity. Stdlib only."""
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        fail("cannot stat %s: %s" % (path, exc))
    if size > MAX_BYTES:
        fail("entry.png is %d bytes, over the 1,048,576 byte cap" % size)
    with open(path, "rb") as fh:
        head = fh.read(33)
    if len(head) < 33 or head[:8] != b"\x89PNG\r\n\x1a\n":
        fail("entry.png is not a PNG file")
    if head[12:16] != b"IHDR":
        fail("entry.png has no IHDR chunk")
    width, height = struct.unpack(">II", head[16:24])
    bit_depth = head[24]
    colour_type = head[25]
    if (width, height) != (WANT_W, WANT_H):
        fail("entry.png is %dx%d, expected 1024x1024" % (width, height))
    if bit_depth != 8 or colour_type not in (2, 6):
        fail("entry.png is bit depth %d colour type %d, expected 8-bit RGB(A)"
             % (bit_depth, colour_type))
    return size


def main():
    size = check_png(SRC)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    shutil.copyfile(SRC, dest)
    try:
        os.chmod(dest, 0o644)
    except OSError:
        pass
    # Re-check the copy we just wrote.
    if os.path.getsize(dest) != size:
        fail("copied entry.png differs in size from the source")
    print("wrote %s (%d bytes, 1024x1024 PNG)" % (dest, size))


if __name__ == "__main__":
    main()

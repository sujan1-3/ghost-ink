#!/usr/bin/env python3
"""
ghost-ink: Zero-Width Unicode Steganography Tool
Encodes any file's content into invisible Unicode characters.
Human eyes see nothing. AI reads everything.
"""

import os
import sys
import hashlib
import base64
import argparse
from pathlib import Path

# Zero-width Unicode characters for 2-bit encoding
ZW_CHARS = {
    0b00: "\u200b",  # ZERO WIDTH SPACE
    0b01: "\u200c",  # ZERO WIDTH NON-JOINER
    0b10: "\u200d",  # ZERO WIDTH JOINER
    0b11: "\u2060",  # WORD JOINER
}
ZW_DECODE = {v: k for k, v in ZW_CHARS.items()}

MAGIC_HEADER = "\u200b\u200c\u200d\u2060\u200d\u200c\u200b"
CARRIER_TEXT = "// This file has been processed."
GHOST_EXT = ".ghost"


def bytes_to_zw(data: bytes) -> str:
    result = []
    for byte in data:
        result.append(ZW_CHARS[(byte >> 6) & 0b11])
        result.append(ZW_CHARS[(byte >> 4) & 0b11])
        result.append(ZW_CHARS[(byte >> 2) & 0b11])
        result.append(ZW_CHARS[(byte >> 0) & 0b11])
    return "".join(result)


def zw_to_bytes(zw_str: str) -> bytes:
    chars = [c for c in zw_str if c in ZW_DECODE]
    if len(chars) % 4 != 0:
        raise ValueError(f"Invalid ZW sequence length: {len(chars)} (must be multiple of 4)")
    result = []
    for i in range(0, len(chars), 4):
        b = (
            (ZW_DECODE[chars[i]]   << 6) |
            (ZW_DECODE[chars[i+1]] << 4) |
            (ZW_DECODE[chars[i+2]] << 2) |
            (ZW_DECODE[chars[i+3]] << 0)
        )
        result.append(b)
    return bytes(result)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode_file(src: Path, dst: Path) -> bool:
    try:
        raw = src.read_bytes()
        original_hash = sha256(raw)
        b64 = base64.b64encode(raw)
        payload = f"{original_hash}:".encode() + b64
        zw = bytes_to_zw(payload)
        content = CARRIER_TEXT + MAGIC_HEADER + zw
        dst.write_text(content, encoding="utf-8")

        # Roundtrip verification
        verify_raw = decode_content(dst.read_text(encoding="utf-8"))
        if sha256(verify_raw) != original_hash:
            dst.unlink(missing_ok=True)
            print(f"  [FAIL] Hash mismatch after encode: {src.name}")
            return False

        print(f"  [OK]   {src.name} -> {dst.name} ({len(raw)} bytes, verified)")
        return True

    except Exception as e:
        print(f"  [ERR]  {src.name}: {e}")
        return False


def decode_content(text: str) -> bytes:
    if MAGIC_HEADER not in text:
        raise ValueError("No ghost-ink magic header found.")
    zw_data = text[text.index(MAGIC_HEADER) + len(MAGIC_HEADER):]
    payload = zw_to_bytes(zw_data)
    colon1 = payload.index(b":")
    stored_hash = payload[:colon1].decode()
    b64 = payload[colon1 + 1:]
    raw = base64.b64decode(b64)
    if sha256(raw) != stored_hash:
        raise ValueError("Hash mismatch during decode! File may be corrupted.")
    return raw


def decode_file(src: Path, out_dir: Path) -> bool:
    try:
        text = src.read_text(encoding="utf-8")
        if MAGIC_HEADER not in text:
            print(f"  [SKIP] {src.name}: not a ghost-ink file")
            return False

        raw = decode_content(text)

        # src.stem = "hello.py" (removes .ghost), use that directly as output filename
        out_path = out_dir / src.stem
        out_path.write_bytes(raw)
        print(f"  [OK]   {src.name} -> {out_path.name} ({len(raw)} bytes, hash verified)")
        return True

    except Exception as e:
        print(f"  [ERR]  {src.name}: {e}")
        return False


def process_folder_encode(folder: Path, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    files = [f for f in folder.rglob("*") if f.is_file() and f.suffix != GHOST_EXT]
    if not files:
        print("No files found to encode.")
        return
    ok = fail = 0
    for f in files:
        rel = f.relative_to(folder)
        dst = output / rel.parent / (rel.name + GHOST_EXT)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if encode_file(f, dst):
            ok += 1
        else:
            fail += 1
    print(f"\nDone: {ok} encoded, {fail} failed.")


def process_folder_decode(folder: Path, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    files = [f for f in folder.rglob("*") if f.is_file() and f.suffix == GHOST_EXT]
    if not files:
        print("No .ghost files found to decode.")
        return
    ok = fail = 0
    for f in files:
        rel = f.relative_to(folder)
        out_dir = output / rel.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        if decode_file(f, out_dir):
            ok += 1
        else:
            fail += 1
    print(f"\nDone: {ok} decoded, {fail} failed.")


def main():
    parser = argparse.ArgumentParser(
        description="ghost-ink: Hide code in plain sight using zero-width Unicode steganography."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encode", help="Encode all files in a folder")
    enc.add_argument("input", help="Source folder")
    enc.add_argument("output", help="Output folder for .ghost files")

    dec = sub.add_parser("decode", help="Decode all .ghost files in a folder")
    dec.add_argument("input", help="Folder containing .ghost files")
    dec.add_argument("output", help="Output folder for recovered files")

    args = parser.parse_args()
    src = Path(args.input).resolve()
    out = Path(args.output).resolve()

    if not src.exists():
        print(f"Error: input path does not exist: {src}")
        sys.exit(1)

    if args.command == "encode":
        print(f"Encoding: {src} -> {out}\n")
        process_folder_encode(src, out)
    elif args.command == "decode":
        print(f"Decoding: {src} -> {out}\n")
        process_folder_decode(src, out)


if __name__ == "__main__":
    main()

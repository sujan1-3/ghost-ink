#!/usr/bin/env python3
"""
ghost-ink v2.0
Zero-Width Unicode Steganography Tool

Supports EVERY file type — Python, JavaScript, Rust, C, C++, Go, Java,
TypeScript, Ruby, PHP, Swift, Kotlin, Shell, HTML, CSS, JSON, YAML,
XML, Markdown, binary, executables, images — literally everything.

Human eyes see nothing. AI reads everything.
"""

import os
import sys
import hashlib
import base64
import argparse
import time
from pathlib import Path

__version__ = "2.0.0"

# ─────────────────────────────────────────────
# Zero-width Unicode: 4 chars → 2-bit encoding
# ─────────────────────────────────────────────
ZW_CHARS = {
    0b00: "\u200b",  # ZERO WIDTH SPACE
    0b01: "\u200c",  # ZERO WIDTH NON-JOINER
    0b10: "\u200d",  # ZERO WIDTH JOINER
    0b11: "\u2060",  # WORD JOINER
}
ZW_DECODE   = {v: k for k, v in ZW_CHARS.items()}
ZW_SET      = set(ZW_CHARS.values())
MAGIC       = "\u200b\u200c\u200d\u2060\u200d\u200c\u200b"
CARRIER     = "// ghost-ink encoded file \u2014 do not edit"
GHOST_EXT   = ".ghost"
SKIP_EXTS   = {GHOST_EXT}

# ANSI colors
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}\u2713{RESET}  {msg}")
def err(msg):  print(f"  {RED}\u2717{RESET}  {msg}")
def skip(msg): print(f"  {YELLOW}\u2298{RESET}  {DIM}{msg}{RESET}")
def info(msg): print(f"  {CYAN}\u2192{RESET}  {msg}")


# ─────────────────────────────────────────────
# Core encode / decode
# ─────────────────────────────────────────────

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bytes_to_zw(data: bytes) -> str:
    out = []
    for byte in data:
        out.append(ZW_CHARS[(byte >> 6) & 0b11])
        out.append(ZW_CHARS[(byte >> 4) & 0b11])
        out.append(ZW_CHARS[(byte >> 2) & 0b11])
        out.append(ZW_CHARS[(byte >> 0) & 0b11])
    return "".join(out)


def zw_to_bytes(zw_str: str) -> bytes:
    chars = [c for c in zw_str if c in ZW_SET]
    if len(chars) % 4 != 0:
        raise ValueError(
            f"Corrupted ghost file: ZW sequence length {len(chars)} is not a multiple of 4."
        )
    out = []
    for i in range(0, len(chars), 4):
        b = (
            (ZW_DECODE[chars[i]]   << 6) |
            (ZW_DECODE[chars[i+1]] << 4) |
            (ZW_DECODE[chars[i+2]] << 2) |
            (ZW_DECODE[chars[i+3]] << 0)
        )
        out.append(b)
    return bytes(out)


def _build_payload(raw: bytes) -> str:
    h       = sha256(raw)
    b64     = base64.b64encode(raw)
    payload = f"{h}:".encode() + b64
    return CARRIER + MAGIC + bytes_to_zw(payload)


def _parse_payload(text: str) -> bytes:
    if MAGIC not in text:
        raise ValueError("Not a ghost-ink file (magic header missing).")
    zw_section = text[text.index(MAGIC) + len(MAGIC):]
    payload    = zw_to_bytes(zw_section)
    colon      = payload.index(b":")
    stored_h   = payload[:colon].decode()
    raw        = base64.b64decode(payload[colon + 1:])
    actual_h   = sha256(raw)
    if actual_h != stored_h:
        raise ValueError(
            f"SHA-256 mismatch!\n  stored : {stored_h}\n  actual : {actual_h}"
        )
    return raw


# ─────────────────────────────────────────────
# Single-file operations
# ─────────────────────────────────────────────

def encode_file(src: Path, dst: Path, verbose: bool = True) -> bool:
    """Encode one file into dst.ghost. Returns True on success."""
    try:
        if not src.is_file():
            if verbose: skip(f"{src.name}: not a regular file")
            return False
        if not os.access(src, os.R_OK):
            if verbose: err(f"{src.name}: permission denied")
            return False

        raw        = src.read_bytes()
        original_h = sha256(raw)
        content    = _build_payload(raw)

        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content, encoding="utf-8")

        # ── Roundtrip verification ──────────────────────────────────
        verify = _parse_payload(dst.read_text(encoding="utf-8"))
        if sha256(verify) != original_h:
            dst.unlink(missing_ok=True)
            if verbose: err(f"{src.name}: roundtrip hash mismatch \u2014 output deleted")
            return False
        # ────────────────────────────────────────────────────────────

        if verbose:
            size = _fmt_size(len(raw))
            ok(f"{src.name}  {DIM}\u2192  {dst.name}  ({size}){RESET}")
        return True

    except PermissionError:
        if verbose: err(f"{src.name}: permission denied")
        return False
    except Exception as e:
        if verbose: err(f"{src.name}: {e}")
        return False


def decode_file(src: Path, out_dir: Path, verbose: bool = True) -> bool:
    """Decode one .ghost file back to original. Returns True on success."""
    try:
        if not src.is_file():
            if verbose: skip(f"{src.name}: not a regular file")
            return False
        if not os.access(src, os.R_OK):
            if verbose: err(f"{src.name}: permission denied")
            return False

        text = src.read_text(encoding="utf-8")
        if MAGIC not in text:
            if verbose: skip(f"{src.name}: not a ghost-ink file \u2014 skipped")
            return False

        raw     = _parse_payload(text)
        out_dir.mkdir(parents=True, exist_ok=True)

        # src.stem of "hello.py.ghost" = "hello.py" (the correct original name)
        out_path = out_dir / src.stem
        out_path.write_bytes(raw)

        if verbose:
            size = _fmt_size(len(raw))
            ok(f"{src.name}  {DIM}\u2192  {out_path.name}  ({size}){RESET}")
        return True

    except PermissionError:
        if verbose: err(f"{src.name}: permission denied")
        return False
    except Exception as e:
        if verbose: err(f"{src.name}: {e}")
        return False


# ─────────────────────────────────────────────
# Folder operations
# ─────────────────────────────────────────────

def _collect_encode(folder: Path):
    """Yield all regular, readable files, excluding .ghost and symlinks."""
    for f in sorted(folder.rglob("*")):
        if f.is_symlink(): continue
        if not f.is_file(): continue
        if f.suffix in SKIP_EXTS: continue
        yield f


def _collect_decode(folder: Path):
    """Yield all .ghost files."""
    for f in sorted(folder.rglob("*" + GHOST_EXT)):
        if f.is_symlink(): continue
        if not f.is_file(): continue
        yield f


def process_folder_encode(src: Path, out: Path, verbose: bool = True):
    files = list(_collect_encode(src))
    if not files:
        print(f"\n{YELLOW}No encodable files found in {src}{RESET}")
        return

    _print_header("ENCODING", src, out, len(files))
    t0 = time.time()
    n_ok = n_fail = 0
    total_bytes = 0

    for f in files:
        rel = f.relative_to(src)
        dst = out / rel.parent / (rel.name + GHOST_EXT)
        if encode_file(f, dst, verbose):
            n_ok += 1
            total_bytes += f.stat().st_size
        else:
            n_fail += 1

    _print_summary("encode", n_ok, n_fail, total_bytes, time.time() - t0)


def process_folder_decode(src: Path, out: Path, verbose: bool = True):
    files = list(_collect_decode(src))
    if not files:
        print(f"\n{YELLOW}No .ghost files found in {src}{RESET}")
        return

    _print_header("DECODING", src, out, len(files))
    t0 = time.time()
    n_ok = n_fail = 0
    total_bytes = 0

    for f in files:
        rel     = f.relative_to(src)
        out_dir = out / rel.parent
        if decode_file(f, out_dir, verbose):
            n_ok += 1
            total_bytes += f.stat().st_size
        else:
            n_fail += 1

    _print_summary("decode", n_ok, n_fail, total_bytes, time.time() - t0)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _fmt_size(n: int) -> str:
    if n < 1024:        return f"{n} B"
    elif n < 1024**2:   return f"{n/1024:.1f} KB"
    elif n < 1024**3:   return f"{n/1024**2:.1f} MB"
    else:               return f"{n/1024**3:.2f} GB"


def _print_header(action: str, src: Path, out: Path, count: int):
    print(f"\n{BOLD}{CYAN}ghost-ink v{__version__}{RESET}  {DIM}zero-width unicode steganography{RESET}")
    print(f"{DIM}{'\u2500' * 56}{RESET}")
    print(f"  {BOLD}{action}{RESET}")
    print(f"  {DIM}from :{RESET} {src}")
    print(f"  {DIM}to   :{RESET} {out}")
    print(f"  {DIM}files:{RESET} {count}")
    print(f"{DIM}{'\u2500' * 56}{RESET}\n")


def _print_summary(action: str, n_ok: int, n_fail: int, total_bytes: int, elapsed: float):
    print(f"\n{DIM}{'\u2500' * 56}{RESET}")
    status = f"{GREEN}{BOLD}All good!{RESET}" if n_fail == 0 else f"{RED}{BOLD}{n_fail} failed{RESET}"
    print(f"  {status}  {GREEN}{n_ok} {action}d{RESET}  \u00b7  {_fmt_size(total_bytes)}  \u00b7  {elapsed:.2f}s")
    print(f"{DIM}{'\u2500' * 56}{RESET}\n")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="ghost-ink",
        description=(
            f"{BOLD}ghost-ink{RESET} \u2014 zero-width unicode steganography.\n"
            "Hides any file in plain sight. Human eyes see nothing. AI reads everything.\n\n"
            "Supports every language: Python, JS, TS, Rust, Go, C, C++, Java, Kotlin,\n"
            "Swift, PHP, Ruby, Shell, HTML, CSS, JSON, YAML, TOML, XML, Markdown,\n"
            "binary files, images, executables \u2014 literally everything."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"ghost-ink {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encode", help="Encode a folder (or single file) into .ghost files")
    enc.add_argument("input",  help="Source folder or single file")
    enc.add_argument("output", help="Output folder")
    enc.add_argument("-q", "--quiet", action="store_true", help="Suppress per-file output")

    dec = sub.add_parser("decode", help="Decode .ghost files back to originals")
    dec.add_argument("input",  help="Folder of .ghost files or single .ghost file")
    dec.add_argument("output", help="Output folder")
    dec.add_argument("-q", "--quiet", action="store_true", help="Suppress per-file output")

    args  = parser.parse_args()
    src   = Path(args.input).resolve()
    out   = Path(args.output).resolve()
    quiet = args.quiet

    if not src.exists():
        print(f"{RED}Error:{RESET} path does not exist: {src}", file=sys.stderr)
        sys.exit(1)

    if args.command == "encode":
        if src.is_file():
            out.mkdir(parents=True, exist_ok=True)
            encode_file(src, out / (src.name + GHOST_EXT), verbose=not quiet)
        else:
            process_folder_encode(src, out, verbose=not quiet)

    elif args.command == "decode":
        if src.is_file():
            decode_file(src, out, verbose=not quiet)
        else:
            process_folder_decode(src, out, verbose=not quiet)


if __name__ == "__main__":
    main()

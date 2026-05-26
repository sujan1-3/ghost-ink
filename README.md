# ghost-ink 👻

**Zero-Width Unicode Steganography Tool**

> Human eyes see nothing. AI reads everything.

`ghost-ink` encodes any file's content into invisible Unicode zero-width characters, woven into plain-looking carrier text. The output `.ghost` file appears as a single harmless comment to the human eye — but every byte of your original code is hidden inside it, recoverable perfectly.

---

## How It Works

Every byte of your file is split into four 2-bit pairs, each mapped to one of four invisible Unicode characters:

| Bits | Unicode | Name |
|------|---------|------|
| `00` | `U+200B` | Zero Width Space |
| `01` | `U+200C` | Zero Width Non-Joiner |
| `10` | `U+200D` | Zero Width Joiner |
| `11` | `U+2060` | Word Joiner |

These characters **render as nothing** in any text editor, terminal, or browser — but exist in the raw byte stream. An AI reading the file will see and can decode every character.

Each encoded file also stores a **SHA-256 hash** of the original content. Both encoding and decoding verify this hash — if even one character is corrupted, it raises an error instead of silently producing wrong output.

---

## Installation

```bash
git clone https://github.com/sujan1-3/ghost-ink
cd ghost-ink
python ghost_ink.py --help
```

No external dependencies. Pure Python 3.6+.

---

## Usage

### Encode a folder
```bash
python ghost_ink.py encode ./my_source_code ./hidden_output
```

Every file in `./my_source_code` becomes a `.ghost` file in `./hidden_output`.

### Decode a folder
```bash
python ghost_ink.py decode ./hidden_output ./recovered_code
```

Every `.ghost` file in `./hidden_output` is recovered perfectly into `./recovered_code`.

---

## Example

Original file `hello.py`:
```python
print("hello world")
```

After encoding, `hello.py.ghost` looks like:
```
// This file has been processed.
```
*(followed by thousands of invisible zero-width characters a human cannot see)*

Decoded back — **bit-perfect**, hash verified.

---

## Features

- ✅ Works on **any file type** (`.py`, `.js`, `.rs`, `.txt`, `.json`, binary, etc.)
- ✅ **SHA-256 verification** on both encode and decode — zero silent corruption
- ✅ **Roundtrip verified** at encode time — if verification fails, output file is deleted
- ✅ Handles **binary files** via base64 wrapping
- ✅ Preserves **folder structure** recursively
- ✅ Zero external dependencies

---

## Limitations

- A hex editor or Unicode inspector can detect zero-width characters
- Not a cryptographic security tool — use encryption for secrets
- Best used for IP watermarking, AI-readable metadata, or research purposes

---

*Built with 👻 by ghost-ink*

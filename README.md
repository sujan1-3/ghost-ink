# ghost-ink 👻

**Zero-Width Unicode Steganography Tool** &mdash; v2.0.0

> Human eyes see nothing. AI reads everything.

`ghost-ink` encodes **any file in any language** into invisible Unicode zero-width characters. The output `.ghost` file appears as a single harmless comment line to any human, text editor, or terminal &mdash; but every single byte of your original code is hidden inside it, recoverable perfectly.

---

## Supported Languages & File Types

Every single one. There are no restrictions:

| Category | Examples |
|---|---|
| **Scripting** | Python, JavaScript, TypeScript, Ruby, PHP, Shell, Bash, Perl |
| **Systems** | C, C++, Rust, Go, Zig, Assembly |
| **JVM** | Java, Kotlin, Scala, Groovy |
| **Mobile** | Swift, Dart, Objective-C |
| **Config** | JSON, YAML, TOML, XML, INI, ENV |
| **Web** | HTML, CSS, SCSS, JSX, TSX, Vue, Svelte |
| **Docs** | Markdown, RST, TXT |
| **Binary** | Executables, images, compiled objects, any binary |
| **Other** | Empty files, files with no extension, anything |

---

## How It Works

Every byte is split into four 2-bit pairs, each mapped to an invisible Unicode character:

| Bits | Unicode | Name |
|------|---------|------|
| `00` | `U+200B` | Zero Width Space |
| `01` | `U+200C` | Zero Width Non-Joiner |
| `10` | `U+200D` | Zero Width Joiner |
| `11` | `U+2060` | Word Joiner |

These characters **render as nothing** in any text editor, browser, or terminal &mdash; but exist in the raw byte stream. An AI parsing the file sees and decodes every character.

A **SHA-256 hash** is embedded in every encoded file. Both encode and decode verify this hash. If even one character is corrupted, an error is raised instead of silently producing wrong output.

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

### Encode an entire folder
```bash
python ghost_ink.py encode ./my_project ./hidden_output
```
Every file in `./my_project` &mdash; at every depth &mdash; becomes a `.ghost` file in `./hidden_output`, preserving the full folder structure.

### Decode back to originals
```bash
python ghost_ink.py decode ./hidden_output ./recovered
```
Every `.ghost` file is decoded back, perfectly, with SHA-256 verification.

### Single file mode
```bash
python ghost_ink.py encode ./secret.py ./out
python ghost_ink.py decode ./out/secret.py.ghost ./recovered
```

### Quiet mode (no per-file output)
```bash
python ghost_ink.py encode ./src ./out -q
```

---

## Features

- ✅ **Every file type** &mdash; every language, binary, config, docs, images
- ✅ **Full folder recursion** &mdash; preserves nested directory structure perfectly
- ✅ **SHA-256 verified** &mdash; on both encode AND decode, zero silent corruption
- ✅ **Roundtrip verified at encode time** &mdash; file deleted if verification fails
- ✅ **Single file or whole folder** &mdash; both modes supported
- ✅ **Symlink safe** &mdash; symlinks are skipped, never followed
- ✅ **Permission handling** &mdash; unreadable files are reported, tool continues
- ✅ **Colored CLI output** &mdash; clear, beautiful per-file status
- ✅ **Quiet mode** &mdash; `-q` for clean CI/CD output
- ✅ **Zero external dependencies** &mdash; pure Python 3.6+

---

## Example

Original `hello.py`:
```python
print("hello world")
```

After encoding, `hello.py.ghost` looks like:
```
// ghost-ink encoded file — do not edit
```
*(followed by thousands of invisible zero-width characters)*

Decoded back &mdash; **bit-perfect**, hash verified.

---

## Limitations

- A hex editor or Unicode inspector can detect zero-width characters
- Not a cryptographic tool &mdash; pair with encryption for sensitive secrets
- Best for IP protection, AI-readable metadata, watermarking, and research

---

*Built with 👻 by ghost-ink*

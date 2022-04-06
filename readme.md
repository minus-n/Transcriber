# Transcriber

A program to directly get transcribe text from one script (e.g. Latin) to another one (e.g. Japanese hiragana).

## Implementation

To know how to transcribe one language into another, this program reads yaml-files of the following structure:

```yaml
name: <transcription name>

rules:
    - regexpr0: repl0
    - regexpr1: repl1
    - regexpr2: repl2
    - ... # and so on

---

# next rule
```


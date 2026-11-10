# Sandhi

`openodia.sandhi` needs a release newer than 0.1.14: `import openodia.sandhi` fails on 0.1.14. `split` and `join` NFC-normalize. For a compound the splitter accepts, `join(split(word))` equals the NFC form of the word.

::: openodia.sandhi

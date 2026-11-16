# Brief: write the AV reason (column AV) for Sony Japan

Sony Japan reviews each proposed Vietnamese fix:
- column **AD** = their present translation;
- **AN** = our proposal;
- **AU** = error type;
- **AV** = the reason, in English.

Sony never sees our drafts.

Each item in your pack has:
- `EN`;
- `OLD` (= AD);
- `FINAL` (= AN);
- `AU` letter (B better translation, F fatal photographic-term error, S spelling, G grammar, O other);
- optional `PRIOR-PROPOSAL` / `PRIOR-REASON` (an earlier draft and its reason, possibly outdated);
- `REVIEWER-NOTE` (why reviewers changed the draft; it is written about the draft, not about AD);
- `⏎` marks a line break.

## Write one reason per item, explaining AD → AN
- Say what is wrong with AD and what AN fixes.
- Refer to the texts as **AD** and **AN**. Refer to other strings by their **S#**.
- Never write OLD, NEW, FINAL, CUR, draft, prior proposal, reviewer, persona, or internal ids like "item 1234".
- Quote Vietnamese in single quotes: `AD 'c.năng' is over-abbreviated; Function = 'chức năng'.`
- Reuse correct parts of PRIOR-REASON. Drop the parts that no longer match AN.
- 8 to 30 words. Plain and specific.
- If AU does not fit the reason, still write the reason, and add `"au_note"` with the letter you think fits.

## Output (JSONL, one line per item)
```
{"id": 123, "av": "AD 'c.năng' is over-abbreviated and hard to read. Function = 'chức năng'."}
{"id": 456, "av": "...", "au_note": "B"}
```

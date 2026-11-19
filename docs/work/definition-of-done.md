# Definition of done

A story is not Done until every box is checked:

- [ ] Every acceptance criterion in the story file is checked and re-verified
      after the final edit (run the command, read the output).
- [ ] `python -m pytest` passes at the repo root.
- [ ] Any new network/data dependency is documented in README (endpoint, auth,
      rate limits).
- [ ] No placeholder or fabricated data is presented as real; demo/seed data is
      labeled as such.
- [ ] Changes are committed with a message referencing the story ID.

## Reminder

Edit `docs/work/items/` directly. Scan `docs/work/items/` and
`docs/work/archive/` before minting a new ID — IDs are stable and never reused.
Never delete `docs/agile/` or `docs/work/archive/`.

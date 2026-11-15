I wrote formal/agent_a.yaml. `fcp lint` reports 3 errors, all in the bundle's requirements.yaml, which I did not change: R-FR-1, R-FR-2 and R-FR-3 point at frame.md lines 56-58, but their quotes are on lines 57-59 (`fcp anchor` should fix them). Apart from those the set lints clean; `fcp explain` reads back as intended; the spec-only analyses (`fcp check --no-mutation`) find no tautologies, the example scenario possible, and one conflict.

13 items, all starting with SA-: 12 properties (signature 1, range check 2, storing 1, never open balance.txt / write the temp file then move it 3, fsync-and-close 1, return value 1, cleanup 1, keeping the temp file 2) and 1 scenario (the example with 1250). Two pieces of ghost state, only because the trace has no signal for file state: which file object is balance.txt.tmp, and whether that file is missing, empty, holds exactly the digits, or something else. Ambiguity choices: R-SYNC-1 reading 1 (fsync the file, no flush required; the example has no flush either); R-CLEAN-1 reading 1 (no temp file once the function returns).

Unformalized: R-FR-1..3, the frame rules already added to every set (covered by F-END, F-ZERO, F-LIMIT).

Problems in the specification:
1. Rule 6 contradicts rule 7 ("leave no temporary file behind" vs "if os.replace fails, keep balance.txt.tmp"); `fcp check` confirms it: save_balance(0) with the answer ["fail"] has no correct behaviour.
2. Rule 2 is unconditional, but every os.replace can fail; I excused runs where an os.replace failed.
3. Rule 5 overlaps rule 1 ("False otherwise" would cover out-of-range amounts); I applied rule 5 to in-range amounts only.
4. Retrying is contradictory: a retry of os.replace that succeeds after a failure needs True under rule 5 and False under rule 7.
5. "Negative" cannot be checked: cents is an unsigned 27-bit signal.
6. The procedure is not crash-safe: rule 4 and the example fsync without flushing Python's buffer, and the text never requires the fsync after the write.
7. Limits of the encoding: "0" and "" both read as 0; digits split across writes are not recognised; "./balance.txt" does not count as balance.txt; the earlier content of balance.txt is not modelled; "once" in rule 5 read as "when".

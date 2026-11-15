I wrote formal/agent_b.yaml (set: agent_b) with 18 items: 17 properties and 1 scenario. Lint reports 3 errors in the real workspace, all wrong line numbers in requirements.yaml (R-FR-1..3 point to frame.md lines 56-58, the rules are on 57-59); on a copy with those fixed, lint is clean, and `fcp explain` reads back as intended.

The model: ghost state tracks the two files: whether each exists, the file object from its latest writing open, whether it was closed (and, for the temporary file, synced), and its content (empty, exactly the digits of cents, something else, or what was there before the run). Moves and removals carry this state between paths; a further ghost follows the example's call sequence. Every output is checked against the model.

Items per requirement: R-SIG-1 1; R-ERR-1 2 (no file call at all over 100,000,000, and ValueError); R-STORE-1 2; R-TMP-1 4 (never opens balance.txt; every os.replace is tmp -> balance.txt; the temp file holds the digits when moved; the move is attempted); R-SYNC-1 2; R-RET-1 2; R-CLEAN-1 1; R-KEEP-1 2 (after a failed os.replace, returns False, and the temp file is kept with the digits); R-EX-1 a scenario. Reading 1 for both flagged phrases (R-SYNC-1, R-CLEAN-1). Unformalized: R-FR-1..3 (frame rules, covered_by F-END, F-ZERO, F-LIMIT).

Problems in the specification:
1. Rule 6 contradicts rule 7; `fcp check` finds the conflict on save_balance(0) with the script ["fail"].
2. Rule 2 cannot be met unconditionally because os.replace can fail; applied only to runs where no os.replace failed. Rule 1 read as a precondition.
3. Rules 5 and 7 conflict if a failed os.replace is retried and then succeeds.
4. R-SYNC-1 reading 1 means no flush is required, following the example, though fsync without a flush may not get the digits to disk.
5. "Negative" cannot be tested (cents is unsigned).
6. Encoding limits: digits over several writes or with leading zeros are misjudged; "text file" and "current directory" only through the relative-name codes; how modes like w+ map to o_mode is not specified.

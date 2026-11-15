49 requirements anchored (32 guarantees, 8 definitions, 5 assumptions, 3 dont_cares, 1 non-functional); 36 with ambiguity entries.
Contradictions: (1) 'cmd_ready only while no response pending' vs 'may accept the next command in the response-handshake cycle'; (2) 'equals' vs 'don't care' on the response fields (consistent only if equalities apply while rsp_valid is high); (3) reset vs hold/stability rules (no stated precedence).
Checked consistent: 4-cycle pready bound and 8-cycle response bound (worst case 6-7).
Gaps: cmd_ready liveness (a bridge that never raises cmd_ready again conforms); rsp_rdata on write responses; pwdata on reads; missing 'low otherwise' statements; slave violating the pready bound; reset mid-transfer; undefined terms. Recorded the 'may' permission as dont_care (low confidence).
Tool issue reported: fcp only ran from the project directory (fixed earlier).

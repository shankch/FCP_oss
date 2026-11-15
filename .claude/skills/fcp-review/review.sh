#!/bin/bash
# review.sh DIR [arguments of `fcp review` other than --out]
#
# One FCP review, written into DIR.  Progress goes to DIR/review.log, whose
# last line is "EXIT <code>".  The review is stopped after FCP_REVIEW_SECONDS
# (default: three hours).  The launcher is the one of the checkout this
# script is in; FCP_BIN names another.  Where DIR lies in a directory named
# .fcp-review, that directory gets a .gitignore that ignores all it holds:
# reviews stay out of commits, and nothing tracked or under .git changes.
set -u
here=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
fcp=${FCP_BIN:-$here/../../../bin/fcp}
if [ $# -lt 1 ]; then
    echo "usage: review.sh DIR --request FILE (--code FILE [--entry MODULE] | --signature FILE) [--resume]" >&2
    exit 2
fi
dir=$1; shift
if [ ! -x "$fcp" ]; then
    echo "no fcp launcher at $fcp (set FCP_BIN)" >&2
    exit 2
fi
mkdir -p "$dir" || exit 2
top=$(dirname "$(readlink -f "$dir")")
if [ "$(basename "$top")" = .fcp-review ] && [ ! -e "$top/.gitignore" ]; then
    echo '*' > "$top/.gitignore"
fi
log=$dir/review.log
date +"START %F %H:%M:%S" >> "$log"
timeout "${FCP_REVIEW_SECONDS:-10800}" "$fcp" review "$@" --out "$dir" >> "$log" 2>&1
code=$?
[ $code -eq 124 ] && echo "stopped at the time limit of ${FCP_REVIEW_SECONDS:-10800} s" >> "$log"
echo "EXIT $code" >> "$log"
if [ -f "$dir/review.md" ] && [ $code -eq 0 ]; then
    echo "review written: $dir/review.md"
    sed -n 3,5p "$dir/review.md" | grep -v '^$'
else
    echo "no review (exit code $code); the last lines of $log:"
    tail -n 6 "$log"
fi
exit $code

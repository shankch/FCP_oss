---
name: fcp-review
description: Review code against the request it was written for, with FCP. Agents formalize the request without seeing the code, the engine checks the code against their readings, and the result is a short list of questions for the author, each with a concrete call, in place of a diff to read. Also reviews a request before any code is written. A review takes 20 to 60 minutes and four or five agent runs, so it is started only when the user asks for one.
argument-hint: "[code.py | package dir] [request.md]   or   [directory of a finished review]"
disable-model-invocation: true
---

# FCP review

An FCP review tells the author of a request where the answer rests on
something the request did not settle. Two agents formalize the request apart
from each other, without the body of the code. The engine checks the code
against both readings and compares the readings with each other. A
requirement that both readings state the same way, that the code meets and
that is in no conflict is certified. Everything else comes back as a question
with a concrete call. The author answers questions; they do not read lines.

A review takes 20 to 60 minutes and four or five agent runs through
`claude -p`. The runs count against the user's usage (about $4 on a short
request). It therefore runs in the background, and only when the user asked
for it.

What the user passed: $ARGUMENTS

## 1. What is asked

If the argument is a directory that holds `review.md`, the review is finished:
go to step 4.

Otherwise this is a new review, and it needs two things.

**The request** is what the author asked for, in the author's words. If an
argument names a file with it, use that file. If not, it is in this
conversation: the message that asked for the code, and every later message
that changed what is asked. Copy those messages word for word, in order, and
nothing else. Leave out your replies, your plan and anything you assumed
while you wrote the code. The review exists to find what the code assumed,
and a request that already states those assumptions hides them.

**The code** is one Python file, or a package directory with the dotted name
of the module that holds its entry point. If no argument names it, it is the
file you wrote for the request. A review sees code through calls and
answers: arguments, return values, exceptions, the state of an object from
one call to the next, the calls the code makes on a service it receives or
imports, the files it opens. Code whose behavior lies elsewhere (a user
interface, threads, timing, floating-point results) is outside a review. Say
so and stop; do not start a review that cannot speak about what matters.

**No code yet.** A review also runs on a request alone, before anything is
written. Write the `def` line of the function the request asks for to
`signature.py` in the review directory and pass `--signature` in place of
`--code`. The review then ends with the questions the request raises.

Ask before you start when you cannot tell which messages make up the request
or which file is the code, and when you put the request together from more
than one message: show the text and let the user correct it. A review of the
wrong request costs as much as a review of the right one.

## 2. Start

Choose a new directory for the review, `.fcp-review/<date>-<time>/` under the
project root, and write the request to `request.md` in it (writing the file
makes the directory). Leave git alone: the script below writes a `.gitignore`
into `.fcp-review/` that ignores everything there, so reviews stay out of
commits and no tracked file changes.

Start one of these as a background command:

```bash
"${CLAUDE_SKILL_DIR}/review.sh" DIR --request DIR/request.md --code FILE
"${CLAUDE_SKILL_DIR}/review.sh" DIR --request DIR/request.md --code PACKAGE_DIR --entry DOTTED.MODULE
"${CLAUDE_SKILL_DIR}/review.sh" DIR --request DIR/request.md --signature DIR/signature.py
```

The script runs `fcp review` with a limit of three hours, writes its
progress to `DIR/review.log` and ends that log with `EXIT <code>`. Tell the
user that the review is running, where it writes, and what it costs (20 to
60 minutes, four or five agent runs). You may go on with other work, but leave the
code under review as it is: the check reads the file near the end of the
review, so a change made meanwhile is what gets checked, against a request
that was read before the change.

## 3. When the command ends

`EXIT 0` with a `review.md` in the directory: go to step 4.

Anything else: read the end of `review.log` and tell the user what stopped
the review, in the log's words. Common causes are a usage limit, a machine on
which the agents' sandbox does not start, and code the first agent could not
describe as calls and answers. Do not run it again unchanged. After the
cause is removed, run the same command with `--resume` added: when both
readings are already in the directory it goes on from them and no agent
runs a second time; when they are not, it starts over.

## 4. Report

Read `DIR/review.md`. For the words of a requirement that the report names
only by its id, read `DIR/bundle/requirements.yaml`. Then tell the user, in
this order:

1. If the report begins with "This review is partial": which steps of the
   check did not end, and why. Nothing that rests on them is certified.
   Where the report lists under a step the requirements that rest on it,
   name them: that step holds back only those.
2. The counts: how many requirements are certified, how many questions.
3. Every question, numbered as in the report and in its order: the
   requirement in the request's words, the question, and the calls under it
   exactly as printed.
4. In a sentence each, where the report has them: the certified
   requirements that a third reader reads another way and that do not wait
   for the shared answers, with the report's reason and what its searches
   covered (the sentence that closes "Shared answers"); what the readings
   take as given; what the request asks that a review does not judge
   ("Outside this review"); calls that were found and not shown; and the
   limits of the review.

Where several questions turn on the same phrase of the request, say which:
one decision may answer them all.

What the kinds of question mean:

| Kind | What the engine found |
|---|---|
| `code` | The code breaks the requirement on the call shown, which was run again. The code is wrong, or the reading is. |
| `conflict` | No implementation can meet these requirements on the calls shown. One of them has to give way. |
| `open` | The request does not say what the answer is on this call. The code picked one. |
| `readings` | The two readers understood the requirement differently. The call is one where that changes the answer. |
| `depends` | Both readers gave the same answer to the phrases under "Shared answers". A third reader that took the other answer reads these requirements differently. With code, the question lists those on which that reading may reject a run that a reader accepts, or was not shown to accept every such run, and those the review does not certify for another reason (the code breaks it, the readers disagree, a step failed); a certified requirement on which it accepts every run the readers accept is named in the sentence that closes "Shared answers". |
| `ambiguity` | A phrase that can be read in the ways listed. No call: this was flagged when the request was split into requirements. |
| `scenario` | An example in the request can never happen under the rules a reader took from it. |
| `unformalized` | A reader wrote no rule for the requirement, so nothing was checked against it. |
| `undecided` | A comparison of readings did not end, the call it found did not hold when it was run again, or there was no behavior to compare the readings on. Nothing was shown either way, so there is no call, and the requirement is not certified. The question reports a search, not a fact about the request: say so. |

Three things keep the report honest:

- Do not answer the questions, and do not order them by what you think the
  author meant. You wrote the code, or would write it, so your view of what
  the request means is the thing under review.
- Do not change the code before the author has answered.
- Say "certified" as the report means it: the code meets what both readers
  took the request to say, on every call of the scope the engine drew, and
  for every call where the report says "proved". It is not a statement that
  the code is correct.

## 5. After the answers

Each answer is a decision about the request. Add the answers to the end of
`DIR/request.md` under the heading `Decisions`, in the author's words, so the
request and its decisions stay in one place. (A review that was not started
here has no `request.md`. Ask which file holds the request; the copy the
review read is `DIR/bundle/spec.md`.) Where an answer goes against
what the code does, change the code, and say which question each change
answers. A review of the changed code is a new review in a new directory
with the request as it now reads: offer it, with its cost, and start it only
when the user says so.

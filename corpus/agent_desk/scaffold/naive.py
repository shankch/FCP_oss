"""Pinecrest returns desk: a pass-through scaffold, i.e. a plain ReAct loop.

Whatever the LLM proposes runs, until a handoff or close ends the
conversation.  Every rule of the prompt is left to the model.  Compiled to
rtl/naive.v by corpus/agent_desk/build.py.
"""

NONE, SAY, VERIFY, LOOKUP, CONFIRM, REFUND, HANDOFF, CLOSE = 0, 1, 2, 3, 4, 5, 6, 7

PRE = {'p_act': 3, 'p_ord': 1, 'p_amt': 9, 'p_more': 1, 'human': 1}
POST = {'id_ok': 1, 'elig': 1, 'total': 9, 'accepted': 1}
OUT = {'say': 1, 'verify': 1, 'lookup': 1, 'confirm': 1, 'refund': 1, 'handoff': 1, 'close': 1,
       'ord': 1, 'amt': 9, 'more': 1, 'done': 1}
REGS = {'done': (1, 0)}


def decide(i, r, o):
    act = NONE if r.done else i.p_act
    o.say = act == SAY
    o.verify = act == VERIFY
    o.lookup = act == LOOKUP
    o.confirm = act == CONFIRM
    o.refund = act == REFUND
    o.handoff = act == HANDOFF
    o.close = act == CLOSE
    o.ord = i.p_ord if (act == LOOKUP or act == CONFIRM or act == REFUND) else 0
    o.amt = i.p_amt if (act == CONFIRM or act == REFUND) else 0
    o.more = i.p_more if act == SAY else 0
    o.done = r.done


def update(i, r, o, n):
    if o.handoff or o.close:
        n.done = 1

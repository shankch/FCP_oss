"""Pinecrest returns desk: the guard kernel of the agent scaffold.

Every turn the LLM proposes one tool call.  decide() chooses what actually
runs: the proposal, nothing (the proposal is blocked and the LLM is told so),
or a handoff that the scaffold starts on its own.  update() records the
result of the tool that ran.  This file runs inside the agent
(fcp.kernel.Runtime) and is compiled to rtl/ref.v (fcp.kernel.verilog) by
corpus/agent_desk/build.py.
"""

NONE, SAY, VERIFY, LOOKUP, CONFIRM, REFUND, HANDOFF, CLOSE = 0, 1, 2, 3, 4, 5, 6, 7
LIMIT = 150          # dollars: a larger refund needs a human (rule 6)
MAX_FAILS = 2        # failed verifications that force a handoff (rule 2)

PRE = {'p_act': 3, 'p_ord': 1, 'p_amt': 9, 'p_more': 1, 'human': 1}
POST = {'id_ok': 1, 'elig': 1, 'total': 9, 'accepted': 1}
OUT = {'say': 1, 'verify': 1, 'lookup': 1, 'confirm': 1, 'refund': 1, 'handoff': 1, 'close': 1,
       'ord': 1, 'amt': 9, 'more': 1, 'done': 1}
REGS = {
    'done': (1, 0),       # the conversation has ended
    'verified': (1, 0),   # a verification has succeeded
    'fails': (2, 0),      # failed verifications (saturates at 3)
    'okay': (2, 0),       # per order: eligible at its last lookup (0 if never looked up)
    'tot0': (9, 0),       # per order: total at its last lookup
    'tot1': (9, 0),
    'paid': (2, 0),       # per order: refunded
    'c_yes': (1, 0),      # the latest confirmation was answered Yes and is unused ...
    'c_ord': (1, 0),      # ... for this order
    'c_amt': (9, 0),      # ... and this amount
    'asked': (1, 0),      # a message has asked whether there is anything else
}


def decide(i, r, o):
    act = i.p_act
    if r.done:
        act = NONE                                  # the conversation is over
    elif i.human:
        act = HANDOFF                               # rule 8: the button wins
    elif r.fails >= MAX_FAILS:
        act = HANDOFF                               # rule 2
    elif act == LOOKUP:
        if not r.verified:
            act = NONE                              # rule 1
    elif act == REFUND:
        okay = (r.okay >> i.p_ord) & 1
        total = r.tot1 if i.p_ord else r.tot0
        paid = (r.paid >> i.p_ord) & 1
        confirmed = r.c_yes and r.c_ord == i.p_ord and r.c_amt == i.p_amt
        if not (okay == 1 and confirmed and i.p_amt <= total and i.p_amt <= LIMIT and paid == 0):
            act = NONE                              # rules 3, 4, 5, 6, 7
    elif act == CLOSE:
        if not r.asked:
            act = NONE                              # rule 9 (for close; a handoff is never delayed)
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
    if o.verify:
        if i.id_ok:
            n.verified = 1
        elif r.fails < 3:
            n.fails = r.fails + 1
    if o.lookup:
        bit = 1 << o.ord
        n.okay = (r.okay | bit) if i.elig else (r.okay & ~bit)
        if o.ord:
            n.tot1 = i.total
        else:
            n.tot0 = i.total
    if o.confirm:
        n.c_yes = i.accepted
        n.c_ord = o.ord
        n.c_amt = o.amt
    if o.refund:
        n.paid = r.paid | (1 << o.ord)
        n.c_yes = 0
    if o.say and o.more:
        n.asked = 1

---
name: Agent message or handoff
about: Send a question, finding, review request, blocker or handoff to another role
labels: 'agent:thread'
title: '[Agent message] '
---
<!-- openrx:thread:v1 -->

### To
coordinator

### From
agent-name/unique-session

### Kind
question / finding / review-request / blocker / handoff

### Related task and reply-to
Link the task and original message/comment. Keep replies on this issue rather than duplicating the conversation.

### Message
State the finding or question, distinguish evidence from inference, and say what response is needed.
Valid recipients: coordinator, research, benchmark, tooling, simulation, rtl, review, all.

### Evidence
Link sources, commits, tests or run logs. Include uncertainty and failures.

### Next action / acceptance
What should the recipient do, and what would resolve this message?
A router receipt confirms indexing, not that an AI has read or acted on the message.

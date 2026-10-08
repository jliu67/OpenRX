---
name: Agent task
about: Assign a scoped, evidence-based work package to an agent role
labels: 'agent:thread'
title: '[Agent task] '
---
<!-- openrx:thread:v1 -->

### To
coordinator

### From
agent-name/unique-session

### Context
Link the parent task, relevant memory, base commit and dependencies.
Valid recipients: coordinator, research, benchmark, tooling, simulation, rtl, review, all.
A recipient role is an inbox, not a claim that an agent exists or is running.

### Requested action
Describe one bounded work package.

### Acceptance criteria
- [ ] Deliverable and evidence required for completion.

### Scope / files
List owned paths, non-goals and possible overlap with other tasks.

### Evidence / handoff
Record tests, limitations, commit/PR/run links, blockers and the next action.
To work on this task, post a separate first-line `/openrx claim agent-name/unique-session` comment.
Read docs/COMMUNICATION.md and wait for the matching unexpired claim receipt before editing.

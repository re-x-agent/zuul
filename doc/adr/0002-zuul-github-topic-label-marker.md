# 0002 The form of the topic read by Zuul's GitHub driver: the marker form (`topic:` + label value), exact match, a per-connection option (2026-11-09)

Status: **Decided** (user decision; a series of judgments from 2026-11-09 18:18 to 20:03; the final form follows the definition fixed on 2026-11-09 19:53).
Sources: internal working records of the author (not public), and the prototype with its verification evidence: https://github.com/re-x-agent/zuul/compare/14.3.0...topic-label-deps (discussion: https://github.com/re-x-agent/zuul/pull/1).
Related: ADR 0001 (decision 1: a Topic is attached with a GitHub label). This ADR defines how Zuul's GitHub driver reads that Topic.

## Background

- GitHub has no field for a topic. Nothing on GitHub corresponds to the topic that Gerrit has (an attribute that groups changes), and Zuul's GitHub driver can read only `Depends-On:` as a dependency declaration.
- A GitHub label is **only one string, its name**. GitHub has no structure that splits a label into a "name" and a "value". Therefore, reading the label `topic:release-1.4` as "the name `topic` and the value `release-1.4`" is **a convention of how our driver reads it**, not a GitHub specification. This convention has to be made explicit and fixed in a form that is hard to change.

## Decision

### 1. The form is the marker form (label name + separator + label value)
- A label is read as "label name + separator (`:`) + label value". **marker = label name + separator** (the configured value is `topic:`).
- The topic is the **label value** after the marker (everything after the first separator). A label that does not start with the marker is not a topic label.
- The marker is matched case-insensitively (in line with GitHub label names). The value keeps its original spelling.

### 2. Matching is exact match of the value only
- Whether two pull requests have the same topic is decided only by whether the label values **match exactly**. Prefix matching, partial matching and degrees of closeness are not used.
- Reason: `1` and `11` must not be mixed (with prefix matching, `topic:11` would join the set of `topic:1`). The simplicity of looking only at whether there is a match is kept.
- Guarantee in the implementation: each Search result has its topic derived again from the labels of the pull request, and only the results that match the requested topic exactly are kept (nothing is mixed even if the Search side is loose).

### 3. The setting is an option of each GitHub connection
- `topic_label_marker` in the GitHub connection section of `zuul.conf` (no default = disabled). Enabling needs this option plus the existing queue setting `dependencies-by-topic` (and `allow-circular-dependencies`).
- Reason: the convention of how labels are read belongs **at the boundary of the connection (the external system, GitHub)**; it is not a setting of a tenant or a job. The same reading applies to all tenants on the same GitHub.

### 4. The term is marker
- The option is named `topic_label_marker`, and the word for this mechanism is marker (the configured value `topic:` is the label name + separator).
- Reason: it was adopted because marker is a name that directly expresses what it is, **a mark that shows the boundary between the label name and the label value**.

## Alternatives not adopted, and why

- **No setting; the label name itself is the topic (pull requests that share a label form a set)**: implemented and taken as far as tests (topic tests 13/13 passing) and put on the fork, but not adopted. Any label (for example `bug`) would form a set, so unrelated pull requests would be gated together as one set. The user decided to return to the marker form (2026-11-09 19:36).
- **Listing the label names of topics in the configuration**: not adopted. It is the user's wish not to list them in the configuration ("I do not want to configure it").
- **The name "prefix" (calling it a "prefix")**: not adopted. "prefix" suggests prefix matching, which disagrees with the fact that matching is exact. The misunderstanding "if it is a prefix, do pull requests form a set by prefix match?" occurred repeatedly.

## Consequences

- The label value of `topic:a:b` is `a:b` (split at the first separator; the value is everything that remains). `topic:a` and `topic:a:b` are different topics and do not form a set. This is fixed by a dedicated test (`test_topic_value_with_separator`).
- Aligning the digits of numbers (for example wanting `topic:01` and `topic:1` to be the same) is **something for people to take care of**; the matching by the machine does not mix them whatever the notation (they are treated as different values because matching is exact).
- The trial (`aether-zuul-01`) is running with `zuul-scheduler-topic:14.3.0-topic3` and `topic_label_marker=topic:`.
- Remaining points (described in Open questions of the draft): pull requests with several topic labels (currently the lexicographically smallest one is used), the delay until Search reflects a label (measured 5.6 to 10.7 seconds, n=5), and re-enqueueing when the members of a queued set increase or decrease.

### Outlook (a record of possibilities; not an implementation decision)

- Because the boundary is expressed by a separator, **room for extension remains on the value side** in the future (for example multi-value, where one label has several values).
- This is a record of a possibility and **not an implementation decision**. The current form does not change: "everything after the first separator is one value, and matching is exact match" (the value of `topic:a:b` is `a:b`; a separator inside the value has no special meaning). Whether to extend it, and in what form, is left to a separate decision.

## Evidence

- Verification run: on 2026-11-09 16:40, with the prototype of the marker form, the same topic label was put on pull requests in 3 repositories (web #24, mobile #563, resolver #124), and `gate_dev` combined them into one set and ran it to completion (buildset `8882b07bf2b7496aa4610a983b79b243`). The option was then named `topic_label_prefix` (only the name changed afterwards; the behavior is unchanged).
- Fork (a copy for evidence, based on Zuul 14.3.0): https://github.com/re-x-agent/zuul/compare/14.3.0...topic-label-deps
- Tests: `tests/unit/test_github_topic.py` (14 topic tests pass; `1` and `11`, a loose Search, labels whose value contains `:`, and others).

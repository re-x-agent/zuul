Branch-Assigned Queues
======================

.. warning:: This is not authoritative documentation.  These features
   are not currently available in Zuul.  They may change significantly
   before final implementation, or may never be fully completed.

The following document describes a change to Zuul's shared change
queue behavior to support a wider variety of project organizational
structures and development methodologies.

Introduction
------------

We describe Zuul as a project gating system because the main purpose
is to control which changes are merged.  A key to how Zuul performs
this activity is controlling the order in which changes are merged.
By doing so, Zuul is able to stack multiple changes on top of each
other when it builds its proposed future states of multiple
repositories.

In order to ensure the correct co-gating behavior between multiple
repositories, all of the repositories which could affect the outcome
of integration test jobs must share a single queue so that if changes
to project A and project B are to be merged, they are tested together.

We found early on that it is worthwhile to minimize the number of
projects involved in a single queue.  The queue must include all the
projects in the integration tests that cover the projects, but ideally
no more than that.  If project C is not involved in the testing of
projects A and B, then it is counter-productive for a change to C to
wait in the queue behind changes to A and B.

In Zuul, a pipeline defines a workflow action, and it contains one or
more queues that it uses when performing that action.  A "gate"
pipeline in Zuul which is responsible for merging changes may have a
single shared queue for all projects, or it may have multiple queues,
one for each individual project, or, more typically, a handful of
queues each for a collection of projects.

There are currently two styles of shared change queues.  The
traditional behavior is that all changes for all projects that are
added to the queue enter that single queue.  That means that changes
that involve different branches share a single queue.  This is to
support a development process where branches interact with each other.
For example, OpenStack ensures that it can upgrade from the most
recent stable branch to master.  There is an upgrade job that acts as
an integration test between these two branches (just as other jobs act
as an integration test between different projects).  In order to
ensure changes to either branch don't break the upgrade test job,
changes to both branches must be sequenced in the shared change queue.

The other style is a "per-branch" queue.  This facilitates a
development process where different branches do not interact with each
other.  For example, an embedded system manufacturer may have a branch
for one hardware revision, and a different branch for another.  There
is no need to coordinate changes between these branches, so the
"per-branch" setting can be enabled which means that changes to branch
X of any involved project go into one queue, and changes to branch Y
of any involved project go into another.  This allows developers of
different hardware to work independently while still performing
integration testing of their whole system.

A third style of development is currently unsupported: systems where
projects have multiple independent branches, but the coordination of
those branches across multiple projects is not done by sharing a
common branch name.  If we consider the previous "per-branch" case,
that works under the assumption that all of the branches involved in
hardware revision 1 use a name like "hw1" and all the branches
involved in revision 2 use "hw2".  But if a system is composed from
arbitrary branches of multiple repositories, there is no way to build
corresponding change queues in Zuul.  This document proposes a way to
do that.

Proposal
--------

The proposed change is simple: to allow users a third way of composing
change queues where individual project-branch combinations can be
assigned to specific queues.  In contrast to the traditional and
"per-branch" queues, we will call this a "branch-assigned" queue.

The default state of any project that is not assigned to a queue is
for Zuul to dynamically create a queue that contains only that
project.  If a user adds a project to a traditional queue, then all
branches of that project are added to that queue.  If the user adds a
project to a per-branch queue, then each branch of the project is
added to the queue for that branch.

When a user assigns a project-branch combination to a branch-assigned
queue, only that specific project-branch will be added to that queue.
Each other project-branch combination may be added to a different
queue.  Any project-branch combinations not explicitly specified will
be subject to a fallback behavior described below.

If any branch of the project specifies either a traditional or
per-branch queue, then that will be considered the default queue for
the project.  If the user does neither, then the default queue for the
project will be (as it is now) an automatically created traditional
queue that contains only that project.  Any project-branch combination
that does not specify a branch-assigned queue will use the default
queue for the project.

The behavior when determining what queue a change for a given
project-branch will be assigned to is therefore:

* If this project-branch was assigned to a branch-assigned queue, use that
* If the project was assigned to a traditional or per-branch queue, use that
* Use the automatically created traditional queue

User Interface
--------------

Currently, a project may only be assigned to a single queue, therefore
when we first see a ``queue`` attribute in a ``project`` stanza for a
given project, we take that as the project's queue and ignore any
subsequent appearances.  That means that if a project has a ``project``
stanza in every branch of its repo, we consider only the one on the
master branch and ignore the rest.

The simplest and most intuitive way to support a branch-assigned queue
is to lift this restriction, and therefore, if the ``project`` stanza
on the master branch declares ``queue: foo`` and on the stable branch
declares ``queue: bar``, then the master branch will be in `foo` and
the stable branch in `bar`.

However, that may be an unexpected behavior change for existing users
since they may be relying on the current behavior to ignore obsolete
values in older branches.  Or they may remove ``queue`` attributes
from ``project`` stanzas in older branches.  Therefore, we should
expect users to opt-in to this behavior.  We will add a new attribute
to the ``queue`` object itself to indicate what type of queue it is.

We will add a ``type`` attribute to the queue object which can be one
of the following values: ``all-branches``, ``per-branch``, and
``branch-assigned``.

The ``all-branches`` value will be the default and is the traditional
queue behavior.  The ``per-branch`` value will be a synonym for
``per-branch: true``.  The ``per-branch`` attribute will be
deprecated.

We will use the new ``type`` attribute instead of adding a new
``branch-assigned: true`` attribute because ``per-branch`` and
``branch-assigned`` should be mutually exclusive (and neither one is
also a traditional ``all-branches`` queue).

It will be an error to specify both ``type`` and ``per-branch``
attributes.

If a ``project`` stanza declares a queue assignment, when
considering what project-branch is involved, we will consider the name
of the project in the ``project`` stanza.  If the name is a regular
expression, then it will apply to all projects that match the regular
expression.  If the ``project`` stanza omits the ``branches``
attribute, then we will use the current branch if it appears in an
untrusted project.  If it appears in a config project, then it will
apply to all branches of the project.  If the ``branches`` attribute
is a regular expression, then it will apply to all branches of the
project that match the regular expression.  In other words, we will
follow the same procedure as outlined in :attr:`project.branches`.

Only the first queue assignment for a given project-branch combination
will be honored; subsequent appearances will be ignored.

The following example would assign `project1@legacy` to the `legacy` queue,
while all other branches of the project are assigned to the `general`
queue:

.. code-block:: yaml

   - queue:
       name: general

   - queue:
       name: legacy-queue
       type: branch-assigned

   - project:
       name: project1
       queue: general

   - project:
       name: project1
       branches: legacy
       queue: legacy-queue

Fine-Grained API/Web Access Control
===================================

.. warning:: This is not authoritative documentation.  These features
   are not currently available in Zuul.  They may change significantly
   before final implementation, or may never be fully completed.

The following document describes a proposed change to the access
control system of Zuul's REST API and web user interface.

Introduction
------------

Zuul was originally intended to have no user interface, instead only
interacting with users through the code-review system.  As the actions
that Zuul was able to perform increased in complexity, we developed a
read-only web interface in order to visualize what could not be
expressed through code-review reporting.  As it continued to increase
in complexity, we eventually created read-write endpoints in the API
in order to trigger certain administrative actions.

Today we find Zuul in a position where some of these actions have a
wide impact (such as pausing event processing for a tenant) while
others have a narrow impact (such as re-enqueing a buildset).

Zuul only has two scopes available for authorizing API or web access:
per-tenant read access, and per-tenant administrative access.  The
only scope available for write access is the administrative scope, so
all API actions are either allowed or disallowed for any particular
user or group.  For deployments where administrators would like to
delegate the ability to autohold nodes, or enqueue/dequeue items, this
is proving to be undesirable.

In order to allow admins to be able to dole out the minimal access
required for certain actions, let's add a role-based access control
system to the Zuul tenant configuration.

Proposal
--------

The existing tenant config file already has some modular components
for access control.  We create ``authorization-rule`` objects to
encapsulate a description attributes from an identity provider.  These
rules may then be attached to a tenant as either an ``admin-rule`` or
an ``access-rule`` in order to determine the access level for users
who match those rules.

We can introduce a new object, a ``role``, which specifies
fine-grained permissions (such as `autohold`, `enqueue`, and
`tenant-state`).  Roles may then be associated with tenants and
authorization-rules in order to specify the exact permissions
available to users who match a given authorization-rule in a given
tenant.

For convenience, we will define two built-in roles: ``admin`` which
will always have all permissions (even if more are added to Zuul in
the future), and ``read`` which will have only the permission
necessary for read-only access to the tenant.

Here is an example configuration:

.. code-block:: yaml

   - authorization-rule:
       name: admin-user
       conditions:
         - preferred_username: admin

   - authorization-rule:
       name: alice
       conditions:
         - preferred_username: alice

   - authorization-rule:
       name: everyone
       conditions:
         - iss: our-institution

   - role:
       name: autohold
       permissions:
         autohold: true

   - role:
       name: enqueue-post
       permissions:
         enqueue:
           conditions:
             pipeline: post
             project: foo

   - tenant:
       name: example
       anonymous-read-access: false
       role-mappings:
         admin-user: admin
         everyone: [read, autohold]
         alice: enqueue-post

This configuration describes the following:

* No anonymous access is allowed.
* Anyone who can authenticate is allowed read-access to the tenant,
  and the ability to place any autohold in the tenant.
* The "admin" user has full access.
* The user named "alice" may enqueue items for project "foo" into
  the "post" pipeline in that tenant.

The role mappings are a one-to-many mapping of ``authorization-rule``
to ``role``.

The roles themselves are generally a collection of permissions.  Some
permissions will be boolean (for example, setting the tenant-state to
pause event handling).  Others may have conditions added to them, so
that they only apply to certain pipelines, projects, etc.  These
conditions will vary based on the endpoint being protected.  Because
these objects are defined in the tenant config file, which is parsed
before the tenant layout is constructed, there will not be any
validation of these conditions at configuration time.  Only at
run-time will we perform string comparisons of project names or
pipeline names, etc.

To clarify: if there is an error in the tenant configuration at the
time the tenant configuration file is parsed, the tenant will not be
loaded (if it is a new tenant), or will not be updated and will run
with the previous configuration (if it is changed).  This is the
current behavior for any tenant configuration file syntax error.  If
there is an authorization rule that refers to a project or pipeline
that does not exist in the tenant, then that rule will simply not
match when it is applied at runtime, and access to the resulting
resource will fail with an authorization denied error.

Because the new role system covers all of the cases currently
supported by ``access-rule`` and ``admin-rule`` settings, we will
deprecate those settings and ask users to transition to using roles.
The built-in ``admin`` and ``read`` roles will make that easy for
users who want to make no other changes.  It will be an error to
specify ``role-mappings`` and either of the ``-rule`` settings on the
same tenant.

We currently automatically disable anonymous read access for a tenant
if any ``access-rule`` is listed on the tenant.  Due to the extra
layer of indirection, it would be dangerous to do the same with roles;
it would be difficult to audit whether anonymous read access is truly
disabled.  Therefore, we will introduce a new boolean flag,
``anonymous-read-access`` which defaults to ``true`` but can be set to
``false``.  This way, users may easily set the baseline behavior for
anonymous access, and then, if (and only if) ``anonymous-read-access``
is ``false``, then the ``read`` role permission will be used to
determine access.

The ``api-root`` object currently behaves similarly to tenants, except
that it has no ``admin-rule`` attribute, only ``access-rule``.
Everything in the preceding paragraph will apply to the ``api-root``
object as well -- it will simply not consult any permissions other
than ``read``.

This spec does not enumerate the permissions and conditions, but it is
expected that every zuul-web API endpoint that is currently protected
by `admin` access will have a unique permission, and that generally,
if those endpoints accept user input (such as project names), we will
try to make conditions available for them as well.  Any variances from
this can be discussed in the implementing changes.

Alternatives
------------

Because we are proposing the ability to add conditions to roles that
refer to the contents of the tenant layout (such as pipeline or
project names), it would make sense to define these role objects
within the tenants themselves.  However, that may produce both
technical and organizational problems.

From a technical standpoint, there is no object with which to
associate the roles.  Some of them could be attached to a pipeline
(for enqueue/dequeue).  Others, such as autohold, might simply be
global within the tenant.  That suggests that simply defining a role
would make it take effect in the tenant.  That could make it awkward
for sites to have a centralized repository with authorization
configuration.  Additionally, the existing ``authorization-rule``
objects are defined in the tenant config file, so we would need to
consider whether to move them into the layout.

From an organizational standpoint, much of this authorization
configuration deals with permissions that we may not want to grant to
users who manage tenant pipeline configurations.  Therefore, the idea
of moving this configuration into the layout so that it can be a part
of the layout configuration (especially pipelines) is contradicted by
the idea that we may not want to give authorization configuration
access to the people who manage pipelines.

Therefore, the proposal is to keep authorization managed centrally by
the Zuul administrators and have only a loose coupling with the
contents of the layouts via optional conditions for the permissions.

.. _flavor:

Flavor
======

A flavor is used by :ref:`provider` objects to configure the
characteristics of :ref:`build_nodes` related to the hardware (virtualized
or not) that they run on.  Clouds variously call this concept
`flavors`, `instance types`, `sizes`, etc.  Generally they embody
characteristics as machine architecture, RAM, storage, CPU, and
others.  By abstracting the concept in Zuul, users can express an
intention to run a job on a node with certain characteristics, and
differing flavor configurations in different providers can be used to
select the appropriate system from the cloud.

The standalone flavor configuration object itself is little more than
a name reservation.  It represents the idea of a particular flavor
separate from any implementation of that flavor in a provider, and
therefore there are very few configuration options below.  But once a
flavor is defined in Zuul, when that flavor is attached to a
:ref:`section`, the driver-specific options for flavors are available
and may be applied to it.  See the driver-specific provider options
for details.

For example, a user might decide to use a very small VM size for
launching build nodes.  They would then define a flavor object:

.. code-block:: yaml

   - flavor:
       name: small-vm
       description: A very small VM for running simple tests.

That expresses the idea of a `small-vm` flavor, but it doesn't
contain any of the necessary information to identify the flavor in a
cloud -- because that information depends on the provider.  A section
may then use that flavor like this:

.. code-block:: yaml

   - section:
       name: aws
       flavors:
         - name: small-vm
           instance-type: t3.small

This tells Zuul that to use the `small-vm` flavor on the `aws` cloud,
it should use the ``t3.small`` instance type.  The same flavor could
also be added to OpenStack or Azure clouds, with different attributes
for identification.

The attributes available to top-level flavor objects are:

.. attr:: flavor

   .. attr:: name
      :type: str
      :required:

      The name of the flavor.  Used to refer to the flavor in Zuul
      configuration.

   .. attr:: description
      :type: str

      A textual description of the flavor.

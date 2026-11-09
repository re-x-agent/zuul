:title: Static Driver

Static
======

Zuul can use statically defined nodes as a source for build nodes.
These can be real hardware or virtual machines that are managed
externally to Zuul.

To add static nodes to a provider in Zuul, use the
:attr:`provider[static].nodes` attribute.

Static nodes in Zuul have persistent node ids that are determined
based on their connection information.  This means the same node ID is
used for every build on a given static node.

.. warning:: There is no restriction that would prohibit users in
             multiple tenants from configuring the same static nodes.
             If static nodes should only be used by users of certain
             tenants, you may wish to configure the static node to
             only accept a :ref:`tenant-key` in order to restrict
             access.

Connection Configuration
------------------------

The connection configuration for the static driver is not used to
provide any settings or information to Zuul, but a connection is
nonetheless required in order to enable the functionality.

The only supported option in ``zuul.conf`` connections is:

.. attr:: <static connection>

   .. attr:: driver
      :required:

      .. value:: static

         The connection must set ``driver=static`` for a static connection.

Provider Configuration
----------------------

The ``static`` driver adds the following options to the :attr:`provider`
and :attr:`section` configurations:

.. include:: static-attrs.rstinc

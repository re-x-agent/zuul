:title: Azure Driver

Azure
=====

Zuul can use Azure as a source for build nodes.

Before using the Azure driver, make sure you have created a service
principal.

Two methods of authenticating the service principal are available: a
shared secret or OIDC federation.

To use a shared secret: save the credential information in a JSON
file.  Follow the instructions at `Azure CLI`_ and use the
``--sdk-auth`` flag::

  az ad sp create-for-rbac --name zuul --sdk-auth

There are two options for providing the information in this file to
Zuul: place this file on the zuul-launcher and refer to it using
:attr:`<azure connection>.shared_credentials_file` or extract the
information in the file and provide it directly with the configuration
options below.

To use OIDC federation, the JWT must be available in a file on the
zuul-launcher (for example, by way of Kubernetes secret
projection).  Set the
:attr:`<azure connection>.subscription_id`,
:attr:`<azure connection>.tenant_id`,
:attr:`<azure connection>.client_id`, and
:attr:`<azure connection>.federated_token_file` fields.

You must also have created a network for Zuul to use.  Be sure to
enable IPv6 on the network if you plan to use it.

The Azure driver uses the "Standard" SKU for all public IP addresses.
Standard IP addresses block all incoming traffic by default, therefore
the use of a Network Security Group is required in order to allow
incoming traffic.  You will need to create one, add any required
rules, and attach it to the subnet created above.

You may also need to register the `Microsoft.Compute` resource
provider with your subscription.

The ``azure`` driver adds the following options to the :attr:`provider`
and :attr:`section` configurations:

Connection Configuration
------------------------

The supported options in ``zuul.conf`` connections are:

.. attr:: <azure connection>

   .. attr:: driver
      :required:

      .. value:: azure

         The connection must set ``driver=azure`` for Azure connections.

   .. attr:: shared_credentials_file

      A path to JSON file with shared access credentials.  If this is
      supplied, no other credential settings need to be present.

   .. attr:: federated_token_file

      Path to the a file containing a JWT for use with OIDC
      federation.

   .. attr:: tenant_id

      The Microsoft Entra tenant ID for the account.  Required unless
      :attr:`<azure connection>.shared_credentials_file` is set.

   .. attr:: client_id

      The Microsoft Entra client ID for the account.  Required unless
      :attr:`<azure connection>.shared_credentials_file` is set.

   .. attr:: client_secret

      The shared secret for the principal.  Required unless
      :attr:`<azure connection>.shared_credentials_file` or
      :attr:`<azure connection>.federated_token_file` are set.

   .. attr:: subscription_id

      The Azure subscription to use.  Required unless
      :attr:`<azure connection>.shared_credentials_file` is set.

   .. attr:: rate
      :default: 2

      The API rate limit (in requests per second) to use when
      performing API calls with Azure.

Provider Configuration
----------------------

The ``azure`` driver adds the following options to the :attr:`provider`
and :attr:`section` configurations:

.. include:: azure-attrs.rstinc

.. _`Azure CLI`: https://docs.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli?view=azure-cli-latest

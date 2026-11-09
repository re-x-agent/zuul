# Copyright 2024 BMW Group
# Copyright 2024-2025 Acme Gating, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from zuul import model
from zuul.provider import statemachine


class StaticProviderNode(model.ProviderNode, subclass_id="static"):
    pass


class StaticInstance(statemachine.Instance):
    def __init__(self, node_config, quota):
        super().__init__()
        self.quota = quota
        self.metadata = {}
        self.private_ipv4 = None
        self.private_ipv6 = None
        self.public_ipv4 = None
        self.public_ipv6 = None
        self.cloud = None
        self.interface_ip = node_config.name

    @property
    def external_id(self):
        return self.interface_ip

    def getQuotaInformation(self):
        return self.quota

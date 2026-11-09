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


class SubnodeProviderNode(model.ProviderNode, subclass_id="subnode"):
    SUBNODE_ATTRIBUTES = (
        'uuid',
        'slot',
    )

    def __repr__(self):
        # Override the repr method to include the main node id
        return (f"<{self.__class__.__name__} uuid={self.uuid},"
                f" label={self.label}, state={self.state},"
                f" main_node={self.main_node_id}>")

    def updateFromMainNode(self, node):
        # Once the main node is finished creating, this is called to
        # synchronize any attributes that should be copied to the
        # subnode.
        # Called with an active context
        for k, v in node.getNodeData(serialize_node=True).items():
            if k in self.SUBNODE_ATTRIBUTES:
                continue
            setattr(self, k, v)


class SubnodeStateMachine(statemachine.StateMachine):
    """A no-op state machine since subnodes don't need to be created
    or deleted.

    """
    COMPLETE = 'complete'

    def __init__(self):
        super().__init__({})
        self.state = self.COMPLETE
        self.complete = True

    def advance(self):
        pass

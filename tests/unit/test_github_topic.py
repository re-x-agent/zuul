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

from zuul.zk.change_cache import ChangeKey
from tests.base import ZuulTestCase, simple_layout


class TestGithubTopicLabels(ZuulTestCase):
    """Topic dependencies derived from GitHub labels"""
    config_file = 'zuul-github-driver.conf'
    scheduler_count = 1

    topic_label_prefix = 'topic:'

    def setup_config(self, config_file):
        config = super().setup_config(config_file)
        if self.topic_label_prefix:
            config.set('connection github', 'topic_label_prefix',
                       self.topic_label_prefix)
        return config

    def _pr(self, project, name, labels=(), body=None):
        pr = self.fake_github.openFakePullRequest(
            project, 'master', name, body=body)
        for label in labels:
            pr.addLabel(label)
        return pr

    def _connection(self):
        return self.scheds.first.connections.connections['github']

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_from_labels(self):
        conn = self._connection()
        self.assertEqual('foo', conn.getTopicFromLabels(['topic:foo']))
        self.assertEqual('foo', conn.getTopicFromLabels(['bug', 'topic:foo']))
        # The prefix matches case-insensitively, the topic keeps its
        # spelling.
        self.assertEqual('Foo', conn.getTopicFromLabels(['Topic:Foo']))
        self.assertIsNone(conn.getTopicFromLabels([]))
        self.assertIsNone(conn.getTopicFromLabels(['bug', 'topical']))
        # A prefix without a name is not a topic.
        self.assertIsNone(conn.getTopicFromLabels(['topic:']))
        # Several topics: one is picked, deterministically.
        self.assertEqual(
            'a', conn.getTopicFromLabels(['topic:b', 'topic:a']))
        self.assertTrue(conn.isTopicLabel('topic:foo'))
        self.assertFalse(conn.isTopicLabel('bug'))

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_gate(self):
        "Pull requests with the same topic label are gated together"
        A = self._pr('org/project1', 'A', ['topic:t1'])
        B = self._pr('org/project2', 'B', ['topic:t1'])

        self.fake_github.emitEvent(A.getPullRequestEditedEvent())
        self.waitUntilSettled()

        self.assertTrue(A.is_merged)
        self.assertTrue(B.is_merged)
        self.assertEqual(2, len(self.history))
        # Both jobs tested the same speculative state.
        for job in self.history:
            self.assertIn(str(A.number) + ',' + A.head_sha, job.changes)
            self.assertIn(str(B.number) + ',' + B.head_sha, job.changes)

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_case_insensitive(self):
        "The topic label is matched case-insensitively"
        A = self._pr('org/project1', 'A', ['topic:T1'])
        B = self._pr('org/project2', 'B', ['Topic:t1'])

        self.fake_github.emitEvent(A.getPullRequestEditedEvent())
        self.waitUntilSettled()

        self.assertTrue(A.is_merged)
        self.assertTrue(B.is_merged)

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_different_topics(self):
        "Pull requests with different topics are not combined"
        A = self._pr('org/project1', 'A', ['topic:t1'])
        B = self._pr('org/project2', 'B', ['topic:t2'])

        self.fake_github.emitEvent(A.getPullRequestEditedEvent())
        self.waitUntilSettled()

        self.assertTrue(A.is_merged)
        self.assertFalse(B.is_merged)
        self.assertEqual(1, len(self.history))
        self.assertEqual('%s,%s' % (A.number, A.head_sha),
                         self.history[0].changes)

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_no_label(self):
        "Pull requests without a topic label are not combined"
        A = self._pr('org/project1', 'A', ['bug'])
        B = self._pr('org/project2', 'B', ['bug'])

        self.fake_github.emitEvent(A.getPullRequestEditedEvent())
        self.waitUntilSettled()

        self.assertTrue(A.is_merged)
        self.assertFalse(B.is_merged)
        self.assertEqual(1, len(self.history))

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_closed_not_combined(self):
        "Closed pull requests are not part of the topic"
        A = self._pr('org/project1', 'A', ['topic:t1'])
        B = self._pr('org/project2', 'B', ['topic:t1'])
        B.state = 'closed'

        self.fake_github.emitEvent(A.getPullRequestEditedEvent())
        self.waitUntilSettled()

        self.assertTrue(A.is_merged)
        self.assertFalse(B.is_merged)
        self.assertEqual(1, len(self.history))

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_and_depends_on(self):
        "Topic and Depends-On dependencies are combined"
        C = self._pr('org/project3', 'C')
        msg = 'Depends-On: https://github.com/org/project3/pull/%s' % C.number
        A = self._pr('org/project1', 'A', ['topic:t1'], body=msg)
        B = self._pr('org/project2', 'B', ['topic:t1'])

        self.fake_github.emitEvent(B.getPullRequestEditedEvent())
        self.waitUntilSettled()

        self.assertTrue(A.is_merged)
        self.assertTrue(B.is_merged)
        self.assertTrue(C.is_merged)
        self.assertEqual(3, len(self.history))

    def _gate_items(self):
        tenant = self.scheds.first.sched.abide.tenants.get('tenant-one')
        gate = tenant.layout.pipeline_managers['gate']
        return [i for q in gate.state.queues for i in q.queue]

    def _topic_needs(self, change):
        # Re-read the change from the cache; the scheduler stores
        # dependency updates there.
        change = self._connection().getChange(
            ChangeKey.fromReference(change.cache_key))
        return [k for k in (change.topic_needs_changes or [])]

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_label_added_to_queued(self):
        "Adding a topic label to a pull request updates queued peers"
        self.executor_server.hold_jobs_in_build = True
        A = self._pr('org/project1', 'A', ['topic:t1'])
        B = self._pr('org/project2', 'B')

        self.fake_github.emitEvent(A.getPullRequestEditedEvent())
        self.waitUntilSettled()

        items = self._gate_items()
        self.assertEqual(1, len(items))
        self.assertEqual(1, len(items[0].changes))
        a_change = items[0].changes[0]
        self.assertEqual([], self._topic_needs(a_change))

        # B joins the topic.  Only the label event is sent, so queued
        # A can only find out through the label event.
        self.fake_github.emitEvent(B.addLabel('topic:t1'))
        self.waitUntilSettled()

        needs = self._topic_needs(a_change)
        self.assertEqual(1, len(needs))
        self.assertEqual('org/project2',
                         ChangeKey.fromReference(needs[0]).project_name)

        self.executor_server.hold_jobs_in_build = False
        self.executor_server.release()
        self.waitUntilSettled()

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_label_removed_from_queued(self):
        "Removing a topic label from a pull request updates queued peers"
        self.executor_server.hold_jobs_in_build = True
        A = self._pr('org/project1', 'A', ['topic:t1'])
        B = self._pr('org/project2', 'B', ['topic:t1'])

        self.fake_github.emitEvent(A.getPullRequestEditedEvent())
        self.waitUntilSettled()

        items = self._gate_items()
        self.assertEqual(1, len(items))
        self.assertEqual(2, len(items[0].changes))
        a_change = [c for c in items[0].changes if c.number == str(A.number)
                    or c.number == A.number][0]
        self.assertEqual(1, len(self._topic_needs(a_change)))

        self.fake_github.emitEvent(B.removeLabel('topic:t1'))
        self.waitUntilSettled()

        self.assertEqual([], self._topic_needs(a_change))

        self.executor_server.hold_jobs_in_build = False
        self.executor_server.release()
        self.waitUntilSettled()


class TestGithubTopicLabelsDisabled(TestGithubTopicLabels):
    "Without topic_label_prefix, topic labels have no effect"
    topic_label_prefix = None

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_from_labels(self):
        conn = self._connection()
        self.assertIsNone(conn.getTopicFromLabels(['topic:foo']))
        self.assertFalse(conn.isTopicLabel('topic:foo'))

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_disabled(self):
        A = self._pr('org/project1', 'A', ['topic:t1'])
        B = self._pr('org/project2', 'B', ['topic:t1'])

        self.fake_github.emitEvent(A.getPullRequestEditedEvent())
        self.waitUntilSettled()

        self.assertTrue(A.is_merged)
        self.assertFalse(B.is_merged)
        self.assertEqual(1, len(self.history))

    # The remaining tests of the parent class describe the enabled
    # behavior.
    test_topic_gate = None
    test_topic_case_insensitive = None
    test_topic_different_topics = None
    test_topic_no_label = None
    test_topic_closed_not_combined = None
    test_topic_and_depends_on = None
    test_topic_label_added_to_queued = None
    test_topic_label_removed_from_queued = None

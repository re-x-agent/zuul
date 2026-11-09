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

import re
from unittest import mock

from tests import fakegithub
from zuul.driver.github.githubconnection import GithubConnection
from zuul.model import Project
from zuul.zk.change_cache import ChangeKey
from tests.base import ZuulGithubAppTestCase, simple_layout


class TestGithubTopicLabels(ZuulGithubAppTestCase):
    """Topic dependencies derived from GitHub labels"""
    config_file = 'zuul-github-driver.conf'
    scheduler_count = 1

    topic_label_marker = 'topic:'

    def setup_config(self, config_file):
        config = super().setup_config(config_file)
        if self.topic_label_marker:
            config.set('connection github', 'topic_label_marker',
                       self.topic_label_marker)
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
        # The marker matches case-insensitively, the topic keeps its
        # spelling.
        self.assertEqual('Foo', conn.getTopicFromLabels(['Topic:Foo']))
        self.assertIsNone(conn.getTopicFromLabels([]))
        self.assertIsNone(conn.getTopicFromLabels(['bug', 'topical']))
        # A marker without a name is not a topic.
        self.assertIsNone(conn.getTopicFromLabels(['topic:']))
        # Several topics: one is picked, deterministically.
        self.assertEqual(
            'a', conn.getTopicFromLabels(['topic:b', 'topic:a']))
        self.assertTrue(conn.isTopicLabel('topic:foo'))
        # The value is everything after the marker: a value may contain
        # the separator.
        self.assertEqual('a:b', conn.getTopicFromLabels(['topic:a:b']))
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
    def test_topic_exact_match_not_prefix(self):
        "Topic 1 and topic 11 are different topics (exact match only)"
        A = self._pr('org/project1', 'A', ['topic:1'])
        B = self._pr('org/project2', 'B', ['topic:11'])
        C = self._pr('org/project3', 'C', ['topic:1'])
        conn = self._connection()

        def numbers(topic):
            return sorted(c.number for c in conn.getChangesByTopic(topic))

        self.assertEqual(sorted([A.number, C.number]), numbers('1'))
        self.assertEqual([B.number], numbers('11'))

        self.fake_github.emitEvent(A.getPullRequestEditedEvent())
        self.waitUntilSettled()

        self.assertTrue(A.is_merged)
        self.assertTrue(C.is_merged)
        self.assertFalse(B.is_merged)
        for job in self.history:
            self.assertNotIn(
                str(B.number) + ',' + B.head_sha, job.changes)

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_exact_match_loose_search(self):
        "Results of a looser search are filtered to the exact topic"
        A = self._pr('org/project1', 'A', ['topic:1'])
        B = self._pr('org/project2', 'B', ['topic:11'])
        D = self._pr('org/project3', 'D', ['topic:1', 'topic:11'])
        conn = self._connection()

        # Simulate a search that also returns labels merely starting
        # with the requested one.
        def loose_search(client, query):
            label = query.split('label:"')[1].split('"')[0].lower()
            return iter([
                fakegithub.FakeIssueSearchResult(fakegithub.FakeIssue(pr))
                for pr in client._data.pull_requests.values()
                if pr.state == 'open' and
                any(x.lower().startswith(label) for x in pr.labels)])

        with mock.patch.object(fakegithub.FakeGithubClient,
                               'search_issues', loose_search):
            # D has two topic labels; its single topic is the
            # smallest one, "1".
            self.assertEqual(
                sorted([A.number, D.number]),
                sorted(c.number for c in conn.getChangesByTopic('1')))
            self.assertEqual(
                [B.number],
                sorted(c.number for c in conn.getChangesByTopic('11')))

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_value_with_separator(self):
        "A label value may contain the separator; it is matched whole"
        A = self._pr('org/project1', 'A', ['topic:a:b'])
        B = self._pr('org/project2', 'B', ['topic:a:b'])
        C = self._pr('org/project3', 'C', ['topic:a'])
        conn = self._connection()

        def numbers(topic):
            return sorted(c.number for c in conn.getChangesByTopic(topic))

        # topic:a:b has the value "a:b" and pairs with itself ...
        self.assertEqual(sorted([A.number, B.number]), numbers('a:b'))
        # ... but not with topic:a (exact match of the value).
        self.assertEqual([C.number], numbers('a'))

        self.fake_github.emitEvent(A.getPullRequestEditedEvent())
        self.waitUntilSettled()

        self.assertTrue(A.is_merged)
        self.assertTrue(B.is_merged)
        self.assertFalse(C.is_merged)
        for job in self.history:
            self.assertNotIn(
                str(C.number) + ',' + C.head_sha, job.changes)

    def _recordSearches(self):
        """Record the search queries and the installation of the client"""
        queries = []
        original = fakegithub.FakeGithubClient.search_issues

        def recording(client, query):
            queries.append((client._inst_id, query))
            return original(client, query)

        patcher = mock.patch.object(
            fakegithub.FakeGithubClient, 'search_issues', recording)
        patcher.start()
        self.addCleanup(patcher.stop)
        return queries

    def _addProject(self, name):
        """Configure a project of another owner and install the App there"""
        conn = self._connection()
        owner, project = name.split('/')
        # Only the names are used to prime the installation map.
        repos = self.fake_github.github_data.repos
        repos[(owner, project)] = mock.Mock()
        self.addCleanup(repos.pop, (owner, project), None)
        conn.projects[name] = Project(name, conn.source)
        self.addCleanup(conn.projects.pop, name, None)
        conn._github_client_manager._prime_installation_map()

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_search_per_installation(self):
        "One search per installation, listing only its configured projects"
        self._addProject('org2/projectx')
        conn = self._connection()
        A = self._pr('org/project1', 'A', ['topic:t1'])
        inst = conn._github_client_manager.installation_map
        self.assertNotEqual(inst['org/project1'], inst['org2/projectx'])
        queries = self._recordSearches()

        numbers = sorted(c.number for c in conn.getChangesByTopic('t1'))

        self.assertEqual([A.number], numbers)
        by_inst = {i: q for i, q in queries}
        self.assertEqual(2, len(queries))
        # Each query lists the configured projects of one installation.
        org_repos = {n for n in conn.projects if n.startswith('org/')}
        q1 = by_inst[inst['org/project1']]
        self.assertEqual(set(re.findall(r'repo:(\S+)', q1)), org_repos)
        self.assertEqual(
            by_inst[inst['org2/projectx']],
            'type:pr is:open label:"topic:t1" repo:org2/projectx')
        self.assertNotIn('org:', q1)

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_search_chunks(self):
        "More repositories than the limit are split into several queries"
        conn = self._connection()
        self.assertLessEqual(GithubConnection.TOPIC_SEARCH_MAX_REPOS, 21)
        names = sorted(conn.projects.keys())
        self.assertGreater(len(names), 2)
        A = self._pr('org/project1', 'A', ['topic:t1'])
        B = self._pr('org/project2', 'B', ['topic:t1'])
        queries = self._recordSearches()

        with mock.patch.object(GithubConnection,
                               'TOPIC_SEARCH_MAX_REPOS', 2):
            numbers = sorted(c.number for c in conn.getChangesByTopic('t1'))

        self.assertEqual(sorted([A.number, B.number]), numbers)
        repos = [re.findall(r'repo:(\S+)', q) for _, q in queries]
        self.assertEqual(-(-len(names) // 2), len(queries))
        self.assertTrue(all(len(r) <= 2 for r in repos))
        # Every configured project is searched exactly once.
        self.assertEqual(names, sorted(r for rs in repos for r in rs))

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_search_not_installed(self):
        "A configured project without the App is logged and not searched"
        conn = self._connection()
        manager = conn._github_client_manager
        A = self._pr('org/project1', 'A', ['topic:t1'])
        C = self._pr('org/project3', 'C', ['topic:t1'])
        queries = self._recordSearches()
        # Pretend the App is not installed in project3.
        manager.installation_map.pop('org/project3')

        with self.assertLogs('zuul', 'WARNING') as logs:
            numbers = sorted(c.number for c in conn.getChangesByTopic('t1'))

        self.assertIn('org/project3', '\n'.join(logs.output))
        self.assertEqual([A.number], numbers)
        self.assertNotIn(C.number, numbers)
        self.assertNotIn('org/project3', ' '.join(q for _, q in queries))

    @simple_layout('layouts/github-topic-deps.yaml', driver='github')
    def test_topic_api_token_mode(self):
        "Topics need the GitHub App: with an api_token no set is built"
        conn = self._connection()
        manager = conn._github_client_manager
        A = self._pr('org/project1', 'A', ['topic:t1'])
        B = self._pr('org/project2', 'B', ['topic:t1'])
        queries = self._recordSearches()

        with mock.patch.object(manager, 'app_id', None):
            with self.assertLogs('zuul', 'WARNING') as logs:
                self.assertEqual([], conn.getChangesByTopic('t1'))
            self.assertIn('GitHub App', '\n'.join(logs.output))
            self.assertEqual([], queries)

            # The dependency resolution goes on as usual, without a set.
            self.fake_github.emitEvent(A.getPullRequestEditedEvent())
            self.waitUntilSettled()

        self.assertTrue(A.is_merged)
        self.assertFalse(B.is_merged)
        self.assertEqual(1, len(self.history))

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
    "Without topic_label_marker, topic labels have no effect"
    topic_label_marker = None

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
    test_topic_exact_match_not_prefix = None
    test_topic_exact_match_loose_search = None
    test_topic_search_per_installation = None
    test_topic_search_chunks = None
    test_topic_search_not_installed = None
    test_topic_api_token_mode = None
    test_topic_value_with_separator = None
    test_topic_different_topics = None
    test_topic_no_label = None
    test_topic_closed_not_combined = None
    test_topic_and_depends_on = None
    test_topic_label_added_to_queued = None
    test_topic_label_removed_from_queued = None

# Copyright 2018 Red Hat, Inc
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
"""Hook for pbr to build javascript as part of tarball."""

import os
import subprocess


def _build_javascript():
    if subprocess.call(['which', 'yarn']) != 0:
        return
    if not os.path.exists('web/node_modules/.bin/webpack'):
        r = subprocess.Popen(['yarn', 'install',
                              '--frozen-lockfile'], cwd="web/").wait()
        if r:
            raise RuntimeError("Yarn install failed")
    r = subprocess.Popen(['yarn', 'list'], cwd="web/").wait()
    if r:
        raise RuntimeError("Yarn list failed")
    if not os.path.exists('zuul/web/static/index.html'):
        os.makedirs('zuul/web/static', exist_ok=True)
        if not os.path.islink('../zuul/web/static'):
            os.symlink('../zuul/web/static', 'web/dist',
                       target_is_directory=True)
        r = subprocess.Popen(['yarn', 'build'], cwd="web/").wait()
        if r:
            raise RuntimeError("Yarn build failed")


def setup_hook(config):
    _build_javascript()

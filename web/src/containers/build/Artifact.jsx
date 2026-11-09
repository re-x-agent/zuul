// Copyright 2019 Red Hat, Inc
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

import React from 'react'
import PropTypes from 'prop-types'
import {
  TreeView,
} from '@patternfly/react-core'
import {
  TableComposable,
  Tbody,
  Thead,
  Tr,
  Td,
} from '@patternfly/react-table'
import { JSONTree } from 'react-json-tree'
import { connect } from 'react-redux'

class Artifact extends React.Component {
  static propTypes = {
    artifact: PropTypes.object.isRequired,
    preferences: PropTypes.object,
  }

  render() {
    const { artifact, preferences } = this.props
    return (
      <TableComposable>
        <Thead>
          <Tr></Tr>
        </Thead>
        <Tbody>
          {Object.keys(artifact.metadata).map(key => (
            <Tr key={key}>
              <Td>{key}</Td>
              <Td>
                {typeof(artifact.metadata[key]) === 'object'?
                 <JSONTree
                   data={artifact.metadata[key]}
                   hideRoot={true}
                   sortObjectKeys={true}
                   theme="default"
                   invertTheme={!preferences.darkMode}/>
                 :artifact.metadata[key].toString()}
              </Td>
            </Tr>
          ))}
        </Tbody>
      </TableComposable>
    )
  }
}

class ArtifactList extends React.Component {
  static propTypes = {
    artifacts: PropTypes.array.isRequired,
    preferences: PropTypes.object,
  }

  render() {
    const { artifacts, preferences } = this.props

    const nodes = artifacts.map((artifact, index) => {
      const node = {id: index, name: <a href={artifact.url}>{artifact.name}</a>}
      if (artifact.metadata) {
        node['children']= [{id: index, name: <Artifact artifact={artifact} preferences={preferences}/>}]
      }
      return node
    })

    return (
      <>
        <br/>
        <div className="tree-view-container">
          <TreeView data={nodes} />
        </div>
      </>
    )
  }
}

function mapStateToProps(state) {
  return {
    preferences: state.preferences,
  }
}

export default connect(mapStateToProps)(ArtifactList)

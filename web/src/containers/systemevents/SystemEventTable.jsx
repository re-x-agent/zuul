// Copyright 2020 BMW Group
// Copyright 2023,2025 Acme Gating, LLC
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
import { useSelector } from 'react-redux'
import PropTypes from 'prop-types'
import {
  EmptyState,
  EmptyStateBody,
  EmptyStateIcon,
  Spinner,
  Title,
} from '@patternfly/react-core'
import {
  InfoCircleIcon,
  FlagIcon,
  OutlinedCalendarAltIcon,
} from '@patternfly/react-icons'
import {
  Table,
  TableHeader,
  TableBody,
  TableVariant,
  nowrap,
} from '@patternfly/react-table'
import moment_tz from 'moment-timezone'

import { IconProperty } from '../../MiscComponents'

function SystemEventTable({
  events,
  fetching,
}) {
  const timezone = useSelector((state) => state.timezone)

  const columns = [
    {
      title: <IconProperty icon={<OutlinedCalendarAltIcon />} value="Time" />,
      dataLabel: 'Time',
      cellTransforms: [nowrap],
    },
    {
      title: <IconProperty icon={<FlagIcon />} value="Description" />,
      dataLabel: 'Description',
    },
  ]

  function createSystemEventRow(rows, event) {
    return {
      id: rows.length,
      cells: [
        {
          title: moment_tz
            .utc(event.event_time)
            .tz(timezone)
            .format('YYYY-MM-DD HH:mm:ss')
        },
        {
          title: event.description,
        },
      ],
    }
  }

  function createFetchingRow() {
    const rows = [
      {
        heightAuto: true,
        cells: [
          {
            props: { colSpan: 2 },
            title: (
              <center>
                <Spinner size="xl" />
              </center>
            ),
          },
        ],
      },
    ]
    return rows
  }

  let rows = []
  if (fetching) {
    rows = createFetchingRow()
    // The dataLabel property is used to show the column header in a list-like
    // format for smaller viewports. When we are fetching, we don't want the
    // fetching row to be prepended by a "Job" column header. The other column
    // headers are not relevant here since we only have a single cell in the
    // fetcihng row.
    columns[0].dataLabel = ''
  } else {
    rows = []
    events.forEach(event => {
      rows.push(createSystemEventRow(rows, event))
    })
  }

  return (
    <>
      <Table
        aria-label="Config Events Table"
        variant={TableVariant.compact}
        cells={columns}
        rows={rows}
      >
        <TableHeader />
        <TableBody />
      </Table>

      {/* Show an empty state in case we don't have any events but are also not
          fetching */}
      {!fetching && events.length === 0 && (
        <EmptyState>
          <EmptyStateIcon icon={InfoCircleIcon} />
          <Title headingLevel="h1">No events found</Title>
          <EmptyStateBody>
            No events found.
          </EmptyStateBody>
        </EmptyState>
      )}
    </>
  )
}

SystemEventTable.propTypes = {
  events: PropTypes.array.isRequired,
  fetching: PropTypes.bool.isRequired,
}

export default SystemEventTable

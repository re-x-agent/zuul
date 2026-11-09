// Copyright 2018 Red Hat, Inc
// Copyright 2020 BMW Group
// Copyright 2024 Acme Gating, LLC
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

import { React } from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'

import {
  Label,
  Progress,
  ProgressMeasureLocation,
  ProgressVariant,
  Tooltip,
} from '@patternfly/react-core'
import {
  BundleIcon,
  CodeBranchIcon,
  FlaskIcon,
  SortAmountDownIcon,
  StreamIcon,
} from '@patternfly/react-icons'

import {
  getChangeLabel,
  getJobResultIconConfig,
  getJobStrResult,
} from './Misc'

import { formatTime } from '../../Misc'
import { ExternalLink } from '../../MiscComponents'

/*
  Note: the documentation links are unused at the moment, but kept for
  convenience. We might figure a way to use these at some point.
*/
const PIPELINE_ICON_CONFIGS = {
  dependent: {
    icon: CodeBranchIcon,
    help_title: 'Dependent Pipeline',
    help: 'A dependent pipeline ensures that every change is tested exactly in the order it is going to be merged into the repository.',
    doc_url: 'https://zuul-ci.org/docs/zuul/reference/pipeline_def.html#value-pipeline.manager.dependent',
  },
  independent: {
    icon: FlaskIcon,
    help_title: 'Independent Pipeline',
    help: 'An independent pipeline treats every change as independent of other changes in it.',
    doc_url: 'https://zuul-ci.org/docs/zuul/reference/pipeline_def.html#value-pipeline.manager.independent',
  },
  serial: {
    icon: SortAmountDownIcon,
    help_title: 'Serial Pipeline',
    help: 'A serial pipeline supports shared queues, but only one item in each shared queue is processed at a time.',
    doc_url: 'https://zuul-ci.org/docs/zuul/reference/pipeline_def.html#value-pipeline.manager.serial',
  },
  supercedent: {
    icon: BundleIcon,
    help_title: 'Supercedent Pipeline',
    help: 'A supercedent pipeline groups items by project and ref, and processes only one item per grouping at a time. Only two items (currently processing and latest) can be queued per grouping.',
    doc_url: 'https://zuul-ci.org/docs/zuul/reference/pipeline_def.html#value-pipeline.manager.supercedent',
  },
  unknown: {
    icon: StreamIcon,
    help_title: '?',
    help: 'Unknown pipeline type',
    doc_url: 'https://zuul-ci.org/docs/zuul/reference/pipeline_def.html'
  },
}

const DEFAULT_PIPELINE_ICON_CONFIG = PIPELINE_ICON_CONFIGS['unknown']

function PipelineIcon({ pipelineType, size = 'sm' }) {
  const iconConfig = PIPELINE_ICON_CONFIGS[pipelineType] || DEFAULT_PIPELINE_ICON_CONFIG
  const Icon = iconConfig.icon

  // Define the verticalAlign based on the size
  let verticalAlign = '-0.2em'

  if (size === 'md') {
    verticalAlign = '-0.35em'
  }

  return (
    <Icon
      size={size}
      style={{
        marginRight: 'var(--pf-global--spacer--sm)',
        verticalAlign: verticalAlign,
      }}
    />
  )
}

PipelineIcon.propTypes = {
  pipelineType: PropTypes.string,
  size: PropTypes.string,
}

function ChangeLink({ change }) {
  const label = getChangeLabel(change)
  return (
    <ExternalLink target={change.url}>
      {label}
    </ExternalLink>
  )
}

ChangeLink.propTypes = {
  change: PropTypes.object,
}

function QueueItemProgressbar({ item }) {
  const interesting_jobs = item.jobs.filter(j => getJobStrResult(j) !== 'skipped')
  let jobPercent = (100 / interesting_jobs.length).toFixed(2)

  return (
    <div style={{ textWrap: 'nowrap' }}>
      {interesting_jobs.map((job, idx) => {
        const iconConfig = getJobResultIconConfig(job)
        return (
          <Tooltip
            key={`${job.name}-${job.uuid}-${idx}`}
            content={job.name}
          >
            <Progress
              aria-label={`${job.name}-progress`}
              className="zuul-item-progress"
              value={100}
              measureLocation={ProgressMeasureLocation.none}
              variant={iconConfig.variant}
              style={{ width: jobPercent + '%', display: 'inline-block' }}
            />
          </Tooltip>
        )
      })}
    </div>
  )
}

QueueItemProgressbar.propTypes = {
  item: PropTypes.object,
  darkMode: PropTypes.bool,
}

function JobProgressBar({ job, elapsedTime, remainingTime }) {
  let progressPercent = 100 * (elapsedTime / (elapsedTime + remainingTime))
  const remainingTimeStr = formatTime(remainingTime)

  if (Number.isNaN(progressPercent)) {
    progressPercent = 0
  }

  const progressBar = (
    <Progress
      aria-label={`${job.name}-progress`}
      className={progressPercent === 0 ? 'zuul-progress-animated' : 'zuul-progress'}
      variant={job.pre_fail ? ProgressVariant.danger : ''}
      value={progressPercent}
      measureLocation={ProgressMeasureLocation.none}
    />
  )

  if (progressPercent === 0) {
    return progressBar
  }
  return (
    <Tooltip content={`Estimated remaining time: ${remainingTimeStr}`} position="right">
      {progressBar}
    </Tooltip>
  )
}

JobProgressBar.propTypes = {
  job: PropTypes.object,
  elapsedTime: PropTypes.number,
  remainingTime: PropTypes.number,
}

function JobStatusLabel({ job, result }) {
  const iconConfig = getJobResultIconConfig(job)

  const label = (
    <Label className="zuul-job-result-label" color={iconConfig.labelColor}>
      {result}
    </Label>
  )

  if (['waiting', 'queued'].includes(result) && job.waiting_status !== null) {
    return (
      // Wrap the result label in a Tooltip to show the waiting status
      <Tooltip
        position="right"
        content={`Waiting on ${job.waiting_status}`}
      >
        {label}
      </Tooltip>
    )
  }

  // If there is no waiting status, just show the label
  return label
}

JobStatusLabel.propTypes = {
  job: PropTypes.object,
  result: PropTypes.string,
}

function JobLink({ job, tenant }) {
  // Format job name with retries
  let job_name = job.name
  let ordinal_rules = new Intl.PluralRules('en', { type: 'ordinal' })
  const suffixes = {
    one: 'st',
    two: 'nd',
    few: 'rd',
    other: 'th',
  }
  if (job.tries > 1) {
    job_name = job_name + ' (' + job.tries + suffixes[ordinal_rules.select(job.tries)] + ' attempt)'
  }

  let name = ''
  if (job.result !== null) {
    name = <a className='zuul-job-name' href={job.report_url}>{job_name}</a>
  } else if (job.url !== null) {
    let url = job.url
    if (job.url.match('stream/')) {
      const to = (
        tenant.linkPrefix + '/' + job.url
      )
      name = <Link className='zuul-job-name' to={to}>{job_name}</Link>
    } else {
      name = <a className='zuul-job-name' href={url}>{job_name}</a>
    }
  } else {
    name = <span className='zuul-job-name'>{job_name}</span>
  }

  return (
    <span>
      {name}
      {job.voting === false
        ? <small className='zuul-non-voting-desc'> (non-voting)</small>
        : ''
      }
    </span>
  )
}

JobLink.propTypes = {
  job: PropTypes.object,
  tenant: PropTypes.object,
}

function JobResultOrStatus({ job, job_times }) {
  let result = getJobStrResult(job)
  if (result === 'in progress') {
    return <JobProgressBar job={job} elapsedTime={job_times.elapsed} remainingTime={job_times.remaining} />
  }

  return <JobStatusLabel job={job} result={result} />
}

JobResultOrStatus.propTypes = {
  job: PropTypes.object,
  job_times: PropTypes.object,
}

export {
  ChangeLink,
  JobLink,
  JobResultOrStatus,
  QueueItemProgressbar,
  PipelineIcon,
}

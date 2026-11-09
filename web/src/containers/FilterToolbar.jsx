// Copyright 2020 BMW Group
// Copyright 2025 Acme Gating, LLC
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

function getFiltersFromUrl(location, filterCategories) {
  const urlParams = new URLSearchParams(location.search)
  const _filters = filterCategories.reduce((filterDict, item) => {
    // Initialize each filter category with an empty list
    filterDict[item.key] = []

    // And update the list with each matching element from the URL query
    urlParams.getAll(item.key).forEach((param) => {
      if (item.type === 'checkbox') {
        switch (param) {
          case '1':
            filterDict[item.key].push(1)
            break
          case '0':
            filterDict[item.key].push(0)
            break
          default:
            break
        }
      } else {
        filterDict[item.key].push(param)
      }
    })
    return filterDict
  }, {})
  const pagination_options = {
    skip: urlParams.getAll('skip') ? urlParams.getAll('skip') : [0,],
    limit: urlParams.getAll('limit') ? urlParams.getAll('limit') : [50,],
  }
  const filters = { ..._filters, ...pagination_options }
  return filters
}

function writeFiltersToUrl(filters, filterCategories, location, history) {
  // Build new URL parameters from the filters in state
  const searchParams = new URLSearchParams(location.search)

  // first clear existing searchParams contained in the current valid
  // filterCategories or "skip"/"limit". This is to make sure we don't remove
  // other unrelated searchParams
  const keys = filterCategories.map(c => c.key).concat(['skip', 'limit'])
  for (const key of keys) {
    searchParams.delete(key)
  }

  Object.keys(filters).map((key) => {
    filters[key].forEach((value) => {
      searchParams.append(key, value)
    })
    return searchParams
  })
  history.push({
    pathname: location.pathname,
    search: searchParams.toString(),
  })
}

function makeQueryString(filters) {
  let queryString = ''
  if (filters) {
    Object.keys(filters).map((key) => {
      filters[key].forEach((value) => {
        queryString += '&' + key + '=' + value
      })
      return queryString
    })
  }
  return queryString
}

function isFilterActive(filters) {
  return Object.values(filters).some(f => f.length > 0)
}

function applyFilter(haystack, searchTerms, fuzzy) {
  if (fuzzy) {
    searchTerms = searchTerms.map(s => s.replace(/\*/g, '(.*)'))
  }
  const searchPatterns = searchTerms.map(s => new RegExp(`^${s}$`))
  for (const text of haystack) {
    if (searchPatterns.some(p => p.test(text))) {
      return true
    }
  }
  return false
}

export {
  applyFilter,
  getFiltersFromUrl,
  isFilterActive,
  makeQueryString,
  writeFiltersToUrl,
}

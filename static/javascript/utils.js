export const breakpointCalcURL = '/breakpoint-calc/'

export const choicesOptions = {
  searchPlaceholderValue: 'Type in at least 3 characters',
  searchFloor: 3,
  searchResultLimit: 10,
  itemSelectText: '',
  loadingText: 'loading',
  shouldSort: false,
}

const debounceEvent = (callbackFn, time, interval) =>
  (...args) => {
    clearTimeout(interval)
    interval = setTimeout(() => {
      interval = null
      callbackFn(...args)
    }, time)
  }

export const processInput = debounceEvent((select, event) => {
  const value = event.target.value

  if (value.length > 2) {
    fetchPokemon(select, value)
  }
}, 500)

const fetchPokemon = (select, value) => {
  select.ajax(callback => {
    fetch(`${window.pgoAPIURLs['simple-pokemon-list']}?pokemon-slug=${value}`)
      .then(response => {
        response.json()
          .then(data => {
            select.clearChoices()
            callback(data.results, 'value', 'label')
          })
          .then(() => {
            select.input.element.focus()
          })
          .catch(() => {
            showErrors()
          })
      })
      .catch(() => {
        showErrors()
      })
  })
}

export const showErrors = () => {
  const results = document.querySelector('.results')
  results.hidden = false
  results.classList.add('error-text')
  results.innerHTML = ':( something broke, let me know if refreshing the page does not help.'
}

export const formatParams = (params) => {
  const paramsCopy = {...params}
  delete paramsCopy.status
  delete paramsCopy.staleTab

  return `?${Object.keys(paramsCopy).map((key) =>
    `${key}=${encodeURIComponent(paramsCopy[key])}`
  ).join('&')}`
}

export const updateBrowserHistory = (getParams, url) => {
  window.history.pushState(
    {}, null, url + getParams
  )
}

export const fetchPokemonChoice = (select, pokemonSlug) => {
  select.ajax(callback => {
    fetch(`${window.pgoAPIURLs['simple-pokemon-list']}${pokemonSlug}/`)
      .then(response => {
        response.json()
          .then(data => {
            callback(data, 'value', 'label')
          })
          .then(() => {
            select.setChoiceByValue(pokemonSlug)
          })
      })
  })
}

export const validateLevel = (input) => {
  const val = input.value.replace(',', '.')
  let level = parseFloat(val)

  if (level < 0) {
    level *= -1
  }
  if (level < 1) {
    level = 1
  }
  if (level > 40) {
    level = 40
  }
  if ((level * 10) % 5 !== 0) {
    level = parseInt(level)
  }
  return level
}

export const createMoveOption = (moveData, moveId, moveKey, form, pokemon = 'attacker') => {
  const move = moveData.move

  return new Option(
    pokemon === 'attacker' ? `${move.name} ${moveData.legacy ? '*' : ''} (${move.power})` : move.name,
    move.id,
    false,
    determineSelectedMove(moveId, move, moveKey, form)
  )
}

const determineSelectedMove = (moveId, move, type, form) => {
  if (moveId > 0 && moveId === move.id) {
    form[type] = move.id
    return true
  }
  return false
}

export const processParams = (params) => {
  const queryDict = {}
  params.substr(1).split('&').forEach((item) => {
    queryDict[item.split('=')[0]] = item.split('=')[1]
  })
  return queryDict
}
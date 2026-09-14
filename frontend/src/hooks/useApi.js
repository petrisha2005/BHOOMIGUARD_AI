import { useCallback, useEffect, useState } from 'react'

export function useApi(loader) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async () => {
    try {
      setLoading(true)
      setError('')
      setData(await loader())
    } catch (requestError) {
      setError(requestError.message || 'The requested information could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [loader])

  useEffect(() => {
    let active = true

    async function loadInitialData() {
      try {
        const result = await loader()
        if (active) {
          setData(result)
          setError('')
        }
      } catch (requestError) {
        if (active) setError(requestError.message || 'The requested information could not be loaded.')
      } finally {
        if (active) setLoading(false)
      }
    }

    loadInitialData()
    return () => {
      active = false
    }
  }, [loader])

  return { data, error, loading, reload }
}

import { useEffect, useState } from 'react'
import { createRequest, deleteRequest, fetchRequests, updateStatus } from './api'
import { nextStatus, upsertRequest, type NewRequest, type RequestItem, type Status } from './requests'
import { subscribeRequests, type RequestEvent } from './realtime'

export function useRequests() {
  const [requests, setRequests] = useState<RequestItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let ignore = false
    let unsubscribe: (() => void) | undefined
    let pending: RequestEvent[] | null = []

    function apply(list: RequestItem[], { action, record }: RequestEvent) {
      return action === 'delete'
        ? list.filter((item) => item.id !== record.id)
        : upsertRequest(list, record)
    }

    async function load() {
      try {
        unsubscribe = await subscribeRequests((event) => {
          if (ignore) return
          if (pending) pending.push(event)
          else setRequests((list) => apply(list, event))
        })
        if (ignore) {
          unsubscribe()
          return
        }
        const list = await fetchRequests()
        if (!ignore) {
          // События могли прийти между подпиской и ответом со списком.
          setRequests((pending ?? []).reduce(apply, list))
          pending = null
        }
      } catch {
        if (!ignore) {
          unsubscribe?.()
          setError('Не удалось загрузить заявки. Проверьте, что PocketBase запущен.')
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    void load()
    return () => {
      ignore = true
      unsubscribe?.()
    }
  }, [attempt])

  function retry() {
    setError('')
    setLoading(true)
    setAttempt((value) => value + 1)
  }

  async function add(data: NewRequest): Promise<RequestItem> {
    const created = await createRequest(data)
    setRequests((list) => upsertRequest(list, created))
    return created
  }

  async function next(id: string, status: Status) {
    const updated = await updateStatus(id, nextStatus(status))
    setRequests((list) => upsertRequest(list, updated))
  }

  async function remove(id: string) {
    await deleteRequest(id)
    setRequests((list) => list.filter((r) => r.id !== id))
  }

  return { requests, loading, error, retry, add, next, remove }
}

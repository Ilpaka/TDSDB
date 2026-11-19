import { useEffect, useState } from 'react'
import Header from './components/Header'
import RequestForm from './components/RequestForm'
import RequestCard from './components/RequestCard'
import type { NewRequest, Status } from './requests'
import { useRequests } from './useRequests'
import { sendRequest } from './notify'

type Filter = 'Все' | Status

const FILTERS: Filter[] = ['Все', 'Новая', 'В работе', 'Готово']

function App() {
  const { requests, loading, error, retry, add, next, remove } = useRequests()
  const [filter, setFilter] = useState<Filter>('Все')
  const [notice, setNotice] = useState('')

  const newCount = requests.filter((r) => r.status === 'Новая').length
  const visible = filter === 'Все' ? requests : requests.filter((r) => r.status === filter)

  useEffect(() => {
    document.title = `Новых: ${newCount} · Заявки в общежитие`
  }, [newCount])

  useEffect(() => {
    if (notice === '') {
      return
    }
    const timer = setTimeout(() => setNotice(''), 5000)
    return () => clearTimeout(timer)
  }, [notice])

  useEffect(() => {
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setFilter('Все')
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  async function handleNext(id: string, status: Status) {
    try {
      await next(id, status)
    } catch (e) {
      setNotice((e as Error).message)
    }
  }

  async function handleAdd(data: NewRequest) {
    const created = await add(data)
    setNotice('Заявка добавлена. Отправляем уведомление…')
    void sendRequest(created).then((sent) => {
      setNotice(sent
        ? 'Заявка добавлена. Сервер принял уведомление.'
        : 'Заявка добавлена, но уведомление не отправлено: сервер автоматизации недоступен.')
    })
  }

  async function handleRemove(id: string) {
    try {
      await remove(id)
    } catch (e) {
      setNotice((e as Error).message)
    }
  }

  return (
    <>
      <Header newCount={newCount} />
      <main className="board">
        <RequestForm onAdd={handleAdd} />
        <section className="list">
          <h2>Заявки</h2>
          {notice !== '' && <p className="notice" role="status">{notice}</p>}
          <div className="filters">
            {FILTERS.map((f) => (
              <button key={f} className={f === filter ? 'active' : ''} onClick={() => setFilter(f)}>
                {f}
              </button>
            ))}
          </div>
          {loading && <p className="empty">Загрузка заявок…</p>}
          {error !== '' && (
            <div className="load-error">
              <p>{error}</p>
              <button onClick={retry}>Повторить</button>
            </div>
          )}
          {!loading && error === '' && visible.length === 0 && <p className="empty">Заявок с таким статусом нет</p>}
          {visible.map((r) => (
            <RequestCard
              key={r.id}
              title={r.title}
              room={r.room}
              category={r.category}
              details={r.details}
              status={r.status}
              onNext={() => handleNext(r.id, r.status)}
              onRemove={() => handleRemove(r.id)}
            />
          ))}
        </section>
      </main>
    </>
  )
}

export default App

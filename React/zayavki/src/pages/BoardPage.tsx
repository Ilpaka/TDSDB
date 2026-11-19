import { useEffect, useState } from 'react'
import RequestForm from '../components/RequestForm'
import RequestCard from '../components/RequestCard'
import { useBoard } from '../board'
import type { Status } from '../requests'

type Filter = 'Все' | Status

const FILTERS: Filter[] = ['Все', 'Новая', 'В работе', 'Готово']

function BoardPage() {
  const { requests, loading, error, retry, handleAdd, handleNext, handleRemove } = useBoard()
  const [filter, setFilter] = useState<Filter>('Все')

  const visible = filter === 'Все' ? requests : requests.filter((r) => r.status === filter)

  useEffect(() => {
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setFilter('Все')
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  return (
    <main className="board">
      <RequestForm onAdd={handleAdd} />
      <section className="list">
        <h2>Заявки</h2>
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
            id={r.id}
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
  )
}

export default BoardPage

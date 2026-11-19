import { useState } from 'react'
import { Link } from 'react-router'
import type { Category, Status } from '../requests'

type RequestCardProps = {
  id: string
  title: string
  room: string
  category: Category
  details: string
  status: Status
  onNext: () => void
  onRemove: () => void
}

function RequestCard({ id, title, room, category, details, status, onNext, onRemove }: RequestCardProps) {
  const [open, setOpen] = useState(false)

  return (
    <article className="card">
      <div className="card__top">
        <span className="card__room">каб. {room} · {category}</span>
        <span className="card__status">{status}</span>
      </div>
      <h3>
        <Link to={`/requests/${id}`}>{title}</Link>
      </h3>
      {open && <p>{details}</p>}
      <div className="card__actions">
        <button className="card__more" onClick={() => setOpen(!open)}>
          {open ? 'Скрыть' : 'Подробнее'}
        </button>
        {status === 'Готово' ? (
          <button onClick={onRemove}>Убрать с доски</button>
        ) : (
          <button onClick={onNext}>{status === 'Новая' ? 'Взять в работу' : 'Завершить'}</button>
        )}
      </div>
    </article>
  )
}

export default RequestCard

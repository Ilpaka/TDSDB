import { Link, useNavigate, useParams } from 'react-router'
import { useBoard } from '../board'

function RequestPage() {
  const { requests, loading, error, retry, handleNext, handleRemove } = useBoard()
  const { id } = useParams()
  const navigate = useNavigate()

  if (loading) {
    return (
      <main className="page">
        <p className="empty">Загрузка заявки…</p>
      </main>
    )
  }

  if (error) {
    return <main className="page"><p role="alert">{error}</p><button onClick={retry}>Повторить</button></main>
  }

  const request = requests.find((r) => r.id === id)
  if (request === undefined) {
    return (
      <main className="page">
        <Link to="/" className="back">← Все заявки</Link>
        <p className="empty">Заявки с номером {id} нет: её удалили или в адресе ошибка.</p>
      </main>
    )
  }

  async function removeAndReturn(requestId: string) {
    if (await handleRemove(requestId)) navigate('/')
  }

  return (
    <main className="page">
      <Link to="/" className="back">← Все заявки</Link>
      <article className="card request">
        <div className="card__top">
          <span className="card__room">каб. {request.room} · {request.category}</span>
          <span className="card__status">{request.status}</span>
        </div>
        <h2>{request.title}</h2>
        <p>{request.details === '' ? 'Подробностей нет.' : request.details}</p>
        <p className="request__id">Номер заявки: {request.id}</p>
        <div className="card__actions">
          {request.status === 'Готово' ? (
            <button onClick={() => removeAndReturn(request.id)}>Убрать с доски</button>
          ) : (
            <button onClick={() => handleNext(request.id, request.status)}>
              {request.status === 'Новая' ? 'Взять в работу' : 'Завершить'}
            </button>
          )}
        </div>
      </article>
    </main>
  )
}

export default RequestPage

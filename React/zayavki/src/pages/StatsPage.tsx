import { useBoard } from '../board'
import type { Category, Status } from '../requests'

const STATUSES: Status[] = ['Новая', 'В работе', 'Готово']
const CATEGORIES: Category[] = ['Компьютер', 'Проектор', 'Принтер', 'Интернет']

function StatsPage() {
  const { requests, loading, error, retry } = useBoard()

  if (loading) {
    return (
      <main className="page">
        <p className="empty">Загрузка заявок…</p>
      </main>
    )
  }

  if (error) {
    return <main className="page"><p role="alert">{error}</p><button onClick={retry}>Повторить</button></main>
  }

  return (
    <main className="page">
      <h2>Статистика</h2>
      <p>Всего заявок: {requests.length}</p>
      <div className="stats">
        <table>
          <thead>
            <tr><th>Статус</th><th>Заявок</th></tr>
          </thead>
          <tbody>
            {STATUSES.map((s) => (
              <tr key={s}>
                <td>{s}</td>
                <td>{requests.filter((r) => r.status === s).length}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <table>
          <thead>
            <tr><th>Категория</th><th>Заявок</th></tr>
          </thead>
          <tbody>
            {CATEGORIES.map((c) => (
              <tr key={c}>
                <td>{c}</td>
                <td>{requests.filter((r) => r.category === c).length}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  )
}

export default StatsPage

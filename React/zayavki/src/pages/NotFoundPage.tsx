import { Link, useLocation } from 'react-router'

function NotFoundPage() {
  const { pathname } = useLocation()

  return (
    <main className="page">
      <h2>Страница не найдена</h2>
      <p>Адреса {pathname} в приложении нет.</p>
      <Link to="/">К заявкам</Link>
    </main>
  )
}

export default NotFoundPage

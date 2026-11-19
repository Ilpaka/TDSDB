import { NavLink } from 'react-router'
import { useBoard } from '../board'

function Header() {
  const { newCount } = useBoard()

  return (
    <header className="header">
      <h1>Доска заявок</h1>
      <p>ИТ-отдел колледжа · заявки студентов и преподавателей</p>
      <span className="header__count">Новых заявок: {newCount}</span>
      <nav className="nav">
        <NavLink to="/">Заявки</NavLink>
        <NavLink to="/stats">Статистика</NavLink>
      </nav>
    </header>
  )
}

export default Header

type HeaderProps = {
  newCount: number
}

function Header({ newCount }: HeaderProps) {
  return (
    <header className="header">
      <h1>Заявки в общежитие</h1>
      <p>Заявки жильцов коменданту</p>
      <span className="header__count">Новых заявок: {newCount}</span>
    </header>
  )
}

export default Header

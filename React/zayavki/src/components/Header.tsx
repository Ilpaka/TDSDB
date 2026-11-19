type HeaderProps = {
  newCount: number
}

function Header({ newCount }: HeaderProps) {
  return (
    <header className="header">
      <h1>Доска заявок</h1>
      <p>ИТ-отдел колледжа · заявки студентов и преподавателей</p>
      <span className="header__count">Новых заявок: {newCount}</span>
    </header>
  )
}

export default Header

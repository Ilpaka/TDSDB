import { useState, type SubmitEvent } from 'react'
import type { Category, NewRequest } from '../requests'

type RequestFormProps = {
  onAdd: (request: NewRequest) => void
}

function RequestForm({ onAdd }: RequestFormProps) {
  const [title, setTitle] = useState('')
  const [room, setRoom] = useState('')
  const [category, setCategory] = useState<Category>('Сантехника')
  const [details, setDetails] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (title.trim() === '' || room.trim() === '') {
      setError('Заполните поля «Что случилось» и «Комната».')
      return
    }
    onAdd({ title: title.trim(), room: room.trim(), category, details: details.trim() })
    setTitle('')
    setRoom('')
    setCategory('Сантехника')
    setDetails('')
    setError('')
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <h2>Новая заявка</h2>

      <label htmlFor="title">Что случилось</label>
      <input
        id="title"
        type="text"
        placeholder="Например: течёт кран"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
      />

      <label htmlFor="room">Комната</label>
      <input
        id="room"
        type="text"
        placeholder="214"
        value={room}
        onChange={(event) => setRoom(event.target.value)}
      />

      <label htmlFor="category">Категория</label>
      <select
        id="category"
        value={category}
        onChange={(event) => setCategory(event.target.value as Category)}
      >
        <option>Сантехника</option>
        <option>Электрика</option>
        <option>Мебель</option>
        <option>Интернет</option>
      </select>

      <label htmlFor="details">Подробности</label>
      <textarea
        id="details"
        rows={3}
        value={details}
        onChange={(event) => setDetails(event.target.value)}
      />

      {error !== '' && <p className="form__error" role="alert">{error}</p>}

      <button type="submit">Отправить заявку</button>
    </form>
  )
}

export default RequestForm

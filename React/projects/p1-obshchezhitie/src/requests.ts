export type Status = 'Новая' | 'В работе' | 'Готово'

export type Category = 'Сантехника' | 'Электрика' | 'Мебель' | 'Интернет'

export type RequestItem = {
  id: number
  title: string
  room: string
  category: Category
  details: string
  status: Status
}

export type NewRequest = {
  title: string
  room: string
  category: Category
  details: string
}

export const initialRequests: RequestItem[] = [
  {
    id: 1,
    title: 'Капает кран у раковины',
    room: '214',
    category: 'Сантехника',
    details: 'После закрытия крана вода продолжает капать.',
    status: 'Новая',
  },
  {
    id: 2,
    title: 'Не горит свет над столом',
    room: '308',
    category: 'Электрика',
    details: 'Лампу заменили, светильник всё равно не включается.',
    status: 'В работе',
  },
  {
    id: 3,
    title: 'Шатается ножка стула',
    room: '117',
    category: 'Мебель',
    details: 'Мастер закрепил ножку. Стул вернули в комнату.',
    status: 'Готово',
  },
  {
    id: 4,
    title: 'Пропадает Wi-Fi',
    room: '402',
    category: 'Интернет',
    details: 'После девяти вечера связь обрывается на нескольких телефонах.',
    status: 'Новая',
  },
  {
    id: 5,
    title: 'Не закрывается дверца шкафа',
    room: '225',
    category: 'Мебель',
    details: 'Верхняя петля отошла от стенки, дверца висит под углом.',
    status: 'Новая',
  },
]

export function nextStatus(status: Status): Status {
  if (status === 'Новая') {
    return 'В работе'
  }
  return 'Готово'
}

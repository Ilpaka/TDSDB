export type Status = 'Новая' | 'В работе' | 'Готово'

export type Category = 'Компьютер' | 'Проектор' | 'Принтер' | 'Интернет'

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
    title: 'Не работает проектор',
    room: '214',
    category: 'Проектор',
    details: 'Проектор включается, но изображения на экране нет.',
    status: 'Новая',
  },
  {
    id: 2,
    title: 'Нет интернета',
    room: '305',
    category: 'Интернет',
    details: 'На всех компьютерах в кабинете не открываются сайты.',
    status: 'В работе',
  },
  {
    id: 3,
    title: 'Замятие бумаги в принтере',
    room: '112',
    category: 'Принтер',
    details: 'Принтер пишет «замятие бумаги», лоток пустой.',
    status: 'Готово',
  },
  {
    id: 4,
    title: 'Не включается компьютер',
    room: '214',
    category: 'Компьютер',
    details: 'Компьютер преподавателя не реагирует на кнопку питания.',
    status: 'Новая',
  },
  {
    id: 5,
    title: 'Не работает мышь',
    room: '118',
    category: 'Компьютер',
    details: 'Курсор не двигается, мышь подключена к компьютеру № 7.',
    status: 'Новая',
  },
]

export function nextStatus(status: Status): Status {
  if (status === 'Новая') {
    return 'В работе'
  }
  return 'Готово'
}

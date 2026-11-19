import type { Check } from './types'

export function statusText(check?: Check) {
  if (!check) return 'Нет проверки'
  if (check.ok) return `Работает · ${check.ms} мс`
  return `Не открывается · ${check.status || check.error || 'нет ответа'}`
}

const moscowTime = new Intl.DateTimeFormat('ru-RU', {
  day: '2-digit', month: 'long', year: 'numeric',
  hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Moscow',
})

export function formatTime(iso: string) {
  return moscowTime.format(new Date(iso))
}

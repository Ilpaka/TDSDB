export function sitesWord(count: number) {
  const last = count % 10
  const lastTwo = count % 100
  if (last === 1 && lastTwo !== 11) {
    return 'сайт'
  }
  if (last >= 2 && last <= 4 && (lastTwo < 12 || lastTwo > 14)) {
    return 'сайта'
  }
  return 'сайтов'
}

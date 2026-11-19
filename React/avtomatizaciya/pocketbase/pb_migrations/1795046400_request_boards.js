migrate((app) => {
  const boards = [
    {
      name: 'requests',
      categories: ["Компьютер", "Проектор", "Принтер", "Интернет"],
      examples: [
        ["Не работает проектор", "214", "Проектор", "Проектор включается, но изображения на экране нет.", "Новая"],
        ["Нет интернета", "305", "Интернет", "На всех компьютерах в кабинете не открываются сайты.", "В работе"],
        ["Замятие бумаги в принтере", "112", "Принтер", "Принтер пишет «замятие бумаги», лоток пустой.", "Готово"],
        ["Не включается компьютер", "214", "Компьютер", "Компьютер преподавателя не реагирует на кнопку питания.", "Новая"],
        ["Не работает мышь", "118", "Компьютер", "Курсор не двигается, мышь подключена к компьютеру № 7.", "Новая"],
      ],
    },
    {
      name: 'obshchezhitie',
      categories: ["Сантехника", "Электрика", "Мебель", "Интернет"],
      examples: [
        ["Капает кран у раковины", "214", "Сантехника", "После закрытия крана вода продолжает капать.", "Новая"],
        ["Не горит свет над столом", "308", "Электрика", "Лампу заменили, светильник всё равно не включается.", "В работе"],
        ["Шатается ножка стула", "117", "Мебель", "Мастер закрепил ножку. Стул вернули в комнату.", "Готово"],
        ["Пропадает Wi-Fi", "402", "Интернет", "После девяти вечера связь обрывается на нескольких телефонах.", "Новая"],
        ["Не закрывается дверца шкафа", "225", "Мебель", "Верхняя петля отошла от стенки, дверца висит под углом.", "Новая"],
      ],
    },
  ]

  for (const board of boards) {
    const collection = new Collection({
      type: 'base',
      name: board.name,
      listRule: '',
      viewRule: '',
      createRule: '@request.body.status = "Новая"',
      updateRule: '@request.body.title:isset = false && @request.body.room:isset = false && @request.body.details:isset = false',
      deleteRule: 'status = "Готово"',
      fields: [
        { name: 'title', type: 'text', required: true },
        { name: 'room', type: 'text', required: true },
        { name: 'category', type: 'select', required: true, maxSelect: 1, values: board.categories },
        { name: 'details', type: 'text' },
        { name: 'status', type: 'select', required: true, maxSelect: 1, values: ['Новая', 'В работе', 'Готово'] },
        { name: 'created', type: 'autodate', onCreate: true },
        { name: 'updated', type: 'autodate', onCreate: true, onUpdate: true },
      ],
    })
    app.save(collection)
    for (const [title, room, category, details, status] of board.examples) {
      const record = new Record(collection)
      record.load({ title, room, category, details, status })
      app.save(record)
    }
  }
})

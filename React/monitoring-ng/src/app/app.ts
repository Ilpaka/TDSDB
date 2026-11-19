import { Component, computed, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Monitoring } from './monitoring';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  template: `
    <header class="header">
      <h1>Мониторинг сайтов группы</h1>
      <p>{{ lastCheck() }}</p>
    </header>
    <main class="main">
      <router-outlet />
    </main>
  `,
})
export class App {
  private readonly monitoring = inject(Monitoring);
  protected readonly lastCheck = computed(() => {
    const last = this.monitoring.history()[0];
    return last === undefined
      ? 'Проверок ещё не было'
      : `Последняя проверка: ${new Date(last.time).toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' })} МСК`;
  });
}

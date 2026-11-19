import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Monitoring } from '../monitoring';
import { sitesWord } from '../plural';
import { statusText } from '../status';

@Component({
  selector: 'app-sites-page',
  imports: [RouterLink],
  templateUrl: './sites-page.html',
})
export class SitesPage {
  protected readonly monitoring = inject(Monitoring);
  protected readonly query = signal('');
  protected readonly onlyDown = signal(false);

  private readonly last = computed(() => this.monitoring.history()[0]);
  protected readonly down = computed(
    () => this.monitoring.sites().filter((site) => this.check(site.id)?.ok === false).length,
  );
  protected readonly summary = computed(() => {
    const count = this.monitoring.sites().length;
    if (this.last() === undefined) {
      return 'Проверок ещё не было';
    }
    if (this.down() > 0) {
      return `Не открываются: ${this.down()} из ${count}`;
    }
    const checked = this.monitoring.sites().filter((site) => this.check(site.id) !== undefined).length;
    if (checked < count) return `Проверены: ${checked} из ${count}`;
    if (count === 0) return 'Список сайтов пуст';
    if (count === 1) return '1 сайт открывается';
    return `Все ${count} ${sitesWord(count)} открываются`;
  });
  protected readonly shown = computed(() => {
    const text = this.query().trim().toLowerCase();
    return this.monitoring
      .sites()
      .filter((site) => site.name.toLowerCase().includes(text))
      .filter((site) => !this.onlyDown() || this.check(site.id)?.ok === false);
  });

  protected check(id: string) {
    return this.last()?.checks.find((c) => c.id === id);
  }

  protected status(id: string) {
    return statusText(this.check(id));
  }
}

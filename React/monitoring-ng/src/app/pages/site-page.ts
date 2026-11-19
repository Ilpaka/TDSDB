import { Component, computed, inject, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Monitoring } from '../monitoring';

@Component({
  selector: 'app-site-page',
  imports: [RouterLink],
  template: `
    <a routerLink="/" class="back">← Все сайты</a>
    @if (monitoring.loading()) {
      <p role="status">Загрузка результатов…</p>
    } @else if (monitoring.error()) {
      <p role="alert">{{ monitoring.error() }}</p>
    } @else if (site(); as site) {
      <h2>{{ site.name }}</h2>
      <p><a [href]="site.url" target="_blank" rel="noreferrer">{{ site.url }}</a></p>
    } @else {
      <p class="empty">Сайта «{{ id() }}» нет в списке.</p>
    }
  `,
})
export class SitePage {
  protected readonly monitoring = inject(Monitoring);
  readonly id = input.required<string>();
  protected readonly site = computed(() => this.monitoring.sites().find((s) => s.id === this.id()));
}

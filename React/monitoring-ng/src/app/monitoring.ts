import { httpResource, HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed } from '@angular/core';
import { Run, Site } from './types';

function loadError(name: string, error: unknown): string {
  const status = error instanceof HttpErrorResponse ? error.status : 0;
  return `Файл ${name} не загрузился: код ${status}.`;
}

@Injectable({ providedIn: 'root' })
export class Monitoring {
  private readonly sitesFile = httpResource<Site[]>(() => 'data/sites.json');
  private readonly resultsFile = httpResource<{ history: Run[] }>(() => 'data/results.json');

  readonly sites = computed(() => this.sitesFile.hasValue() ? this.sitesFile.value() : []);
  readonly history = computed(() => this.resultsFile.hasValue() ? this.resultsFile.value().history : []);
  readonly loading = computed(() => this.sitesFile.isLoading() || this.resultsFile.isLoading());
  readonly error = computed(() => {
    if (this.sitesFile.error()) {
      return loadError('sites.json', this.sitesFile.error());
    }
    if (this.resultsFile.error()) {
      return loadError('results.json', this.resultsFile.error());
    }
    return '';
  });
}

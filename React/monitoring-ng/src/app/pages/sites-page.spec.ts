import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Monitoring } from '../monitoring';
import { Run, Site } from '../types';
import { SitesPage } from './sites-page';

const sites: Site[] = [
  { id: 'git', name: 'Справочник по Git', url: 'https://example.org/git/' },
  { id: 'react', name: 'Справочник по React', url: 'https://example.org/react/' },
  { id: 'sql', name: 'Задачник по SQL', url: 'https://example.org/sql/' },
];

const run: Run = {
  time: '2026-11-12T21:00:00Z',
  checks: [
    { id: 'git', ok: true, status: 200, ms: 340, error: '' },
    { id: 'react', ok: false, status: 404, ms: 120, error: '' },
    { id: 'sql', ok: true, status: 200, ms: 510, error: '' },
  ],
};

async function show() {
  const fake = {
    sites: signal(sites),
    history: signal([run]),
    loading: signal(false),
    error: signal(''),
  };
  TestBed.configureTestingModule({
    providers: [provideRouter([]), { provide: Monitoring, useValue: fake }],
  });
  const fixture = TestBed.createComponent(SitesPage);
  await fixture.whenStable();
  return fixture;
}

function names(page: HTMLElement) {
  return [...page.querySelectorAll('h2')].map((h) => h.textContent);
}

describe('SitesPage', () => {
  it('считает сайты, которые не открываются', async () => {
    const fixture = await show();
    const page: HTMLElement = fixture.nativeElement;
    expect(page.querySelector('.summary')?.textContent).toBe('Не открываются: 1 из 3');
  });

  it('карточка ведёт на страницу сайта', async () => {
    const fixture = await show();
    const page: HTMLElement = fixture.nativeElement;
    const link = page.querySelectorAll('a.site')[1];
    expect(link.getAttribute('href')).toBe('/site/react');
  });

  it('поиск оставляет одну карточку', async () => {
    const fixture = await show();
    const page: HTMLElement = fixture.nativeElement;
    const input = page.querySelector<HTMLInputElement>('input[type=search]')!;
    input.value = 'react';
    input.dispatchEvent(new Event('input'));
    await fixture.whenStable();
    expect(names(page)).toEqual(['Справочник по React']);
  });

  it('поиск git с флажком: сайтов не найдено', async () => {
    const fixture = await show();
    const page: HTMLElement = fixture.nativeElement;
    const input = page.querySelector<HTMLInputElement>('input[type=search]')!;
    input.value = 'git';
    input.dispatchEvent(new Event('input'));
    page.querySelector<HTMLInputElement>('input[type=checkbox]')!.click();
    await fixture.whenStable();
    expect(names(page)).toEqual([]);
    expect(page.textContent).toContain('Сайтов не найдено');
  });
});

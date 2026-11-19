import { Routes } from '@angular/router';
import { SitePage } from './pages/site-page';
import { SitesPage } from './pages/sites-page';

export const routes: Routes = [
  { path: '', component: SitesPage, title: 'Сайты · Мониторинг сайтов группы' },
  { path: 'site/:id', component: SitePage, title: 'Сайт · Мониторинг сайтов группы' },
];

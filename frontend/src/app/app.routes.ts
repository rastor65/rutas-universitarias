import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/accounts/login',
    pathMatch: 'full',
  },
  {
    path: 'accounts',
    loadChildren: () =>
      import('./features/accounts/accounts.routes').then(
        (m) => m.accountsRoutes
      ),
  },
  {
    path: 'dashboard',
    loadChildren: () =>
      import('./features/dashboard/dashboard.routes').then(
        (m) => m.DASHBOARD_ROUTES
      ),
  },
];

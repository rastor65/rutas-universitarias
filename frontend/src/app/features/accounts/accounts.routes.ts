import { Routes } from '@angular/router';
import { LoginComponent } from './login/login';

export const accountsRoutes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full',
  },
  {
    path: 'login',
    component: LoginComponent,
    title: 'Iniciar sesión',
  },
//   {
//     path: 'register',
//     loadComponent: () =>
//       import('./register/register').then((m) => m.RegisterComponent),
//     title: 'Registro de usuario',
//   },
//   {
//     path: 'logout',
//     loadComponent: () =>
//       import('./logout/logout').then((m) => m.LogoutComponent),
//     title: 'Cerrar sesión',
//   },
];

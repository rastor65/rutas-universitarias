import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface User {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_staff: boolean;
  roles?: any[];
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private API_URL = `${environment.API_URI}/api/accounts/auth/`;
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  currentUser$ = this.currentUserSubject.asObservable();

  constructor(private http: HttpClient) {}

  // --- Registrar un nuevo usuario ---
  register(data: any): Observable<User> {
    return this.http.post<User>(`${this.API_URL}register/`, data, {
      withCredentials: true,
    });
  }

  // --- Iniciar sesión ---
  login(credentials: { username: string; password: string }): Observable<User> {
    return this.http.post<User>(`${this.API_URL}login/`, credentials, {
      withCredentials: true,
    }).pipe(
      tap(user => this.currentUserSubject.next(user))
    );
  }

  // --- Cerrar sesión ---
  logout(): Observable<any> {
    return this.http.post(`${this.API_URL}logout/`, {}, { withCredentials: true }).pipe(
      tap(() => this.currentUserSubject.next(null))
    );
  }

  // --- Obtener usuario autenticado ---
  me(): Observable<User> {
    return this.http.get<User>(`${this.API_URL}me/`, { withCredentials: true }).pipe(
      tap(user => this.currentUserSubject.next(user))
    );
  }

  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  isAuthenticated(): boolean {
    return !!this.currentUserSubject.value;
  }
}

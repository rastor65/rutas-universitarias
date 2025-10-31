import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators, FormGroup } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  templateUrl: './login.html',
  imports: [CommonModule, ReactiveFormsModule],
})
export class LoginComponent implements OnInit {
  loading = false;
  error = '';
  form!: FormGroup; // ✅ declaramos sin inicializar

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // ✅ se crea después de que Angular inyecta fb
    this.form = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required],
    });
  }

  onSubmit(): void {
    if (this.form.invalid) return;

    this.loading = true;
    this.error = '';

    const username = this.form.value.username ?? '';
    const password = this.form.value.password ?? '';

    this.auth.login({ username, password }).subscribe({
      next: (response) => {
        this.loading = false;
        console.log('✅ Sesión iniciada:', response);
        this.router.navigate(['/dashboard']); // redirige
      },
      error: (err) => {
        this.loading = false;
        this.error = 'Credenciales incorrectas o error de conexión.';
        console.error('❌ Error de inicio de sesión:', err);
      },
    });
  }
}

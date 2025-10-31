import { Component, contentChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Header } from './layout/header/header';
import { Sidebar } from './layout/sidebar/sidebar';
import { Content } from './layout/content/content';
import { Footer } from './layout/footer/footer';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, Header, Sidebar, Content, Footer],
  template: `
    <div class="dashboard-layout">
      <app-header></app-header>

      <div class="dashboard-body">
        <app-sidebar></app-sidebar>
        <app-content></app-content>
      </div>

      <app-footer></app-footer>
    </div>
  `,
  styleUrls: ['./dashboard.css'],
})
export class Dashboard {}

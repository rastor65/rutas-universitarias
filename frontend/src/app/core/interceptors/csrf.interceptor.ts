import { HttpInterceptorFn } from '@angular/common/http';

export const CsrfInterceptor: HttpInterceptorFn = (req, next) => {
  const csrfToken = getCookie('csrftoken');
  if (csrfToken) {
    req = req.clone({
      withCredentials: true,
      setHeaders: { 'X-CSRFToken': csrfToken },
    });
  }
  return next(req);
};

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? match[2] : null;
}

import { Body, Injectable } from '@nestjs/common';

@Injectable()
export class AuthService {
  login(username: string, password: string, behavior: any[]) {
    try {
      if (username !== 'admin' || password !== 'password') {
        return { success: false, message: 'Invalid credentials' };
      }
    } catch (err) {
      console.error('Login error:', err);
      return { success: false, message: 'Login failed' };
    }
  }
}

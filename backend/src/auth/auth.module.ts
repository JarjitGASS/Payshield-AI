import { Module } from '@nestjs/common';
import { AuthService } from './auth.service';
import { AuthController } from './auth.controller';
import { QwenModule } from 'src/qwen/qwen.module';

@Module({
  imports: [QwenModule],
  controllers: [AuthController],
  providers: [AuthService],
})
export class AuthModule {}

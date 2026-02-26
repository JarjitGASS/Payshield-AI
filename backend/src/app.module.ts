import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { AuthModule } from './auth/auth.module';
import { QwenService } from './qwen/qwen.service';
import { QwenController } from './qwen/qwen.controller';
import { QwenModule } from './qwen/qwen.module';
import { ConfigModule } from '@nestjs/config';

@Module({
  imports: [
    AuthModule, 
    QwenModule,
    ConfigModule.forRoot({
      isGlobal: true,
    }),
  ],
  controllers: [AppController, QwenController],
  providers: [AppService, QwenService],
})
export class AppModule {}

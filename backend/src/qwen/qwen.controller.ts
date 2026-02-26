import { Controller, Post, Body } from '@nestjs/common';
import { QwenService } from './qwen.service';

@Controller('qwen')
export class QwenController {
  constructor(private readonly qwenService: QwenService) {}

  @Post('chat')
  async chat(@Body('prompt') prompt: string, @Body('system') system: string) {
    const result = await this.qwenService.generateText(prompt, system);
    return { result };
  }
}

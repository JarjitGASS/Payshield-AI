import { Test, TestingModule } from '@nestjs/testing';
import { QwenService } from './qwen.service';

describe('QwenService', () => {
  let service: QwenService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [QwenService],
    }).compile();

    service = module.get<QwenService>(QwenService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});

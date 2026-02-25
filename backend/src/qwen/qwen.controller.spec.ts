import { Test, TestingModule } from '@nestjs/testing';
import { QwenController } from './qwen.controller';

describe('QwenController', () => {
  let controller: QwenController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [QwenController],
    }).compile();

    controller = module.get<QwenController>(QwenController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });
});

import { Injectable, HttpException } from '@nestjs/common';
import axios from 'axios';
import OpenAI from "openai";

@Injectable()
export class QwenService {
  private readonly apiUrl = process.env.QWEN_API_URL || '';
  private readonly apiKey = process.env.QWEN_API_KEY || '';

  async generateText(prompt: string, system: string): Promise<string> {
    try {
      const client = new OpenAI({
        apiKey: this.apiKey,
        baseURL: this.apiUrl
      });

      const completion = await client.chat.completions.create({
        model: "qwen-plus",
        messages: [
          { role: "system", content: system },
          { role: "user", content: prompt }
        ],
      });

      return completion.choices[0].message.content || 'no result';
    } catch (error) {
      console.log(error);
      throw new HttpException(
        error.response?.data || 'Qwen API Error',
        error.response?.status || 500
      );
    }
  }
}
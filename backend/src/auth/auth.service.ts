import { Body, Injectable } from '@nestjs/common';
import { QwenService } from 'src/qwen/qwen.service';

@Injectable()
export class AuthService {
  constructor(private readonly qwenService: QwenService) {}

  async login(body: { username: string; password: string; behavior: any[] }) {
    try {
      if (body.username !== 'admin' || body.password !== 'password') {
        return { success: false, message: 'Invalid credentials' };
      }

      const prompt = `
        ROLE:
        You are a behavioral security system specialized in distinguishing humans from automated bots.

        INPUT:
        You are given a chronological list of browser interaction events from a single session.
        Each event may include:
        - t: timestamp in milliseconds
        - x, y: cursor coordinates
        - key: keyboard key
        - type: mousemove | keydown | keyup

        TASK:
        Analyze the interaction data and determine whether the session behavior is more likely Human or Bot.

        EVALUATION CRITERIA (use all that apply):
        1. Mouse dynamics:
          - Human: curved paths, variable speed, micro-corrections, pauses
          - Bot: linear paths, constant velocity, repeated coordinates

        2. Timing characteristics:
          - Human: irregular reaction times, natural pauses
          - Bot: uniform or unrealistically fast intervals

        3. Keyboard behavior:
          - Human: realistic key press durations and overlaps
          - Bot: instantaneous or perfectly timed sequences

        4. Input coordination:
          - Human: natural alternation between mouse and keyboard
          - Bot: rigid or mechanically ordered patterns

        5. Data quality:
          - If the dataset is sparse, noisy, or insufficient, reduce confidence accordingly.

        DECISION RULES:
        - Classify as "Bot" only if multiple strong bot indicators are present.
        - Otherwise, classify as "Human".
        - Confidence must reflect certainty given the data quality.

        OUTPUT:
        Return ONLY valid JSON.
        Do NOT include explanations, markdown, or extra text.

        FORMAT:
        {
          "classification": "Human" | "Bot",
          "confidence": number
        }

        INTERACTION DATA:
        ${JSON.stringify(body.behavior)}
      `;

      const system = "You are a deterministic security classifier. Output must be strict JSON only.";

      const rawAnalysis = await this.qwenService.generateText(system, prompt);
      
      let analysis: { classification: 'Human' | 'Bot'; confidence: number };

      try {
        analysis = JSON.parse(rawAnalysis.trim());
      } catch {
        return {
          success: false,
          message: 'Behavior analysis failed',
        };
      }

      if (analysis.classification === 'Bot' && analysis.confidence >= 0.5) {
        return {
          success: false,
          message: 'Login blocked: automated behavior detected',
          analysis: rawAnalysis,
        };
      }

      return {
        success: true,
        message: 'Login successful',
        analysis: rawAnalysis,
      };
    } catch (err) {
      console.error('Login error:', err);
      return { success: false, message: 'Login failed' };
    }
  }
}

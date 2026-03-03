/**
 * Token Counter Service
 * Estimates token usage for messages and prompts
 */

import { Tiktoken, encoding_for_model } from 'tiktoken';
import { ChatMessage, Tool } from '../types/openai';
import { createLogger } from './logger';

const logger = createLogger('token-counter');

export class TokenCounter {
  private encoder: Tiktoken | null = null;
  private fallbackEnabled = false;

  constructor() {
    try {
      // Use cl100k_base encoding (same as GPT-4)
      this.encoder = encoding_for_model('gpt-4');
      logger.info({ type: 'token_counter_init', encoding: 'cl100k_base' });
    } catch (error) {
      logger.warn({
        type: 'token_counter_fallback',
        error,
        message: 'Failed to initialize tiktoken, using approximate counting',
      });
      this.fallbackEnabled = true;
    }
  }

  /**
   * Count tokens in a text string
   */
  count(text: string): number {
    if (!text) return 0;

    if (this.encoder && !this.fallbackEnabled) {
      try {
        const tokens = this.encoder.encode(text);
        return tokens.length;
      } catch (error) {
        logger.warn({ type: 'tiktoken_error', error, text: text.slice(0, 100) });
        return this.approximateCount(text);
      }
    }

    return this.approximateCount(text);
  }

  /**
   * Approximate token count (fallback method)
   * Rule of thumb: ~4 characters per token for English, ~2 for code
   */
  private approximateCount(text: string): number {
    // Count words and characters
    const words = text.split(/\s+/).length;
    const chars = text.length;

    // Heuristic: average between word count and char count / 4
    const estimate = Math.ceil((words + chars / 4) / 2);

    return estimate;
  }

  /**
   * Count tokens in an array of chat messages
   * Accounts for message formatting overhead
   */
  countMessages(messages: ChatMessage[]): number {
    let totalTokens = 0;

    // Each message has formatting overhead
    // Based on OpenAI's token counting: every message follows <|start|>{role/name}\n{content}<|end|>\n
    const tokensPerMessage = 4; // <|start|>, role, content, <|end|>
    const tokensPerName = 1; // if name is present

    for (const message of messages) {
      totalTokens += tokensPerMessage;

      if (message.role) {
        totalTokens += this.count(message.role);
      }

      if (message.content) {
        totalTokens += this.count(message.content);
      }

      if (message.name) {
        totalTokens += tokensPerName;
        totalTokens += this.count(message.name);
      }

      // Tool calls
      if (message.tool_calls) {
        for (const toolCall of message.tool_calls) {
          totalTokens += this.count(toolCall.function.name);
          totalTokens += this.count(toolCall.function.arguments);
          totalTokens += 3; // formatting overhead
        }
      }

      // Function call (deprecated but still supported)
      if (message.function_call) {
        totalTokens += this.count(message.function_call.name);
        totalTokens += this.count(message.function_call.arguments);
        totalTokens += 3; // formatting overhead
      }
    }

    // Add 3 tokens for reply priming (<|start|>assistant<|message|>)
    totalTokens += 3;

    return totalTokens;
  }

  /**
   * Estimate tokens for tool definitions
   * Tools add significant overhead to prompts
   */
  estimateTools(tools: Tool[]): number {
    if (!tools || tools.length === 0) return 0;

    let totalTokens = 0;

    // Base overhead for tools section
    totalTokens += 10; // "tools:" header and formatting

    for (const tool of tools) {
      // Function name and type
      totalTokens += this.count(tool.function.name);
      totalTokens += this.count(tool.type);

      // Description
      if (tool.function.description) {
        totalTokens += this.count(tool.function.description);
      }

      // Parameters schema (JSON)
      if (tool.function.parameters) {
        const schemaJson = JSON.stringify(tool.function.parameters);
        totalTokens += this.count(schemaJson);
      }

      // Formatting overhead per tool
      totalTokens += 5;
    }

    return totalTokens;
  }

  /**
   * Estimate total prompt tokens for a request
   */
  estimatePromptTokens(params: {
    messages: ChatMessage[];
    tools?: Tool[];
    systemInstruction?: string;
  }): number {
    let total = 0;

    // System instruction (if provided)
    if (params.systemInstruction) {
      total += this.count(params.systemInstruction);
      total += 4; // formatting overhead
    }

    // Messages
    total += this.countMessages(params.messages);

    // Tools
    if (params.tools) {
      total += this.estimateTools(params.tools);
    }

    return total;
  }

  /**
   * Calculate cost estimate based on token usage
   * Gemini pricing (as of 2026):
   * - Flash: $0.075 per 1M input tokens, $0.30 per 1M output tokens
   * - Pro: $1.25 per 1M input tokens, $5.00 per 1M output tokens
   */
  estimateCost(params: {
    promptTokens: number;
    completionTokens: number;
    model: string;
  }): { inputCostUSD: number; outputCostUSD: number; totalCostUSD: number } {
    const { promptTokens, completionTokens, model } = params;

    let inputCostPer1M = 0.075; // Flash default
    let outputCostPer1M = 0.3;

    if (model.includes('pro')) {
      inputCostPer1M = 1.25;
      outputCostPer1M = 5.0;
    }

    const inputCostUSD = (promptTokens / 1_000_000) * inputCostPer1M;
    const outputCostUSD = (completionTokens / 1_000_000) * outputCostPer1M;
    const totalCostUSD = inputCostUSD + outputCostUSD;

    return { inputCostUSD, outputCostUSD, totalCostUSD };
  }

  /**
   * Free resources
   */
  free(): void {
    if (this.encoder) {
      this.encoder.free();
      this.encoder = null;
    }
  }
}

/**
 * Global token counter instance
 */
export const tokenCounter = new TokenCounter();

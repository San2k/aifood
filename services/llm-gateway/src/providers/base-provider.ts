/**
 * Base Provider Interface
 * Abstract interface for LLM providers
 */

import { ChatCompletionRequest, ChatCompletionResponse } from '../types/openai';

export interface BaseProvider {
  /**
   * Provider name
   */
  readonly name: string;

  /**
   * Send a chat completion request
   * @param request - OpenAI-compatible chat completion request
   * @returns Chat completion response
   */
  chatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse>;

  /**
   * Send a streaming chat completion request
   * @param request - OpenAI-compatible chat completion request
   * @param onChunk - Callback for each streamed chunk
   */
  streamChatCompletion(
    request: ChatCompletionRequest,
    onChunk: (chunk: string) => void
  ): Promise<void>;

  /**
   * Check if the provider is available
   */
  healthCheck(): Promise<boolean>;
}

export abstract class AbstractProvider implements BaseProvider {
  abstract readonly name: string;

  abstract chatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse>;

  abstract streamChatCompletion(
    request: ChatCompletionRequest,
    onChunk: (chunk: string) => void
  ): Promise<void>;

  async healthCheck(): Promise<boolean> {
    try {
      // Simple ping with minimal request
      await this.chatCompletion({
        model: 'test',
        messages: [{ role: 'user', content: 'ping' }],
        max_tokens: 1,
      });
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * Gemini Provider Adapter
 * Translates OpenAI-compatible requests to Gemini OpenAI-compatible API
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { Readable } from 'stream';
import { AbstractProvider } from './base-provider';
import { ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChunk } from '../types/openai';
import { GeminiConfig } from '../types/config';
import { createLogger } from '../services/logger';

const logger = createLogger('gemini-provider');

export class GeminiProvider extends AbstractProvider {
  readonly name = 'gemini';
  private client: AxiosInstance;
  private config: GeminiConfig;
  private retryCount = 0;

  constructor(config: GeminiConfig) {
    super();
    this.config = config;

    this.client = axios.create({
      baseURL: config.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: config.timeout,
    });

    // Add auth header to every request
    this.client.interceptors.request.use((config) => {
      config.headers.Authorization = `Bearer ${this.config.apiKey}`;
      return config;
    });
  }

  async chatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    const geminiRequest = this.translateRequest(request);

    try {
      logger.debug({
        type: 'gemini_request',
        model: geminiRequest.model,
        messageCount: geminiRequest.messages.length,
        temperature: geminiRequest.temperature,
        maxTokens: geminiRequest.max_tokens,
      });

      const startTime = Date.now();
      const response = await this.client.post('/chat/completions', geminiRequest);
      const latency = Date.now() - startTime;

      logger.debug({
        type: 'gemini_response',
        latency,
        statusCode: response.status,
        usage: response.data.usage,
      });

      return this.translateResponse(response.data);

    } catch (error) {
      if (axios.isAxiosError(error)) {
        return this.handleAxiosError(error, request);
      }
      throw error;
    }
  }

  async streamChatCompletion(
    request: ChatCompletionRequest,
    onChunk: (chunk: string) => void
  ): Promise<void> {
    const geminiRequest = {
      ...this.translateRequest(request),
      stream: true,
    };

    try {
      logger.debug({
        type: 'gemini_stream_request',
        model: geminiRequest.model,
      });

      const response = await this.client.post('/chat/completions', geminiRequest, {
        responseType: 'stream',
      });

      const stream = response.data as Readable;
      let buffer = '';

      stream.on('data', (chunk: Buffer) => {
        buffer += chunk.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') continue;

            try {
              const parsed: ChatCompletionChunk = JSON.parse(data);
              const delta = parsed.choices[0]?.delta?.content;
              if (delta) {
                onChunk(delta);
              }
            } catch (parseError) {
              logger.warn({
                type: 'gemini_stream_parse_error',
                error: parseError,
                line,
              });
            }
          }
        }
      });

      await new Promise<void>((resolve, reject) => {
        stream.on('end', () => {
          logger.debug({ type: 'gemini_stream_complete' });
          resolve();
        });
        stream.on('error', reject);
      });

    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw this.createProviderError(error);
      }
      throw error;
    }
  }

  /**
   * Translate OpenAI format request to Gemini OpenAI-compatible format
   */
  private translateRequest(request: ChatCompletionRequest): any {
    // Remove fields that might cause issues
    const translated: any = {
      model: this.normalizeModelName(request.model),
      messages: request.messages,
    };

    // Add optional parameters only if present
    if (request.temperature !== undefined) {
      translated.temperature = request.temperature;
    }

    if (request.max_tokens !== undefined) {
      translated.max_tokens = request.max_tokens;
    }

    if (request.top_p !== undefined) {
      translated.top_p = request.top_p;
    }

    if (request.stop !== undefined) {
      translated.stop = request.stop;
    }

    // Tools: Convert to Gemini format if needed
    if (request.tools && request.tools.length > 0) {
      translated.tools = this.translateTools(request.tools);
    }

    if (request.tool_choice !== undefined) {
      translated.tool_choice = request.tool_choice;
    }

    return translated;
  }

  /**
   * Normalize model name (remove provider prefix if present)
   */
  private normalizeModelName(model: string): string {
    // Remove "google/" prefix if present
    if (model.startsWith('google/')) {
      return model.slice(7);
    }
    // Map logical model names to actual Gemini models
    if (model === 'brief' || model === 'standard') {
      return this.config.model;
    }
    if (model === 'analysis') {
      return 'gemini-1.5-pro';
    }
    return model;
  }

  /**
   * Translate tools to Gemini format
   */
  private translateTools(tools: any[]): any[] {
    return tools.map((tool) => ({
      type: 'function',
      function: {
        name: tool.function.name,
        description: tool.function.description,
        parameters: tool.function.parameters,
      },
    }));
  }

  /**
   * Translate Gemini response to OpenAI format
   */
  private translateResponse(data: any): ChatCompletionResponse {
    // Gemini OpenAI-compatible API should return OpenAI format directly
    return data as ChatCompletionResponse;
  }

  /**
   * Handle axios errors with retry logic
   */
  private async handleAxiosError(
    error: AxiosError,
    request: ChatCompletionRequest
  ): Promise<ChatCompletionResponse> {
    const statusCode = error.response?.status;

    logger.error({
      type: 'gemini_error',
      statusCode,
      message: error.message,
      response: error.response?.data,
    });

    // Retry on rate limit (429) or temporary server errors (502, 503, 504)
    if (
      (statusCode === 429 || statusCode === 502 || statusCode === 503 || statusCode === 504) &&
      this.retryCount < this.config.retries
    ) {
      this.retryCount++;
      const backoffMs = Math.min(1000 * Math.pow(2, this.retryCount), 10000);

      logger.info({
        type: 'gemini_retry',
        attempt: this.retryCount,
        maxRetries: this.config.retries,
        backoffMs,
      });

      await this.sleep(backoffMs);
      return this.chatCompletion(request);
    }

    // Reset retry count
    this.retryCount = 0;

    // Throw user-friendly error
    throw this.createProviderError(error);
  }

  /**
   * Create a user-friendly error from axios error
   */
  private createProviderError(error: AxiosError): Error {
    const statusCode = error.response?.status;
    const responseData = error.response?.data as any;

    let message = 'Gemini API error';

    if (statusCode === 401) {
      message = 'Invalid Gemini API key';
    } else if (statusCode === 429) {
      message = 'Gemini API rate limit exceeded';
    } else if (statusCode === 400) {
      message = `Gemini API bad request: ${responseData?.error?.message || 'Invalid request'}`;
    } else if (statusCode && statusCode >= 500) {
      message = 'Gemini API service unavailable';
    } else if (responseData?.error?.message) {
      message = `Gemini API error: ${responseData.error.message}`;
    }

    const providerError: any = new Error(message);
    providerError.statusCode = statusCode || 500;
    providerError.code = responseData?.error?.code || 'provider_error';

    return providerError;
  }

  /**
   * Sleep for specified milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async healthCheck(): Promise<boolean> {
    try {
      await this.chatCompletion({
        model: this.config.model,
        messages: [{ role: 'user', content: 'ping' }],
        max_tokens: 1,
      });
      return true;
    } catch (error) {
      logger.error({ type: 'gemini_health_check_failed', error });
      return false;
    }
  }
}

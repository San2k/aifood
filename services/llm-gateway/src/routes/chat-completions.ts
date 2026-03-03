/**
 * Chat Completions Route
 * OpenAI-compatible /v1/chat/completions endpoint with token optimization
 */

import { FastifyPluginAsync, FastifyRequest, FastifyReply } from 'fastify';
import { GeminiProvider } from '../providers/gemini-provider';
import { ChatCompletionRequest } from '../types/openai';
import { config } from '../config';
import { createLogger } from '../services/logger';
import { tokenPolicyMiddleware, recordTokenUsage } from '../middleware/token-policy';
import { cacheService } from '../services/cache-service';

const logger = createLogger('chat-completions');

// Initialize provider
const geminiProvider = new GeminiProvider(config.gemini);

export const chatCompletionsRoute: FastifyPluginAsync = async (fastify) => {
  /**
   * POST /v1/chat/completions
   * OpenAI-compatible chat completions endpoint with full optimization pipeline
   */
  fastify.post('/chat/completions', async (request: FastifyRequest, reply: FastifyReply) => {
    const startTime = Date.now();
    const requestId = request.id;

    try {
      const body = request.body as ChatCompletionRequest;

      // Validate request
      if (!body.model || !body.messages || !Array.isArray(body.messages)) {
        reply.status(400).send({
          error: {
            message: 'Invalid request: model and messages are required',
            type: 'invalid_request_error',
          },
        });
        return;
      }

      logger.info({
        type: 'chat_completion_request',
        requestId,
        model: body.model,
        messageCount: body.messages.length,
        stream: body.stream || false,
      });

      // Check cache first (for non-streaming requests)
      if (!body.stream) {
        const cachedResponse = await cacheService.getCached(body);
        if (cachedResponse) {
          const latency = Date.now() - startTime;

          logger.info({
            type: 'chat_completion_cache_hit',
            requestId,
            latency,
            promptTokens: cachedResponse.usage.prompt_tokens,
            completionTokens: cachedResponse.usage.completion_tokens,
            totalTokens: cachedResponse.usage.total_tokens,
          });

          reply.header('X-Cache', 'HIT');
          reply.send(cachedResponse);
          return;
        }

        reply.header('X-Cache', 'MISS');
      }

      // Apply token policy middleware
      // This will: optimize history, enforce output profiles, check quotas
      const policyContext = await tokenPolicyMiddleware(request, reply);

      logger.info({
        type: 'token_policy_applied',
        requestId,
        policyActions: policyContext.policyActions,
        estimatedTokens: policyContext.estimatedTotalTokens,
        tenantId: policyContext.tenantId,
      });

      // Use optimized request
      const optimizedRequest = policyContext.optimizedRequest;

      // Handle streaming
      if (optimizedRequest.stream) {
        reply.raw.writeHead(200, {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        });

        let chunkCount = 0;

        await geminiProvider.streamChatCompletion(optimizedRequest, (chunk) => {
          chunkCount++;
          const sseData = {
            id: `chatcmpl-${requestId}`,
            object: 'chat.completion.chunk',
            created: Math.floor(Date.now() / 1000),
            model: optimizedRequest.model,
            choices: [
              {
                index: 0,
                delta: { content: chunk },
                finish_reason: null,
              },
            ],
          };

          reply.raw.write(`data: ${JSON.stringify(sseData)}\n\n`);
        });

        // Send [DONE] message
        reply.raw.write('data: [DONE]\n\n');
        reply.raw.end();

        const latency = Date.now() - startTime;
        logger.info({
          type: 'chat_completion_stream_complete',
          requestId,
          chunkCount,
          latency,
        });

        // Note: For streaming, we can't easily track actual token usage
        // Using estimated tokens for quota tracking
        await recordTokenUsage(
          policyContext.tenantId,
          optimizedRequest.model,
          policyContext.estimatedPromptTokens,
          optimizedRequest.max_tokens || 1200
        );

        return;
      }

      // Handle non-streaming
      const response = await geminiProvider.chatCompletion(optimizedRequest);

      const latency = Date.now() - startTime;

      logger.info({
        type: 'chat_completion_response',
        requestId,
        latency,
        promptTokens: response.usage.prompt_tokens,
        completionTokens: response.usage.completion_tokens,
        totalTokens: response.usage.total_tokens,
        policyActions: policyContext.policyActions,
      });

      // Record actual token usage for quota tracking
      await recordTokenUsage(
        policyContext.tenantId,
        optimizedRequest.model,
        response.usage.prompt_tokens,
        response.usage.completion_tokens
      );

      // Cache the response (if eligible)
      await cacheService.setCached(body, response);

      reply.send(response);

    } catch (error: any) {
      const latency = Date.now() - startTime;

      logger.error({
        type: 'chat_completion_error',
        requestId,
        latency,
        error: error.message,
        stack: error.stack,
      });

      const statusCode = error.statusCode || 500;
      const errorMessage = error.message || 'Internal server error';

      reply.status(statusCode).send({
        error: {
          message: errorMessage,
          type: error.code || 'internal_error',
        },
      });
    }
  });
};

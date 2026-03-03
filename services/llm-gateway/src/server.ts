/**
 * Fastify Server Setup
 */

import Fastify from 'fastify';
import cors from '@fastify/cors';
import { config } from './config';
import { createLogger } from './services/logger';

const logger = createLogger('server');

export async function createServer() {
  const fastify = Fastify({
    logger: false, // We use our own logger
    requestIdHeader: 'x-request-id',
    requestIdLogLabel: 'requestId',
    disableRequestLogging: false,
    bodyLimit: 10485760, // 10MB
  });

  // CORS support
  await fastify.register(cors, {
    origin: true, // Allow all origins for now
    credentials: true,
  });

  // Request logging middleware
  fastify.addHook('onRequest', async (request, reply) => {
    logger.info({
      type: 'http_request',
      method: request.method,
      url: request.url,
      requestId: request.id,
      userAgent: request.headers['user-agent'],
    });
  });

  // Response logging middleware
  fastify.addHook('onResponse', async (request, reply) => {
    logger.info({
      type: 'http_response',
      method: request.method,
      url: request.url,
      requestId: request.id,
      statusCode: reply.statusCode,
      responseTime: reply.elapsedTime,
    });
  });

  // Global error handler
  fastify.setErrorHandler((error, request, reply) => {
    logger.error({
      type: 'http_error',
      method: request.method,
      url: request.url,
      requestId: request.id,
      error: error.message,
      stack: error.stack,
    });

    // Don't expose internal errors to clients
    const statusCode = error.statusCode || 500;
    const message = statusCode === 500 ? 'Internal server error' : error.message;

    reply.status(statusCode).send({
      error: {
        message,
        type: error.name || 'Error',
        code: error.code,
      },
    });
  });

  // Health check route
  fastify.get('/health', async (request, reply) => {
    return {
      status: 'ok',
      uptime: process.uptime(),
      timestamp: Date.now(),
      version: '1.0.0',
    };
  });

  // Register chat completions route
  const { chatCompletionsRoute } = await import('./routes/chat-completions');
  await fastify.register(chatCompletionsRoute, { prefix: '/v1' });

  return fastify;
}

export async function startServer() {
  const fastify = await createServer();

  try {
    await fastify.listen({
      port: config.server.port,
      host: config.server.host,
    });

    logger.info({
      type: 'server_start',
      message: `LLM Gateway listening on ${config.server.host}:${config.server.port}`,
      port: config.server.port,
      host: config.server.host,
    });

    // Graceful shutdown
    const shutdown = async (signal: string) => {
      logger.info({ type: 'server_shutdown', signal });

      try {
        await fastify.close();
        logger.info({ type: 'server_shutdown_complete' });
        process.exit(0);
      } catch (error) {
        logger.error({ type: 'server_shutdown_error', error });
        process.exit(1);
      }
    };

    process.on('SIGTERM', () => shutdown('SIGTERM'));
    process.on('SIGINT', () => shutdown('SIGINT'));

  } catch (error) {
    logger.error({ type: 'server_start_error', error });
    process.exit(1);
  }

  return fastify;
}

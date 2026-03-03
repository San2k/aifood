/**
 * LLM Gateway Entry Point
 * Self-hosted gateway with token optimization for OpenClaw
 */

import { startServer } from './server';
import { logger } from './services/logger';

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  logger.error({
    type: 'uncaught_exception',
    error: error.message,
    stack: error.stack,
  });
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error({
    type: 'unhandled_rejection',
    reason,
    promise,
  });
  process.exit(1);
});

// Start the server
startServer().catch((error) => {
  logger.error({
    type: 'startup_error',
    error: error.message,
    stack: error.stack,
  });
  process.exit(1);
});

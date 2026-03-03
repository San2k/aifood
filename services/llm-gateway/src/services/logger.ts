/**
 * Logging Service
 * Structured JSON logging with winston
 */

import winston from 'winston';
import { config } from '../config';

const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

/**
 * Create a logger instance with the specified module name
 */
export function createLogger(module: string) {
  return winston.createLogger({
    level: config.observability.logsLevel,
    format: logFormat,
    defaultMeta: { module },
    transports: [
      // Console output
      new winston.transports.Console({
        format: winston.format.combine(
          winston.format.colorize(),
          winston.format.printf(({ timestamp, level, message, module, ...meta }) => {
            const metaStr = Object.keys(meta).length > 0 ? JSON.stringify(meta) : '';
            return `${timestamp} [${level}] [${module}] ${typeof message === 'string' ? message : JSON.stringify(message)} ${metaStr}`;
          })
        ),
      }),

      // File output (JSON format)
      new winston.transports.File({
        filename: 'logs/error.log',
        level: 'error',
        format: logFormat,
      }),

      new winston.transports.File({
        filename: 'logs/combined.log',
        format: logFormat,
      }),
    ],
  });
}

/**
 * Default logger instance
 */
export const logger = createLogger('app');

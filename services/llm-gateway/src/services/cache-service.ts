/**
 * Cache Service
 * Redis-based response caching for deterministic queries
 */

import Redis from 'ioredis';
import { createHash } from 'crypto';
import { ChatCompletionRequest, ChatCompletionResponse } from '../types/openai';
import { config } from '../config';
import { createLogger } from './logger';

const logger = createLogger('cache-service');

export class CacheService {
  private redis: Redis | null = null;
  private cacheHits = 0;
  private cacheMisses = 0;
  private enabled: boolean;

  constructor() {
    this.enabled = config.tokenPolicy.cacheEnabled;

    if (this.enabled) {
      this.redis = new Redis(config.redis.url, {
        maxRetriesPerRequest: 3,
        enableReadyCheck: true,
        retryStrategy(times) {
          const delay = Math.min(times * 50, 2000);
          return delay;
        },
      });

      this.redis.on('connect', () => {
        logger.info({ type: 'cache_connected', url: config.redis.url });
      });

      this.redis.on('error', (error) => {
        logger.error({ type: 'cache_error', error });
      });

      this.redis.on('close', () => {
        logger.warn({ type: 'cache_disconnected' });
      });
    } else {
      logger.info({ type: 'cache_disabled' });
    }
  }

  /**
   * Get cached response for a request
   * Only caches deterministic queries (temperature=0)
   */
  async getCached(request: ChatCompletionRequest): Promise<ChatCompletionResponse | null> {
    if (!this.enabled || !this.redis || !this.shouldCache(request)) {
      return null;
    }

    try {
      const key = this.generateKey(request);
      const cached = await this.redis.get(key);

      if (cached) {
        this.cacheHits++;
        logger.debug({
          type: 'cache_hit',
          key: key.slice(0, 16),
          totalHits: this.cacheHits,
          hitRate: this.getCacheHitRate(),
        });

        return JSON.parse(cached) as ChatCompletionResponse;
      }

      this.cacheMisses++;
      logger.debug({
        type: 'cache_miss',
        key: key.slice(0, 16),
        totalMisses: this.cacheMisses,
      });

      return null;
    } catch (error) {
      logger.error({ type: 'cache_get_error', error });
      return null; // Graceful degradation
    }
  }

  /**
   * Cache a response
   */
  async setCached(
    request: ChatCompletionRequest,
    response: ChatCompletionResponse,
    ttl?: number
  ): Promise<void> {
    if (!this.enabled || !this.redis || !this.shouldCache(request)) {
      return;
    }

    try {
      const key = this.generateKey(request);
      const cacheTTL = ttl || config.tokenPolicy.cacheTTL;

      await this.redis.setex(key, cacheTTL, JSON.stringify(response));

      logger.debug({
        type: 'cache_set',
        key: key.slice(0, 16),
        ttl: cacheTTL,
      });
    } catch (error) {
      logger.error({ type: 'cache_set_error', error });
      // Don't throw - caching is optional
    }
  }

  /**
   * Check if a request should be cached
   * Only cache deterministic queries
   */
  private shouldCache(request: ChatCompletionRequest): boolean {
    // Don't cache streaming requests
    if (request.stream) {
      return false;
    }

    // Only cache deterministic queries (temperature = 0)
    if (request.temperature !== undefined && request.temperature !== 0) {
      return false;
    }

    // Don't cache if tools are present (tool responses are non-deterministic)
    if (request.tools && request.tools.length > 0) {
      return false;
    }

    return true;
  }

  /**
   * Generate cache key from request
   * Uses SHA-256 hash of normalized request
   */
  private generateKey(request: ChatCompletionRequest): string {
    const normalized = {
      model: request.model,
      messages: this.normalizeMessages(request.messages),
      temperature: request.temperature || 0,
      max_tokens: request.max_tokens,
      top_p: request.top_p,
      stop: request.stop,
    };

    const hash = createHash('sha256').update(JSON.stringify(normalized)).digest('hex');

    return `llm_cache:${hash}`;
  }

  /**
   * Normalize messages for consistent hashing
   * Removes non-deterministic fields
   */
  private normalizeMessages(messages: any[]): any[] {
    return messages.map((msg) => ({
      role: msg.role,
      content: msg.content || null,
      name: msg.name || undefined,
    }));
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): {
    hits: number;
    misses: number;
    total: number;
    hitRate: number;
    enabled: boolean;
  } {
    const total = this.cacheHits + this.cacheMisses;
    const hitRate = total > 0 ? this.cacheHits / total : 0;

    return {
      hits: this.cacheHits,
      misses: this.cacheMisses,
      total,
      hitRate,
      enabled: this.enabled,
    };
  }

  /**
   * Get cache hit rate as percentage
   */
  getCacheHitRate(): number {
    const stats = this.getCacheStats();
    return Math.round(stats.hitRate * 100);
  }

  /**
   * Reset cache statistics
   */
  resetStats(): void {
    this.cacheHits = 0;
    this.cacheMisses = 0;
    logger.info({ type: 'cache_stats_reset' });
  }

  /**
   * Invalidate cache entry
   */
  async invalidate(request: ChatCompletionRequest): Promise<void> {
    if (!this.enabled || !this.redis) return;

    try {
      const key = this.generateKey(request);
      await this.redis.del(key);
      logger.debug({ type: 'cache_invalidated', key: key.slice(0, 16) });
    } catch (error) {
      logger.error({ type: 'cache_invalidate_error', error });
    }
  }

  /**
   * Clear all cache entries
   */
  async clearAll(): Promise<void> {
    if (!this.enabled || !this.redis) return;

    try {
      const keys = await this.redis.keys('llm_cache:*');
      if (keys.length > 0) {
        await this.redis.del(...keys);
        logger.info({ type: 'cache_cleared', keysDeleted: keys.length });
      }
    } catch (error) {
      logger.error({ type: 'cache_clear_error', error });
    }
  }

  /**
   * Close Redis connection
   */
  async close(): Promise<void> {
    if (this.redis) {
      await this.redis.quit();
      logger.info({ type: 'cache_closed' });
    }
  }

  /**
   * Check if cache is ready
   */
  async isReady(): Promise<boolean> {
    if (!this.enabled || !this.redis) return false;

    try {
      await this.redis.ping();
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * Global cache service instance
 */
export const cacheService = new CacheService();

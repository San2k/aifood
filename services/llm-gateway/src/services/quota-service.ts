/**
 * Quota Service
 * Tracks and enforces per-tenant token quotas and budgets
 */

import Redis from 'ioredis';
import { config } from '../config';
import { createLogger } from './logger';

const logger = createLogger('quota-service');

export interface QuotaConfig {
  dailyTokens: number;
  monthlyUSD: number;
}

export interface QuotaUsage {
  dailyTokens: number;
  monthlyTokens: number;
  monthlyUSD: number;
  lastReset: Date;
  monthStartDate: Date;
}

export interface QuotaCheckResult {
  allowed: boolean;
  reason?: string;
  usage: QuotaUsage;
  limit: QuotaConfig;
  percentUsed: number;
}

export class QuotaService {
  private redis: Redis;

  constructor() {
    this.redis = new Redis(config.redis.url, {
      maxRetriesPerRequest: 3,
      enableReadyCheck: true,
      retryStrategy(times) {
        const delay = Math.min(times * 50, 2000);
        return delay;
      },
    });

    this.redis.on('connect', () => {
      logger.info({ type: 'quota_redis_connected' });
    });

    this.redis.on('error', (error) => {
      logger.error({ type: 'quota_redis_error', error });
    });
  }

  /**
   * Get quota configuration for a tenant
   */
  async getQuotaConfig(tenantId: string): Promise<QuotaConfig> {
    try {
      const key = `quota:config:${tenantId}`;
      const cached = await this.redis.get(key);

      if (cached) {
        return JSON.parse(cached);
      }

      // Return default quota
      return config.quotas.default;
    } catch (error) {
      logger.error({ type: 'quota_config_error', tenantId, error });
      return config.quotas.default;
    }
  }

  /**
   * Set custom quota configuration for a tenant
   */
  async setQuotaConfig(tenantId: string, quota: QuotaConfig): Promise<void> {
    try {
      const key = `quota:config:${tenantId}`;
      await this.redis.set(key, JSON.stringify(quota));
      logger.info({ type: 'quota_config_updated', tenantId, quota });
    } catch (error) {
      logger.error({ type: 'quota_config_set_error', tenantId, error });
    }
  }

  /**
   * Get current usage for a tenant
   */
  async getUsage(tenantId: string): Promise<QuotaUsage> {
    try {
      const key = `quota:usage:${tenantId}`;
      const cached = await this.redis.hgetall(key);

      if (Object.keys(cached).length === 0) {
        // No usage yet, return zeros
        const now = new Date();
        return {
          dailyTokens: 0,
          monthlyTokens: 0,
          monthlyUSD: 0,
          lastReset: now,
          monthStartDate: this.getMonthStart(now),
        };
      }

      return {
        dailyTokens: parseInt(cached.dailyTokens || '0', 10),
        monthlyTokens: parseInt(cached.monthlyTokens || '0', 10),
        monthlyUSD: parseFloat(cached.monthlyUSD || '0'),
        lastReset: new Date(cached.lastReset || Date.now()),
        monthStartDate: new Date(cached.monthStartDate || Date.now()),
      };
    } catch (error) {
      logger.error({ type: 'quota_usage_get_error', tenantId, error });
      const now = new Date();
      return {
        dailyTokens: 0,
        monthlyTokens: 0,
        monthlyUSD: 0,
        lastReset: now,
        monthStartDate: this.getMonthStart(now),
      };
    }
  }

  /**
   * Check if request is within quota limits
   */
  async checkQuota(tenantId: string, estimatedTokens: number): Promise<QuotaCheckResult> {
    const quota = await this.getQuotaConfig(tenantId);
    const usage = await this.getUsage(tenantId);

    // Check if daily reset is needed
    if (this.shouldResetDaily(usage.lastReset)) {
      await this.resetDailyUsage(tenantId);
      usage.dailyTokens = 0;
    }

    // Check if monthly reset is needed
    if (this.shouldResetMonthly(usage.monthStartDate)) {
      await this.resetMonthlyUsage(tenantId);
      usage.monthlyTokens = 0;
      usage.monthlyUSD = 0;
    }

    // Calculate projected usage
    const projectedDaily = usage.dailyTokens + estimatedTokens;
    const percentUsed = Math.round((usage.dailyTokens / quota.dailyTokens) * 100);

    // Check daily limit
    if (projectedDaily > quota.dailyTokens) {
      logger.warn({
        type: 'quota_exceeded',
        tenantId,
        dailyLimit: quota.dailyTokens,
        currentUsage: usage.dailyTokens,
        estimatedTokens,
        projectedUsage: projectedDaily,
      });

      return {
        allowed: false,
        reason: `Daily token limit exceeded (${usage.dailyTokens}/${quota.dailyTokens} tokens used)`,
        usage,
        limit: quota,
        percentUsed,
      };
    }

    // Check monthly USD budget (approximation based on Flash pricing)
    const projectedMonthlyCost = usage.monthlyUSD + this.estimateCost(estimatedTokens);
    if (projectedMonthlyCost > quota.monthlyUSD) {
      logger.warn({
        type: 'budget_exceeded',
        tenantId,
        monthlyBudget: quota.monthlyUSD,
        currentSpend: usage.monthlyUSD,
        projectedSpend: projectedMonthlyCost,
      });

      return {
        allowed: false,
        reason: `Monthly budget exceeded ($${usage.monthlyUSD.toFixed(2)}/$${quota.monthlyUSD.toFixed(2)} used)`,
        usage,
        limit: quota,
        percentUsed,
      };
    }

    return {
      allowed: true,
      usage,
      limit: quota,
      percentUsed,
    };
  }

  /**
   * Record token usage for a tenant
   */
  async recordUsage(
    tenantId: string,
    promptTokens: number,
    completionTokens: number,
    costUSD: number
  ): Promise<void> {
    try {
      const key = `quota:usage:${tenantId}`;
      const totalTokens = promptTokens + completionTokens;

      // Increment counters atomically
      const pipeline = this.redis.pipeline();
      pipeline.hincrby(key, 'dailyTokens', totalTokens);
      pipeline.hincrby(key, 'monthlyTokens', totalTokens);
      pipeline.hincrbyfloat(key, 'monthlyUSD', costUSD);
      pipeline.hset(key, 'lastReset', new Date().toISOString());

      // Set expiry (keep for 35 days to handle month boundaries)
      pipeline.expire(key, 35 * 24 * 60 * 60);

      await pipeline.exec();

      logger.debug({
        type: 'quota_usage_recorded',
        tenantId,
        promptTokens,
        completionTokens,
        totalTokens,
        costUSD,
      });
    } catch (error) {
      logger.error({
        type: 'quota_usage_record_error',
        tenantId,
        error,
      });
    }
  }

  /**
   * Reset daily usage for a tenant
   */
  private async resetDailyUsage(tenantId: string): Promise<void> {
    try {
      const key = `quota:usage:${tenantId}`;
      await this.redis.hset(key, {
        dailyTokens: '0',
        lastReset: new Date().toISOString(),
      });

      logger.info({ type: 'quota_daily_reset', tenantId });
    } catch (error) {
      logger.error({ type: 'quota_daily_reset_error', tenantId, error });
    }
  }

  /**
   * Reset monthly usage for a tenant
   */
  private async resetMonthlyUsage(tenantId: string): Promise<void> {
    try {
      const key = `quota:usage:${tenantId}`;
      const now = new Date();

      await this.redis.hset(key, {
        monthlyTokens: '0',
        monthlyUSD: '0',
        monthStartDate: this.getMonthStart(now).toISOString(),
      });

      logger.info({ type: 'quota_monthly_reset', tenantId });
    } catch (error) {
      logger.error({ type: 'quota_monthly_reset_error', tenantId, error });
    }
  }

  /**
   * Check if daily reset is needed (after midnight UTC)
   */
  private shouldResetDaily(lastReset: Date): boolean {
    const now = new Date();
    const lastResetDay = lastReset.getUTCDate();
    const currentDay = now.getUTCDate();

    return currentDay !== lastResetDay;
  }

  /**
   * Check if monthly reset is needed
   */
  private shouldResetMonthly(monthStartDate: Date): boolean {
    const now = new Date();
    const currentMonthStart = this.getMonthStart(now);

    return currentMonthStart.getTime() > monthStartDate.getTime();
  }

  /**
   * Get the start of the current month (UTC)
   */
  private getMonthStart(date: Date): Date {
    return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1, 0, 0, 0, 0));
  }

  /**
   * Estimate cost in USD for token usage
   * Using Gemini Flash pricing: $0.075/1M input, $0.30/1M output
   */
  private estimateCost(tokens: number): number {
    // Conservative estimate: assume 50/50 split between input/output
    const inputTokens = tokens * 0.5;
    const outputTokens = tokens * 0.5;

    const inputCost = (inputTokens / 1_000_000) * 0.075;
    const outputCost = (outputTokens / 1_000_000) * 0.3;

    return inputCost + outputCost;
  }

  /**
   * Get quota statistics for all tenants
   */
  async getAllUsageStats(): Promise<
    Array<{
      tenantId: string;
      usage: QuotaUsage;
      quota: QuotaConfig;
      percentUsed: number;
    }>
  > {
    try {
      const keys = await this.redis.keys('quota:usage:*');
      const stats = [];

      for (const key of keys) {
        const tenantId = key.replace('quota:usage:', '');
        const usage = await this.getUsage(tenantId);
        const quota = await this.getQuotaConfig(tenantId);
        const percentUsed = Math.round((usage.dailyTokens / quota.dailyTokens) * 100);

        stats.push({ tenantId, usage, quota, percentUsed });
      }

      return stats;
    } catch (error) {
      logger.error({ type: 'quota_stats_error', error });
      return [];
    }
  }

  /**
   * Close Redis connection
   */
  async close(): Promise<void> {
    await this.redis.quit();
    logger.info({ type: 'quota_redis_closed' });
  }
}

/**
 * Global quota service instance
 */
export const quotaService = new QuotaService();

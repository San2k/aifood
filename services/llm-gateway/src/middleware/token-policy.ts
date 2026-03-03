/**
 * Token Policy Middleware
 * Applies token optimization policies to requests
 */

import { FastifyRequest, FastifyReply } from 'fastify';
import { ChatCompletionRequest } from '../types/openai';
import { OutputProfile } from '../types/config';
import { tokenCounter } from '../services/token-counter';
import { HistoryManager } from '../services/history-manager';
import { quotaService } from '../services/quota-service';
import { config } from '../config';
import { createLogger } from '../services/logger';

const logger = createLogger('token-policy');

// Create history manager instance
const historyManager = new HistoryManager(tokenCounter);

export interface TokenPolicyContext {
  tenantId: string; // Extracted from auth header or default
  requestId: string;
  originalRequest: ChatCompletionRequest;
  optimizedRequest: ChatCompletionRequest;
  policyActions: string[];
  estimatedPromptTokens: number;
  estimatedTotalTokens: number;
  quotaCheck: {
    allowed: boolean;
    reason?: string;
    percentUsed: number;
  };
}

/**
 * Extract tenant ID from request
 * Can be from Authorization header, API key, or default to 'default'
 */
function extractTenantId(request: FastifyRequest): string {
  // Try to extract from Authorization header
  const authHeader = request.headers.authorization;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    const token = authHeader.slice(7);
    // In production, decode JWT or validate API key to get tenant ID
    // For now, use a simple hash
    return `tenant_${Buffer.from(token).toString('base64').slice(0, 16)}`;
  }

  // Default tenant
  return 'default';
}

/**
 * Get output profile from model name or request
 */
function getOutputProfile(model: string): OutputProfile {
  if (model.includes('brief')) {
    return OutputProfile.BRIEF;
  }
  if (model.includes('analysis') || model.includes('long')) {
    return OutputProfile.LONG;
  }
  return OutputProfile.STANDARD;
}

/**
 * Enforce output profile limits
 */
function enforceOutputProfile(
  request: ChatCompletionRequest,
  profile: OutputProfile
): ChatCompletionRequest {
  const maxTokens = config.tokenPolicy.outputProfiles[profile];

  // Clone request
  const optimized = { ...request };

  // Override max_tokens if excessive or not set
  if (!optimized.max_tokens || optimized.max_tokens > maxTokens) {
    optimized.max_tokens = maxTokens;
  }

  // For brief profile, reduce temperature for more focused responses
  if (profile === OutputProfile.BRIEF && (!optimized.temperature || optimized.temperature > 0.5)) {
    optimized.temperature = 0.3;
  }

  return optimized;
}

/**
 * Token Policy Middleware
 * Applies optimization policies before sending to LLM
 */
export async function tokenPolicyMiddleware(
  request: FastifyRequest,
  reply: FastifyReply
): Promise<TokenPolicyContext> {
  const startTime = Date.now();
  const body = request.body as ChatCompletionRequest;
  const requestId = request.id;
  const tenantId = extractTenantId(request);

  logger.debug({
    type: 'token_policy_start',
    requestId,
    tenantId,
    model: body.model,
    messageCount: body.messages?.length || 0,
  });

  const policyActions: string[] = [];
  let optimizedRequest = { ...body };

  // Step 1: Output Profile Enforcement
  const profile = getOutputProfile(body.model);
  optimizedRequest = enforceOutputProfile(optimizedRequest, profile);
  policyActions.push(`output_profile_${profile}`);

  logger.debug({
    type: 'output_profile_applied',
    profile,
    maxTokens: optimizedRequest.max_tokens,
  });

  // Step 2: History Management (Sliding Window + Summarization)
  if (optimizedRequest.messages && optimizedRequest.messages.length > 3) {
    try {
      const historyResult = await historyManager.applyPolicy(optimizedRequest.messages, {
        windowTokens: config.tokenPolicy.historyWindowTokens,
        windowMessages: config.tokenPolicy.historyWindowMessages,
        summaryTrigger: config.tokenPolicy.summaryTriggerTokens,
        summaryTarget: config.tokenPolicy.summaryTargetTokens,
      });

      optimizedRequest.messages = historyResult.messages;
      policyActions.push(...historyResult.actions);

      logger.info({
        type: 'history_optimization_applied',
        requestId,
        tokensBefore: historyResult.tokensBefore,
        tokensAfter: historyResult.tokensAfter,
        tokensSaved: historyResult.tokensSaved,
        actions: historyResult.actions,
      });
    } catch (error) {
      logger.error({
        type: 'history_optimization_error',
        requestId,
        error,
        message: 'Failed to optimize history, using original messages',
      });
      // Continue with original messages if optimization fails
    }
  }

  // Step 3: Token Estimation
  const estimatedPromptTokens = tokenCounter.estimatePromptTokens({
    messages: optimizedRequest.messages,
    tools: optimizedRequest.tools,
  });

  const estimatedOutputTokens = optimizedRequest.max_tokens || 1200;
  const estimatedTotalTokens = estimatedPromptTokens + estimatedOutputTokens;

  logger.debug({
    type: 'token_estimation',
    requestId,
    promptTokens: estimatedPromptTokens,
    outputTokens: estimatedOutputTokens,
    totalTokens: estimatedTotalTokens,
  });

  // Step 4: Quota Check
  const quotaCheck = await quotaService.checkQuota(tenantId, estimatedTotalTokens);

  if (!quotaCheck.allowed) {
    logger.warn({
      type: 'quota_limit_exceeded',
      requestId,
      tenantId,
      reason: quotaCheck.reason,
      percentUsed: quotaCheck.percentUsed,
    });

    reply.status(429).send({
      error: {
        message: quotaCheck.reason || 'Quota exceeded',
        type: 'quota_exceeded',
        code: 'rate_limit_exceeded',
      },
    });

    throw new Error(quotaCheck.reason); // Stop processing
  }

  // Warn if approaching limit (>80%)
  if (quotaCheck.percentUsed > 80) {
    logger.warn({
      type: 'quota_warning',
      requestId,
      tenantId,
      percentUsed: quotaCheck.percentUsed,
      usage: quotaCheck.usage.dailyTokens,
      limit: quotaCheck.limit.dailyTokens,
    });
  }

  const latency = Date.now() - startTime;

  logger.info({
    type: 'token_policy_complete',
    requestId,
    tenantId,
    policyActions,
    estimatedPromptTokens,
    estimatedTotalTokens,
    quotaAllowed: quotaCheck.allowed,
    quotaPercentUsed: quotaCheck.percentUsed,
    latencyMs: latency,
  });

  return {
    tenantId,
    requestId,
    originalRequest: body,
    optimizedRequest,
    policyActions,
    estimatedPromptTokens,
    estimatedTotalTokens,
    quotaCheck: {
      allowed: quotaCheck.allowed,
      reason: quotaCheck.reason,
      percentUsed: quotaCheck.percentUsed,
    },
  };
}

/**
 * Record actual token usage after LLM response
 */
export async function recordTokenUsage(
  tenantId: string,
  model: string,
  promptTokens: number,
  completionTokens: number
): Promise<void> {
  try {
    // Calculate cost
    const cost = tokenCounter.estimateCost({
      promptTokens,
      completionTokens,
      model,
    });

    // Record in quota service
    await quotaService.recordUsage(tenantId, promptTokens, completionTokens, cost.totalCostUSD);

    logger.debug({
      type: 'token_usage_recorded',
      tenantId,
      promptTokens,
      completionTokens,
      totalTokens: promptTokens + completionTokens,
      costUSD: cost.totalCostUSD,
    });
  } catch (error) {
    logger.error({
      type: 'token_usage_record_error',
      tenantId,
      error,
    });
  }
}

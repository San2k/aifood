/**
 * History Manager Service
 * Manages conversation history with sliding window and summarization
 */

import { ChatMessage } from '../types/openai';
import { TokenCounter } from './token-counter';
import { GeminiProvider } from '../providers/gemini-provider';
import { config } from '../config';
import { createLogger } from './logger';

const logger = createLogger('history-manager');

export interface HistoryPolicy {
  windowTokens: number; // Max tokens in history window
  windowMessages: number; // Max messages to keep
  summaryTrigger: number; // Trigger summarization at N tokens
  summaryTarget: number; // Compress summary to N tokens
}

export interface HistoryOptimizationResult {
  messages: ChatMessage[];
  actions: string[]; // Actions taken (e.g., 'trimmed_5_messages', 'summarized')
  tokensBefore: number; // Token count before optimization
  tokensAfter: number; // Token count after optimization
  tokensSaved: number; // Tokens saved
}

export class HistoryManager {
  private tokenCounter: TokenCounter;
  private geminiProvider: GeminiProvider;

  constructor(tokenCounter: TokenCounter) {
    this.tokenCounter = tokenCounter;
    this.geminiProvider = new GeminiProvider(config.gemini);
  }

  /**
   * Apply history optimization policy
   */
  async applyPolicy(
    messages: ChatMessage[],
    policy: HistoryPolicy
  ): Promise<HistoryOptimizationResult> {
    const actions: string[] = [];
    const tokensBefore = this.tokenCounter.countMessages(messages);
    let optimizedMessages = [...messages];

    logger.debug({
      type: 'history_optimization_start',
      messageCount: messages.length,
      tokensBefore,
      policy,
    });

    // Step 1: Sliding window - keep only last N messages
    if (optimizedMessages.length > policy.windowMessages) {
      const trimmed = optimizedMessages.length - policy.windowMessages;
      optimizedMessages = optimizedMessages.slice(-policy.windowMessages);
      actions.push(`trimmed_${trimmed}_messages`);

      logger.info({
        type: 'history_trimmed',
        trimmedCount: trimmed,
        remainingCount: optimizedMessages.length,
      });
    }

    // Step 2: Check token count after trimming
    const tokensAfterTrimming = this.tokenCounter.countMessages(optimizedMessages);

    // Step 3: Summarization if still over trigger threshold
    if (tokensAfterTrimming > policy.summaryTrigger && optimizedMessages.length > 3) {
      try {
        // Keep last 3 messages intact (recent context is important)
        const messagesToSummarize = optimizedMessages.slice(0, -3);
        const recentMessages = optimizedMessages.slice(-3);

        logger.info({
          type: 'history_summarization_start',
          messagesToSummarize: messagesToSummarize.length,
          recentMessagesKept: recentMessages.length,
          tokensBeforeSummarization: tokensAfterTrimming,
        });

        const summary = await this.summarizeHistory(messagesToSummarize, policy.summaryTarget);

        // Create summary message
        const summaryMessage: ChatMessage = {
          role: 'system',
          content: `Previous conversation summary (${messagesToSummarize.length} messages compressed):\n\n${summary}`,
        };

        optimizedMessages = [summaryMessage, ...recentMessages];
        actions.push('summarized');

        logger.info({
          type: 'history_summarization_complete',
          summaryTokens: this.tokenCounter.count(summary),
          finalMessageCount: optimizedMessages.length,
        });
      } catch (error) {
        logger.error({
          type: 'history_summarization_error',
          error,
          message: 'Failed to summarize history, keeping original messages',
        });
        // Keep original messages if summarization fails
      }
    }

    const tokensAfter = this.tokenCounter.countMessages(optimizedMessages);
    const tokensSaved = tokensBefore - tokensAfter;

    logger.info({
      type: 'history_optimization_complete',
      actions,
      tokensBefore,
      tokensAfter,
      tokensSaved,
      savingsPercent: Math.round((tokensSaved / tokensBefore) * 100),
    });

    return {
      messages: optimizedMessages,
      actions,
      tokensBefore,
      tokensAfter,
      tokensSaved,
    };
  }

  /**
   * Summarize conversation history
   */
  private async summarizeHistory(messages: ChatMessage[], targetTokens: number): Promise<string> {
    // Build conversation text for summarization
    const conversationText = messages
      .map((msg) => {
        const role = msg.role === 'user' ? 'User' : msg.role === 'assistant' ? 'Assistant' : 'System';
        return `${role}: ${msg.content || '[no content]'}`;
      })
      .join('\n\n');

    // Summarization prompt
    const summaryPrompt = `You are a conversation summarizer. Summarize the following conversation in approximately ${targetTokens} tokens or less.

Include:
- Main topics discussed
- Important facts, numbers, and decisions
- User goals or constraints mentioned
- Key entities (people, places, things) defined

Be concise but preserve critical information.

Conversation:
${conversationText}

Summary:`;

    try {
      const response = await this.geminiProvider.chatCompletion({
        model: config.gemini.model, // Use brief model for summarization
        messages: [
          {
            role: 'user',
            content: summaryPrompt,
          },
        ],
        temperature: 0.3, // Low temperature for consistent summaries
        max_tokens: targetTokens + 100, // Allow some buffer
      });

      const summary = response.choices[0]?.message?.content || '';

      if (!summary) {
        throw new Error('Empty summary received from LLM');
      }

      return summary.trim();
    } catch (error) {
      logger.error({
        type: 'summarization_api_error',
        error,
      });
      throw error;
    }
  }

  /**
   * Extract system instructions from messages
   * (useful for separating system context from conversation)
   */
  extractSystemMessages(messages: ChatMessage[]): {
    systemMessages: ChatMessage[];
    conversationMessages: ChatMessage[];
  } {
    const systemMessages = messages.filter((msg) => msg.role === 'system');
    const conversationMessages = messages.filter((msg) => msg.role !== 'system');

    return { systemMessages, conversationMessages };
  }

  /**
   * Merge system messages into a single system instruction
   */
  mergeSystemMessages(systemMessages: ChatMessage[]): string {
    return systemMessages.map((msg) => msg.content || '').join('\n\n');
  }

  /**
   * Calculate history statistics
   */
  getHistoryStats(messages: ChatMessage[]): {
    totalMessages: number;
    userMessages: number;
    assistantMessages: number;
    systemMessages: number;
    totalTokens: number;
    averageTokensPerMessage: number;
  } {
    const totalMessages = messages.length;
    const userMessages = messages.filter((m) => m.role === 'user').length;
    const assistantMessages = messages.filter((m) => m.role === 'assistant').length;
    const systemMessages = messages.filter((m) => m.role === 'system').length;
    const totalTokens = this.tokenCounter.countMessages(messages);
    const averageTokensPerMessage = totalMessages > 0 ? Math.round(totalTokens / totalMessages) : 0;

    return {
      totalMessages,
      userMessages,
      assistantMessages,
      systemMessages,
      totalTokens,
      averageTokensPerMessage,
    };
  }
}

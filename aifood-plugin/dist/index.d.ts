/**
 * AiFood OpenClaw Plugin
 * Nutrition tracking plugin
 */
import type { PluginConfig } from './types/index.js';
interface PluginCommandContext {
    senderId?: string;
    channel: string;
    isAuthorizedSender: boolean;
    args?: string;
}
interface PluginCommandResult {
    text?: string;
    markdown?: string;
}
interface OpenClawPluginApi {
    config: PluginConfig;
    pluginConfig: PluginConfig;
    logger: {
        info: (msg: string) => void;
        error: (msg: string, err?: unknown) => void;
    };
    registerTool(tool: any, options?: {
        optional?: boolean;
    }): void;
    registerCommand(command: {
        name: string;
        description: string;
        acceptsArgs?: boolean;
        requireAuth?: boolean;
        handler: (ctx: PluginCommandContext) => PluginCommandResult | Promise<PluginCommandResult>;
    }): void;
}
declare const _default: {
    id: string;
    name: string;
    configSchema: {
        type: string;
        properties: {
            databaseUrl: {
                type: string;
                description: string;
                default: string;
            };
            agentApiUrl: {
                type: string;
                description: string;
                default: string;
            };
        };
    };
    register(api: OpenClawPluginApi): Promise<void>;
};
export default _default;
//# sourceMappingURL=index.d.ts.map
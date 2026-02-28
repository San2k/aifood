/**
 * AiFood OpenClaw Plugin
 * Nutrition tracking plugin
 */
import type { PluginConfig } from './types/index.js';
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
        };
    };
    register(api: OpenClawPluginApi): Promise<void>;
};
export default _default;
//# sourceMappingURL=index.d.ts.map
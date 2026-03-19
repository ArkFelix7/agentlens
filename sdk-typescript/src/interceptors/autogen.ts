/** AutoGen instrumentation for the AgentLens TypeScript SDK.
 *
 * AutoGen's JavaScript API (`@microsoft/autogen`) is in early preview and does
 * not yet have a stable patching surface. This module exists for API symmetry
 * with the Python SDK. When a stable JS AutoGen API is available, this will be
 * implemented in a future release.
 *
 * For now, instrumentAutoGen() is a no-op that emits a console warning.
 * If you are using AutoGen in Python, use the Python SDK:
 *   from agentlens_sdk.interceptors.autogen_interceptor import instrument_autogen
 */

export function instrumentAutoGen(): void {
  console.warn(
    '[AgentLens] instrumentAutoGen() is not yet supported in Node.js. ' +
    'AutoGen JS instrumentation is planned for a future release. ' +
    'For Python AutoGen, use the agentlens-sdk Python package instead.',
  );
}

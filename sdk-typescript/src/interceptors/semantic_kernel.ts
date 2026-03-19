/** Semantic Kernel instrumentation for the AgentLens TypeScript SDK.
 *
 * The Semantic Kernel JavaScript SDK (`@microsoft/semantic-kernel`) is in early
 * preview and does not yet expose a stable filter/middleware API comparable to
 * the Python SDK's FilterTypes.FUNCTION_INVOCATION.
 *
 * When a stable filter API becomes available, this interceptor will be
 * implemented. For now, instrumentSemanticKernel() is a no-op that emits a
 * console warning.
 *
 * For Python Semantic Kernel, use the Python SDK:
 *   from agentlens_sdk.interceptors.semantic_kernel_interceptor import instrument_semantic_kernel
 */

export function instrumentSemanticKernel(): void {
  console.warn(
    '[AgentLens] instrumentSemanticKernel() is not yet supported in Node.js. ' +
    'Semantic Kernel JS instrumentation is planned for a future release. ' +
    'For Python Semantic Kernel, use the agentlens-sdk Python package instead.',
  );
}

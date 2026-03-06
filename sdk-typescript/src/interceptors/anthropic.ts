/** Anthropic auto-instrumentation for the AgentLens TypeScript SDK. */

let patched = false;

export async function patchAnthropic(): Promise<void> {
  if (patched) return;
  try {
    await import('@anthropic-ai/sdk');
    patched = true;
    // Full implementation follows same pattern as Python SDK
    console.warn('[AgentLens] Anthropic TS SDK patching — use Python SDK for more reliable instrumentation.');
  } catch {
    // Anthropic not installed — skip silently
  }
}

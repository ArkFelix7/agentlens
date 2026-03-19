/** CrewAI instrumentation stub for the AgentLens TypeScript SDK.
 *
 * CrewAI is a Python-only framework. This module exists for API symmetry with
 * the Python SDK. In a Node.js/TypeScript environment, instrumentCrewAI() is a
 * no-op that emits a console warning.
 *
 * If you are running CrewAI agents in Python, use the Python SDK:
 *   from agentlens_sdk.interceptors.crewai_interceptor import instrument_crewai
 */

export function instrumentCrewAI(): void {
  console.warn(
    '[AgentLens] instrumentCrewAI() is not supported in Node.js. ' +
    'CrewAI is a Python-only framework. Use the agentlens-sdk Python package instead.',
  );
}

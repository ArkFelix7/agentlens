/** VS Code command registrations for AgentLens extension. */

import * as vscode from 'vscode';
import { AgentLensClient } from './client';
import { TracePanelProvider } from './tracePanel';
import { CostDecorationProvider } from './decorations';

export function registerCommands(
  context: vscode.ExtensionContext,
  client: AgentLensClient,
  panelProvider: TracePanelProvider,
  decorationProvider: CostDecorationProvider,
  statusBar: vscode.StatusBarItem,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand('agentlens.showLastTrace', async () => {
      const sessions = await client.getSessions(1);
      if (!sessions.length) {
        vscode.window.showInformationMessage('AgentLens: No sessions found. Run your agent first.');
        return;
      }
      const s = sessions[0];
      const score = await client.getScore(s.id);
      const scoreStr = score ? ` · Score: ${score.score}/100 (${score.grade})` : '';
      vscode.window.showInformationMessage(
        `Last session: ${s.agent_name} · ${s.total_events} events · $${s.total_cost_usd.toFixed(4)}${scoreStr}`
      );
    }),

    vscode.commands.registerCommand('agentlens.openDashboard', () => {
      const config = vscode.workspace.getConfiguration('agentlens');
      const url = config.get<string>('serverUrl', 'http://localhost:8766');
      vscode.env.openExternal(vscode.Uri.parse(url));
    }),

    vscode.commands.registerCommand('agentlens.toggleCostAnnotations', () => {
      const config = vscode.workspace.getConfiguration('agentlens');
      const current = config.get<boolean>('showCostAnnotations', true);
      config.update('showCostAnnotations', !current, vscode.ConfigurationTarget.Global).then(undefined, () => undefined);
      decorationProvider.setEnabled(!current);
      vscode.window.showInformationMessage(
        `AgentLens: Cost annotations ${!current ? 'enabled' : 'disabled'}`
      );
    }),

    vscode.commands.registerCommand('agentlens.connect', async () => {
      const input = await vscode.window.showInputBox({
        prompt: 'AgentLens server URL',
        value: vscode.workspace.getConfiguration('agentlens').get<string>('serverUrl', 'http://localhost:8766'),
      });
      if (!input) { return; }
      client.setBaseUrl(input);
      vscode.workspace.getConfiguration('agentlens')
        .update('serverUrl', input, vscode.ConfigurationTarget.Global)
        .then(undefined, () => undefined);
      const healthy = await client.isHealthy();
      if (healthy) {
        statusBar.text = '$(pulse) AgentLens';
        statusBar.backgroundColor = undefined;
        vscode.window.showInformationMessage('AgentLens: Connected to server.');
        panelProvider.refresh().catch(() => undefined);
      } else {
        statusBar.text = '$(warning) AgentLens';
        vscode.window.showWarningMessage('AgentLens: Could not reach server at ' + input);
      }
    }),
  );
}

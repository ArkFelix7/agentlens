/** AgentLens VS Code extension — activate/deactivate lifecycle. */

import * as vscode from 'vscode';
import { AgentLensClient } from './client';
import { TracePanelProvider } from './tracePanel';
import { CostDecorationProvider } from './decorations';
import { registerCommands } from './commands';

export function activate(context: vscode.ExtensionContext): void {
  const config = vscode.workspace.getConfiguration('agentlens');
  const serverUrl = config.get<string>('serverUrl', 'http://localhost:8766');
  const autoConnect = config.get<boolean>('autoConnect', true);
  const showAnnotations = config.get<boolean>('showCostAnnotations', true);

  const client = new AgentLensClient(serverUrl);

  // Status bar item
  const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBar.text = '$(pulse) AgentLens';
  statusBar.tooltip = 'AgentLens — AI Agent Observability';
  statusBar.command = 'agentlens.showLastTrace';
  statusBar.show();
  context.subscriptions.push(statusBar);

  // Sidebar panel
  const panelProvider = new TracePanelProvider(context.extensionUri, client);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(TracePanelProvider.viewType, panelProvider)
  );

  // Cost decorations
  const decorationProvider = new CostDecorationProvider(client, showAnnotations);
  context.subscriptions.push({ dispose: () => decorationProvider.dispose() });

  // Register commands
  registerCommands(context, client, panelProvider, decorationProvider, statusBar);

  // Config change listener
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration(e => {
      if (e.affectsConfiguration('agentlens.serverUrl')) {
        const newUrl = vscode.workspace.getConfiguration('agentlens').get<string>('serverUrl', 'http://localhost:8766');
        client.setBaseUrl(newUrl);
        panelProvider.refresh().catch(() => undefined);
      }
      if (e.affectsConfiguration('agentlens.showCostAnnotations')) {
        const enabled = vscode.workspace.getConfiguration('agentlens').get<boolean>('showCostAnnotations', true);
        decorationProvider.setEnabled(enabled);
      }
    })
  );

  // Auto-connect health check
  if (autoConnect) {
    client.isHealthy().then(healthy => {
      if (!healthy) {
        statusBar.text = '$(warning) AgentLens';
        statusBar.tooltip = 'AgentLens: Server offline — run `agentlens-server` to start';
      }
    }).catch(() => undefined);
  }
}

export function deactivate(): void {
  // Timers are cleaned up via WebviewView.onDidDispose subscriptions
}

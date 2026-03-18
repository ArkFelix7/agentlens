/** Webview sidebar panel — shows sessions and trace events from AgentLens server. */

import * as vscode from 'vscode';
import { AgentLensClient, Session } from './client';

function escHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export class TracePanelProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = 'agentlens.tracePanel';
  private _view?: vscode.WebviewView;
  private _client: AgentLensClient;
  private _refreshTimer?: ReturnType<typeof setInterval>;

  constructor(private readonly _extensionUri: vscode.Uri, client: AgentLensClient) {
    this._client = client;
  }

  resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ): void {
    this._view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri],
    };
    webviewView.webview.html = this._getBaseHtml('Connecting...');

    webviewView.webview.onDidReceiveMessage((msg: { command: string }) => {
      if (msg.command === 'refresh') { this.refresh(); }
      if (msg.command === 'openDashboard') {
        vscode.env.openExternal(vscode.Uri.parse(this._client.baseUrl));
      }
    });

    this.refresh();
    this._refreshTimer = setInterval(() => { this.refresh(); }, 10000);
    webviewView.onDidDispose(() => {
      if (this._refreshTimer !== undefined) { clearInterval(this._refreshTimer); }
    });
  }

  async refresh(): Promise<void> {
    if (!this._view) { return; }
    const healthy = await this._client.isHealthy();
    if (!healthy) {
      this._view.webview.html = this._getBaseHtml('', true);
      return;
    }
    const sessions = await this._client.getSessions(10);
    this._view.webview.html = this._getSessionsHtml(sessions);
  }

  private _getSessionsHtml(sessions: Session[]): string {
    const rows = sessions.length === 0
      ? '<p style="color:#666;font-size:12px;padding:8px">No sessions yet. Run your agent to see traces.</p>'
      : sessions.map(s => {
          const cost = s.total_cost_usd > 0 ? `$${s.total_cost_usd.toFixed(4)}` : '—';
          const statusColor = s.status === 'active' ? '#22c55e' : s.status === 'error' ? '#ef4444' : '#6366f1';
          const time = new Date(s.started_at).toLocaleTimeString();
          return `
            <div style="padding:6px 8px;border-bottom:1px solid #1e1e2e;cursor:pointer"
                 onclick="openDashboard()" title="Open dashboard for ${escHtml(s.id)}">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="color:#e2e8f0;font-size:12px;font-weight:500">${escHtml(s.agent_name)}</span>
                <span style="color:${statusColor};font-size:10px">${escHtml(s.status)}</span>
              </div>
              <div style="display:flex;justify-content:space-between;margin-top:2px">
                <span style="color:#64748b;font-size:10px">${s.total_events} events · ${cost}</span>
                <span style="color:#64748b;font-size:10px">${time}</span>
              </div>
            </div>`;
        }).join('');

    return this._getBaseHtml(rows);
  }

  private _getBaseHtml(content: string, disconnected = false): string {
    const body = disconnected
      ? `<div style="padding:16px;text-align:center">
           <div style="color:#ef4444;font-size:12px;margin-bottom:8px">Server offline</div>
           <div style="color:#64748b;font-size:11px">Start with: agentlens-server</div>
           <button onclick="refresh()" style="margin-top:8px;padding:4px 12px;background:#6366f1;color:white;border:none;border-radius:4px;cursor:pointer;font-size:11px">Retry</button>
         </div>`
      : content;

    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0a0a0f; color: #e2e8f0; font-family: 'JetBrains Mono', monospace; font-size: 12px; }
  .toolbar { display: flex; justify-content: space-between; align-items: center; padding: 6px 8px; border-bottom: 1px solid #1e1e2e; }
  .toolbar span { color: #6366f1; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; }
  button { background: none; border: 1px solid #6366f1; color: #6366f1; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 10px; }
  button:hover { background: #6366f120; }
</style>
</head>
<body>
<div class="toolbar">
  <span>AGENTLENS</span>
  <div>
    <button onclick="openDashboard()">Dashboard</button>
    <button onclick="refresh()" style="margin-left:4px">Refresh</button>
  </div>
</div>
${body}
<script>
const vscode = acquireVsCodeApi();
function refresh() { vscode.postMessage({ command: 'refresh' }); }
function openDashboard() { vscode.postMessage({ command: 'openDashboard' }); }
</script>
</body>
</html>`;
  }
}

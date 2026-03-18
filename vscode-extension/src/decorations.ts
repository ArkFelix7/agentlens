/** Inline cost + latency text decorations for @trace decorated functions. */

import * as vscode from 'vscode';
import { AgentLensClient, TraceEvent } from './client';

export class CostDecorationProvider {
  private _decorationType: vscode.TextEditorDecorationType;
  private _client: AgentLensClient;
  private _enabled: boolean;

  constructor(client: AgentLensClient, enabled: boolean) {
    this._client = client;
    this._enabled = enabled;
    this._decorationType = vscode.window.createTextEditorDecorationType({
      after: {
        margin: '0 0 0 2em',
        color: new vscode.ThemeColor('editorCodeLens.foreground'),
        fontStyle: 'italic',
      },
    });
  }

  setEnabled(enabled: boolean): void {
    this._enabled = enabled;
    if (!enabled) { this._clearAll(); }
  }

  async updateDecorations(editor: vscode.TextEditor, sessionId: string): Promise<void> {
    if (!this._enabled) { return; }
    const events = await this._client.getSessionEvents(sessionId);
    if (!events.length) { return; }

    const decorations: vscode.DecorationOptions[] = [];
    const doc = editor.document;

    for (let i = 0; i < doc.lineCount; i++) {
      const line = doc.lineAt(i);
      const text = line.text;
      if (!/@trace|@observe/.test(text)) { continue; }

      // Find the function name on the next non-empty line
      let fnName = '';
      for (let j = i + 1; j < Math.min(i + 3, doc.lineCount); j++) {
        const m = doc.lineAt(j).text.match(/(?:async\s+)?def\s+(\w+)|(?:async\s+)?function\s+(\w+)|const\s+(\w+)/);
        if (m) { fnName = m[1] ?? m[2] ?? m[3] ?? ''; break; }
      }
      if (!fnName) { continue; }

      const matching = events.filter((e: TraceEvent) =>
        e.event_name === fnName || e.event_name.includes(fnName)
      );
      if (!matching.length) { continue; }

      const last = matching[matching.length - 1];
      const cost = last.cost_usd > 0 ? ` $${last.cost_usd.toFixed(4)}` : '';
      const latency = last.duration_ms > 0 ? ` ${last.duration_ms.toFixed(0)}ms` : '';
      const totalTokens = (last.tokens_input ?? 0) + (last.tokens_output ?? 0);
      const tokens = totalTokens > 0 ? ` ${totalTokens}tok` : '';

      decorations.push({
        range: line.range,
        renderOptions: {
          after: { contentText: `⟨${fnName}${latency}${cost}${tokens}⟩` },
        },
      });
    }

    editor.setDecorations(this._decorationType, decorations);
  }

  private _clearAll(): void {
    vscode.window.visibleTextEditors.forEach(ed =>
      ed.setDecorations(this._decorationType, [])
    );
  }

  dispose(): void {
    this._decorationType.dispose();
  }
}

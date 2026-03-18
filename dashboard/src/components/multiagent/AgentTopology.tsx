/** D3 hierarchical tree layout showing multi-agent session topology (F9). */

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Session } from '@/types';

interface AgentTopologyProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
}

interface TopoNode {
  id: string;
  agent_name: string;
  agent_role: string | null;
  status: string;
  total_cost_usd: number;
  total_events: number;
  children: TopoNode[];
}

function buildTree(sessions: Session[]): TopoNode[] {
  const byId = new Map<string, TopoNode>();
  sessions.forEach(s => {
    byId.set(s.id, {
      id: s.id,
      agent_name: s.agent_name,
      agent_role: s.agent_role ?? null,
      status: s.status,
      total_cost_usd: s.total_cost_usd,
      total_events: s.total_events,
      children: [],
    });
  });

  const roots: TopoNode[] = [];
  sessions.forEach(s => {
    const node = byId.get(s.id)!;
    if (s.parent_session_id && byId.has(s.parent_session_id)) {
      byId.get(s.parent_session_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  });
  return roots;
}

const STATUS_COLORS: Record<string, string> = {
  active: '#22c55e',
  completed: '#6366f1',
  error: '#ef4444',
};

export function AgentTopology({ sessions, activeSessionId, onSelectSession }: AgentTopologyProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const roots = buildTree(sessions);
    if (!roots.length || !svgRef.current || !containerRef.current) return;

    const width = containerRef.current.clientWidth || 600;
    const height = 260;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    const g = svg.append('g').attr('transform', 'translate(40,20)');

    // Build single synthetic root if multiple roots
    const treeRoot = roots.length === 1
      ? d3.hierarchy(roots[0], d => d.children)
      : d3.hierarchy({ id: '__root__', agent_name: '', agent_role: null, status: 'completed', total_cost_usd: 0, total_events: 0, children: roots } as TopoNode, d => d.children);

    const treeLayout = d3.tree<TopoNode>().size([width - 80, height - 60]);
    const treeData = treeLayout(treeRoot);

    // Links
    g.selectAll('.topo-link')
      .data(treeData.links())
      .enter()
      .append('path')
      .attr('class', 'topo-link')
      .attr('d', d3.linkVertical<d3.HierarchyPointLink<TopoNode>, d3.HierarchyPointNode<TopoNode>>()
        .x(d => d.x)
        .y(d => d.y) as (d: d3.HierarchyPointLink<TopoNode>) => string)
      .attr('fill', 'none')
      .attr('stroke', '#1e1e2e')
      .attr('stroke-width', 2);

    // Nodes
    const node = g.selectAll('.topo-node')
      .data(treeData.descendants().filter(d => d.data.id !== '__root__'))
      .enter()
      .append('g')
      .attr('class', 'topo-node')
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .style('cursor', 'pointer')
      .on('click', (_e, d) => onSelectSession(d.data.id));

    node.append('circle')
      .attr('r', 22)
      .attr('fill', '#0a0a0f')
      .attr('stroke', d => d.data.id === activeSessionId ? '#6366f1' : (STATUS_COLORS[d.data.status] ?? '#64748b'))
      .attr('stroke-width', d => d.data.id === activeSessionId ? 3 : 1.5);

    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-4')
      .attr('fill', '#e2e8f0')
      .attr('font-size', '9px')
      .attr('font-family', 'JetBrains Mono, monospace')
      .text(d => d.data.agent_name.slice(0, 8));

    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '8')
      .attr('fill', '#64748b')
      .attr('font-size', '8px')
      .attr('font-family', 'JetBrains Mono, monospace')
      .text(d => d.data.agent_role ?? '');

    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '19')
      .attr('fill', '#64748b')
      .attr('font-size', '8px')
      .attr('font-family', 'JetBrains Mono, monospace')
      .text(d => `$${d.data.total_cost_usd.toFixed(3)}`);

  }, [sessions, activeSessionId, onSelectSession]);

  const roots = buildTree(sessions);
  if (!roots.length) return null;

  return (
    <div ref={containerRef} className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg overflow-hidden">
      <div className="px-3 py-1.5 border-b border-[var(--border-subtle)]">
        <span className="text-xs font-mono text-[var(--text-tertiary)] uppercase tracking-widest">Agent Topology</span>
      </div>
      <svg ref={svgRef} className="w-full" style={{ minHeight: 200 }} />
    </div>
  );
}

/** D3.js force-directed graph visualization of trace events. */

import React, { useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';
import { TraceEvent, EventType } from '@/types';
import { GraphData, D3Node, D3Link } from '@/types/trace';

const EVENT_COLORS: Record<EventType, string> = {
  llm_call: '#a855f7',
  tool_call: '#06b6d4',
  decision: '#f59e0b',
  memory_read: '#6366f1',
  memory_write: '#6366f1',
  user_input: '#10b981',
  error: '#ef4444',
};

/** Return node radius for sizing (used for arrowhead offset too). */
function nodeRadius(d: D3Node): number {
  const tokens = d.event.tokens_input + d.event.tokens_output;
  return Math.max(16, Math.min(32, 16 + tokens / 500));
}

/** Append the correct SVG shape for the given event type to a D3 selection. */
function appendNodeShape(
  selection: d3.Selection<SVGGElement, D3Node, SVGGElement, unknown>,
  selectedEventId: string | null,
) {
  // Circles: llm_call, user_input, error (default)
  selection
    .filter((d) => ['llm_call', 'user_input', 'error'].includes(d.event.event_type))
    .append('circle')
    .attr('r', nodeRadius)
    .attr('fill', (d) => `${EVENT_COLORS[d.event.event_type] || '#6b6b80'}25`)
    .attr('stroke', (d) => EVENT_COLORS[d.event.event_type] || '#6b6b80')
    .attr('stroke-width', (d) => d.id === selectedEventId ? 3 : 1.5)
    .attr('filter', (d) => d.id === selectedEventId ? 'url(#glow)' : null);

  // Rounded rect: tool_call
  selection
    .filter((d) => d.event.event_type === 'tool_call')
    .append('rect')
    .attr('x', (d) => -nodeRadius(d))
    .attr('y', (d) => -nodeRadius(d) * 0.7)
    .attr('width', (d) => nodeRadius(d) * 2)
    .attr('height', (d) => nodeRadius(d) * 1.4)
    .attr('rx', 6)
    .attr('ry', 6)
    .attr('fill', (d) => `${EVENT_COLORS[d.event.event_type]}25`)
    .attr('stroke', (d) => EVENT_COLORS[d.event.event_type])
    .attr('stroke-width', (d) => d.id === selectedEventId ? 3 : 1.5)
    .attr('filter', (d) => d.id === selectedEventId ? 'url(#glow)' : null);

  // Diamond: decision
  selection
    .filter((d) => d.event.event_type === 'decision')
    .append('polygon')
    .attr('points', (d) => {
      const r = nodeRadius(d);
      return `0,${-r} ${r},0 0,${r} ${-r},0`;
    })
    .attr('fill', (d) => `${EVENT_COLORS[d.event.event_type]}25`)
    .attr('stroke', (d) => EVENT_COLORS[d.event.event_type])
    .attr('stroke-width', (d) => d.id === selectedEventId ? 3 : 1.5)
    .attr('filter', (d) => d.id === selectedEventId ? 'url(#glow)' : null);

  // Hexagon: memory_read, memory_write
  selection
    .filter((d) => ['memory_read', 'memory_write'].includes(d.event.event_type))
    .append('polygon')
    .attr('points', (d) => {
      const r = nodeRadius(d);
      const angles = [0, 60, 120, 180, 240, 300].map((a) => (a * Math.PI) / 180);
      return angles.map((a) => `${r * Math.cos(a)},${r * Math.sin(a)}`).join(' ');
    })
    .attr('fill', (d) => `${EVENT_COLORS[d.event.event_type]}25`)
    .attr('stroke', (d) => EVENT_COLORS[d.event.event_type])
    .attr('stroke-width', (d) => d.id === selectedEventId ? 3 : 1.5)
    .attr('filter', (d) => d.id === selectedEventId ? 'url(#glow)' : null);
}

interface TraceGraphProps {
  graphData: GraphData;
  selectedEventId: string | null;
  onSelectEvent: (id: string) => void;
}

export function TraceGraph({ graphData, selectedEventId, onSelectEvent }: TraceGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<d3.Simulation<D3Node, D3Link> | null>(null);

  const renderGraph = useCallback(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { nodes, links } = graphData;
    if (nodes.length === 0) return;

    const width = svgRef.current.clientWidth || 800;
    const height = svgRef.current.clientHeight || 600;

    // Container group with zoom
    const g = svg.append('g').attr('class', 'graph-container');

    svg.call(
      d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform.toString());
        }) as unknown as (selection: d3.Selection<SVGSVGElement, unknown, null, undefined>) => void
    );

    // Defs: arrowhead + glow filter
    const defs = svg.append('defs');

    defs.append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', 'var(--border-default)');

    const filter = defs.append('filter').attr('id', 'glow');
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Force simulation
    const simulation = d3.forceSimulation<D3Node>(nodes)
      .force('link', d3.forceLink<D3Node, D3Link>(links).id((d) => d.id).distance(90))
      .force('charge', d3.forceManyBody().strength(-220))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(38));

    simulationRef.current = simulation;

    // Links
    const link = g.append('g').selectAll<SVGLineElement, D3Link>('line')
      .data(links)
      .join('line')
      .attr('stroke', 'var(--border-default)')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 1.5)
      .attr('marker-end', 'url(#arrowhead)');

    // Node groups
    const node = g.append('g').selectAll<SVGGElement, D3Node>('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node')
      .style('cursor', 'pointer')
      .call(
        d3.drag<SVGGElement, D3Node>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      )
      .on('click', (_event, d) => {
        onSelectEvent(d.id);
      });

    // Append shape based on event type
    appendNodeShape(node, selectedEventId);

    // Node labels
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('fill', (d) => EVENT_COLORS[d.event.event_type] || '#6b6b80')
      .attr('font-size', '9px')
      .attr('font-family', 'JetBrains Mono, monospace')
      .attr('font-weight', '600')
      .text((d) => d.event.event_name.slice(0, 8));

    // Tooltip title
    node.append('title').text((d) => `${d.event.event_type}: ${d.event.event_name}`);

    // Tick handler
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as D3Node).x || 0)
        .attr('y1', (d) => (d.source as D3Node).y || 0)
        .attr('x2', (d) => (d.target as D3Node).x || 0)
        .attr('y2', (d) => (d.target as D3Node).y || 0);

      node.attr('transform', (d) => `translate(${d.x || 0},${d.y || 0})`);
    });
  }, [graphData, selectedEventId, onSelectEvent]);

  useEffect(() => {
    renderGraph();
    return () => {
      simulationRef.current?.stop();
    };
  }, [renderGraph]);

  return (
    <svg
      ref={svgRef}
      className="trace-graph w-full h-full"
      style={{ background: 'transparent' }}
      role="img"
      aria-label="Trace event graph"
    />
  );
}

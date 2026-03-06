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

    // Arrow marker for links
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', 'var(--border-default)');

    // Force simulation
    const simulation = d3.forceSimulation<D3Node>(nodes)
      .force('link', d3.forceLink<D3Node, D3Link>(links).id((d) => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(35));

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

    // Node circles
    node.append('circle')
      .attr('r', (d) => {
        // Node size proportional to token cost, min 16, max 32
        const tokens = d.event.tokens_input + d.event.tokens_output;
        return Math.max(16, Math.min(32, 16 + tokens / 500));
      })
      .attr('fill', (d) => `${EVENT_COLORS[d.event.event_type] || '#6b6b80'}25`)
      .attr('stroke', (d) => EVENT_COLORS[d.event.event_type] || '#6b6b80')
      .attr('stroke-width', (d) => d.id === selectedEventId ? 3 : 1.5)
      .attr('filter', (d) => d.id === selectedEventId ? 'url(#glow)' : null);

    // Glow filter for selected node
    const defs = svg.select('defs');
    const filter = defs.append('filter').attr('id', 'glow');
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

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

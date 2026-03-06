// Trace-specific D3 graph types

import { TraceEvent } from './index';

export interface D3Node extends d3.SimulationNodeDatum {
  id: string;
  event: TraceEvent;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  source: string | D3Node;
  target: string | D3Node;
  id: string;
}

export interface GraphData {
  nodes: D3Node[];
  links: D3Link[];
}

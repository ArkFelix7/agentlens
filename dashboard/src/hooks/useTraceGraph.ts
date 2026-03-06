/** D3 graph data transformation hook. Converts flat trace events to graph nodes/links. */

import { useMemo } from 'react';
import { TraceEvent } from '@/types';
import { GraphData, D3Node, D3Link } from '@/types/trace';

export function useTraceGraph(events: TraceEvent[]): GraphData {
  return useMemo(() => {
    const nodes: D3Node[] = events.map((event) => ({
      id: event.id,
      event,
    }));

    const links: D3Link[] = events
      .filter((e) => e.parent_event_id)
      .map((e) => ({
        id: `${e.parent_event_id}-${e.id}`,
        source: e.parent_event_id as string,
        target: e.id,
      }))
      .filter((l) => events.some((e) => e.id === l.source));

    return { nodes, links };
  }, [events]);
}

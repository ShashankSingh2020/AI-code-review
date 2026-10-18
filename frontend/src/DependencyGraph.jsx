import React, { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

export default function DependencyGraph({ dependencies = [] }) {
  // Convert dependency edges into unique React Flow nodes and edges
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodeSet = new Set();
    const edges = [];

    dependencies.forEach((dep, idx) => {
      nodeSet.add(dep.source_node);
      nodeSet.add(dep.target_node);

      edges.push({
        id: `e-${idx}`,
        source: dep.source_node,
        target: dep.target_node,
        label: dep.edge_type || 'imports',
        animated: true,
        style: { stroke: '#6366f1', strokeWidth: 1.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#6366f1',
        },
      });
    });

    const nodesList = Array.from(nodeSet);
    const cols = Math.ceil(Math.sqrt(nodesList.length)) || 1;

    const nodes = nodesList.map((nodeName, index) => {
      const isInternal = nodeName.includes('.');
      const col = index % cols;
      const row = Math.floor(index / cols);

      return {
        id: nodeName,
        position: { x: col * 260 + 50, y: row * 120 + 50 },
        data: { label: nodeName },
        style: {
          background: isInternal ? '#1e1b4b' : '#0f172a',
          color: isInternal ? '#a5b4fc' : '#e2e8f0',
          border: isInternal ? '1px solid #6366f1' : '1px solid #334155',
          borderRadius: '8px',
          padding: '8px 14px',
          fontSize: '12px',
          fontWeight: '500',
          fontFamily: 'monospace',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
        },
      };
    });

    return { initialNodes: nodes, initialEdges: edges };
  }, [dependencies]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  if (!dependencies || dependencies.length === 0) {
    return (
      <div className="h-96 flex items-center justify-center text-slate-500 text-sm font-sans">
        No dependency connections available for this codebase.
      </div>
    );
  }

  return (
    <div className="w-full h-[500px] bg-slate-950 rounded-xl border border-slate-800 overflow-hidden relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <Background color="#334155" gap={18} size={1} />
        <Controls className="bg-slate-900 border border-slate-800 text-white fill-white rounded-lg shadow-lg" />
        <MiniMap
          nodeStrokeColor="#6366f1"
          nodeColor="#1e1b4b"
          maskColor="rgba(11, 15, 25, 0.7)"
          className="bg-slate-900 border border-slate-800 rounded-lg"
        />
      </ReactFlow>
    </div>
  );
}
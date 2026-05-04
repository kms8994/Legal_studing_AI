"use client";

import { useEffect, useMemo, useState } from "react";
import ELK from "elkjs/lib/elk.bundled.js";
import {
  Background,
  Controls,
  MarkerType,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";

type DiagramNodeData = {
  title: string;
  detail: string;
  tone: "partyA" | "partyB" | "event" | "issue" | "rule" | "apply" | "decision";
};

type ParsedDiagram = {
  nodes: Node<DiagramNodeData>[];
  edges: Edge[];
};

const elk = new ELK();

const nodeTypes = {
  legal: LegalNode,
};

export default function ReactFlowDiagram({ code }: { code: string }) {
  const parsed = useMemo(() => parseMermaidFlow(code), [code]);
  const [nodes, setNodes] = useState(parsed.nodes);
  const [edges, setEdges] = useState(parsed.edges);

  useEffect(() => {
    let cancelled = false;
    layoutDiagram(parsed).then((layouted) => {
      if (!cancelled) {
        setNodes(layouted.nodes);
        setEdges(layouted.edges);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [parsed]);

  return (
    <div className="flow-diagram" aria-label="사건 구조 다이어그램">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.45}
        maxZoom={1.6}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
      >
        <Background color="#d8e0ec" gap={24} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

function LegalNode({ data }: NodeProps<Node<DiagramNodeData>>) {
  return (
    <div className={`legal-node ${data.tone}`}>
      <strong>{data.title}</strong>
      {data.detail && <span>{data.detail}</span>}
    </div>
  );
}

async function layoutDiagram(parsed: ParsedDiagram): Promise<ParsedDiagram> {
  const graph = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "DOWN",
      "elk.spacing.nodeNode": "52",
      "elk.layered.spacing.nodeNodeBetweenLayers": "76",
      "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
    },
    children: parsed.nodes.map((node) => ({
      id: node.id,
      width: 190,
      height: node.data.detail ? 74 : 52,
    })),
    edges: parsed.edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  const layouted = await elk.layout(graph);
  const nodeMap = new Map(layouted.children?.map((node) => [node.id, node]) ?? []);
  return {
    nodes: parsed.nodes.map((node) => {
      const layoutNode = nodeMap.get(node.id);
      return {
        ...node,
        position: {
          x: layoutNode?.x ?? node.position.x,
          y: layoutNode?.y ?? node.position.y,
        },
      };
    }),
    edges: parsed.edges,
  };
}

function parseMermaidFlow(code: string): ParsedDiagram {
  const nodeMap = new Map<string, Node<DiagramNodeData>>();
  const edges: Edge[] = [];
  const nodePattern = /([A-Za-z][\w-]*)\s*\["([\s\S]*?)"\](?:::([\w-]+))?/g;

  let nodeMatch: RegExpExecArray | null;
  while ((nodeMatch = nodePattern.exec(code)) !== null) {
    const id = nodeMatch[1];
    const label = decodeLabel(nodeMatch[2]);
    const [title, ...detail] = label.split(/\s*<br\/?>\s*/);
    nodeMap.set(id, {
      id,
      type: "legal",
      position: { x: 0, y: nodeMap.size * 96 },
      data: {
        title: stripHtml(title),
        detail: stripHtml(detail.join(" ")),
        tone: toTone(nodeMatch[3]),
      },
    });
  }

  for (const line of code.split(/\r?\n/)) {
    const parsedEdge = parseEdgeLine(line);
    if (!parsedEdge) continue;
    const { source, label, target } = parsedEdge;
    ensureNode(nodeMap, source);
    ensureNode(nodeMap, target);
    edges.push({
      id: `${source}-${target}-${edges.length}`,
      source,
      target,
      label,
      type: "smoothstep",
      markerEnd: { type: MarkerType.ArrowClosed, color: "#64748b" },
      style: { stroke: "#64748b", strokeWidth: 1.8 },
      labelStyle: { fill: "#0f172a", fontSize: 12, fontWeight: 800 },
      labelBgPadding: [0, 0],
      labelBgBorderRadius: 0,
      labelBgStyle: { fill: "transparent", fillOpacity: 0 },
    });
  }

  return {
    nodes: Array.from(nodeMap.values()),
    edges,
  };
}

function parseEdgeLine(line: string) {
  const cleaned = line.trim();
  if (!cleaned || cleaned.startsWith("flowchart") || cleaned.startsWith("classDef") || cleaned.startsWith("class ")) {
    return null;
  }

  const arrowMatch = cleaned.match(/^(.*?)\s*(?:-->|---|==>|-.->)\s*(.*)$/);
  if (!arrowMatch) return null;

  const source = extractNodeId(arrowMatch[1]);
  let rest = arrowMatch[2].trim();
  let label = "";
  const labelMatch = rest.match(/^\|([^|]+)\|\s*(.*)$/);
  if (labelMatch) {
    label = stripHtml(decodeLabel(labelMatch[1]));
    rest = labelMatch[2].trim();
  }
  const target = extractNodeId(rest);
  if (!source || !target || source === target) return null;
  return { source, label, target };
}

function extractNodeId(value: string) {
  const match = value.trim().match(/^([A-Za-z][\w-]*)/);
  return match?.[1] ?? "";
}

function ensureNode(nodeMap: Map<string, Node<DiagramNodeData>>, id: string) {
  if (!nodeMap.has(id)) {
    nodeMap.set(id, {
      id,
      type: "legal",
      position: { x: 0, y: nodeMap.size * 96 },
      data: { title: id, detail: "", tone: "event" },
    });
  }
}

function toTone(value?: string): DiagramNodeData["tone"] {
  if (value === "partyA" || value === "partyB" || value === "issue" || value === "rule" || value === "apply" || value === "decision") {
    return value;
  }
  return "event";
}

function decodeLabel(value: string) {
  return value.replace(/&quot;/g, "\"").replace(/&#39;/g, "'");
}

function stripHtml(value: string) {
  return value.replace(/<\/?[^>]+>/g, "").trim();
}

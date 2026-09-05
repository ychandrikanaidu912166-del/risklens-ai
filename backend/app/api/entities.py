"""Entity subgraph endpoint.

Given an entity (customer / device / ip / merchant), returns the ego-graph
of transactions connecting it — neighbouring entities and edges. Used by the
Investigation Detail page to visualise relationships.

The graph is built on-the-fly from the transactions table (no separate edge
store yet). Depth is limited to keep the payload small.
"""
from __future__ import annotations

from typing import Dict, List, Literal, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db import models
from backend.app.db.database import get_db

router = APIRouter(prefix="/entities", tags=["entities"])

EntityType = Literal["customer", "device", "ip", "merchant"]


class Node(BaseModel):
    id: str
    type: EntityType
    label: str
    risk_hint: str = "neutral"     # neutral | warning | high
    meta: Dict[str, str] = {}


class Edge(BaseModel):
    source: str
    target: str
    weight: int = 1
    label: str = ""


class Subgraph(BaseModel):
    root: Node
    nodes: List[Node]
    edges: List[Edge]
    stats: Dict[str, int]


def _key(t: EntityType, i: str) -> str:
    return f"{t}:{i}"


def _tx_matches(db: Session, entity_type: EntityType, entity_id: str) -> List[models.Transaction]:
    col = {
        "customer": models.Transaction.customer_id,
        "device": models.Transaction.device_id,
        "ip": models.Transaction.ip_hash,
        "merchant": models.Transaction.merchant_id,
    }[entity_type]
    stmt = select(models.Transaction).where(col == entity_id).limit(500)
    return list(db.scalars(stmt).all())


def _neighbours_for_txs(txs: List[models.Transaction]) -> Tuple[Dict[str, Node], List[Edge]]:
    nodes: Dict[str, Node] = {}
    edges: List[Edge] = []
    seen_edges: Set[Tuple[str, str, str]] = set()

    for tx in txs:
        parts = [
            ("customer", tx.customer_id, f"Customer {tx.customer_id}"),
            ("device", tx.device_id, f"Device {tx.device_id}"),
            ("ip", tx.ip_hash, f"IP {tx.ip_hash[:12]}…"),
            ("merchant", tx.merchant_id, f"Merchant {tx.merchant_id}"),
        ]
        for t, i, label in parts:
            k = _key(t, i)
            if k not in nodes:
                nodes[k] = Node(id=k, type=t, label=label)  # type: ignore[arg-type]
        # Fully connect the four entities on this transaction.
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                a = _key(parts[i][0], parts[i][1])  # type: ignore[arg-type]
                b = _key(parts[j][0], parts[j][1])  # type: ignore[arg-type]
                pair = tuple(sorted([a, b]))
                edge_key = (pair[0], pair[1], "tx")
                if edge_key in seen_edges:
                    # bump weight of an existing edge
                    for e in edges:
                        if {e.source, e.target} == {a, b}:
                            e.weight += 1
                            break
                    continue
                seen_edges.add(edge_key)
                edges.append(Edge(source=pair[0], target=pair[1], weight=1, label="tx"))
    return nodes, edges


@router.get("/{entity_type}/{entity_id}/subgraph", response_model=Subgraph)
def get_subgraph(
    entity_type: EntityType,
    entity_id: str,
    db: Session = Depends(get_db),
    depth: int = Query(default=1, ge=1, le=2),
) -> Subgraph:
    root_txs = _tx_matches(db, entity_type, entity_id)
    if not root_txs and entity_type == "customer":
        if db.get(models.Customer, entity_id) is None:
            raise HTTPException(status_code=404, detail=f"customer {entity_id} not found")
    nodes, edges = _neighbours_for_txs(root_txs)
    root_key = _key(entity_type, entity_id)
    if root_key not in nodes:
        nodes[root_key] = Node(id=root_key, type=entity_type, label=f"{entity_type} {entity_id}")

    # Depth-2 expansion: for each neighbour of a *different* type, pull a few of
    # its own transactions and merge.
    if depth >= 2:
        for k, n in list(nodes.items()):
            if k == root_key:
                continue
            more_txs = _tx_matches(db, n.type, n.id.split(":", 1)[1])[:100]
            more_nodes, more_edges = _neighbours_for_txs(more_txs)
            for mk, mn in more_nodes.items():
                nodes.setdefault(mk, mn)
            existing_pairs = {frozenset([e.source, e.target]) for e in edges}
            for e in more_edges:
                if frozenset([e.source, e.target]) not in existing_pairs:
                    edges.append(e)

    # Simple risk hint: nodes with degree >= 4 in the ego graph are visually flagged
    # as connectors ("hubs") — often a fraud-ring indicator.
    degree: Dict[str, int] = {n.id: 0 for n in nodes.values()}
    for e in edges:
        degree[e.source] += e.weight
        degree[e.target] += e.weight
    for n in nodes.values():
        if n.id == root_key:
            n.risk_hint = "root"
        elif degree.get(n.id, 0) >= 6:
            n.risk_hint = "high"
        elif degree.get(n.id, 0) >= 3:
            n.risk_hint = "warning"

    return Subgraph(
        root=nodes[root_key],
        nodes=list(nodes.values()),
        edges=edges,
        stats={
            "n_transactions": len(root_txs),
            "n_nodes": len(nodes),
            "n_edges": len(edges),
        },
    )

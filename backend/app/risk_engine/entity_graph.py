from typing import List, Dict, Any, Set
from collections import defaultdict


class EntityGraphService:
    """
    In-memory / relational entity graph correlating Customers, Devices, IPs, Merchants, and Transactions.
    Discovers multi-accounting rings, shared hardware, and bot proxy clusters.
    """

    def __init__(self):
        self.device_to_customers: Dict[str, Set[str]] = defaultdict(set)
        self.ip_to_customers: Dict[str, Set[str]] = defaultdict(set)
        self.customer_to_devices: Dict[str, Set[str]] = defaultdict(set)
        self.customer_to_ips: Dict[str, Set[str]] = defaultdict(set)
        self.customer_to_transactions: Dict[str, List[str]] = defaultdict(list)
        self.merchant_to_transactions: Dict[str, List[str]] = defaultdict(list)
        self.device_to_transactions: Dict[str, List[str]] = defaultdict(list)
        self.ip_to_transactions: Dict[str, List[str]] = defaultdict(list)

    def register_transaction(self, tx: Dict[str, Any]):
        txn_id = tx.get("transaction_id", "")
        cust_id = tx.get("customer_id", "")
        dev_id = tx.get("device_id", "")
        ip_addr = tx.get("ip_address", "")
        merch_id = tx.get("merchant_id", "")

        if cust_id:
            if dev_id:
                self.device_to_customers[dev_id].add(cust_id)
                self.customer_to_devices[cust_id].add(dev_id)
            if ip_addr:
                self.ip_to_customers[ip_addr].add(cust_id)
                self.customer_to_ips[cust_id].add(ip_addr)
            self.customer_to_transactions[cust_id].append(txn_id)

        if merch_id:
            self.merchant_to_transactions[merch_id].append(txn_id)
        if dev_id:
            self.device_to_transactions[dev_id].append(txn_id)
        if ip_addr:
            self.ip_to_transactions[ip_addr].append(txn_id)

    def analyze_entity_correlations(self, tx: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyzes infrastructure sharing and returns structured risk signals.
        """
        signals = []
        cust_id = tx.get("customer_id", "")
        dev_id = tx.get("device_id", "")
        ip_addr = tx.get("ip_address", "")

        # 1. Device Shared Across Multiple Customer Accounts (Syndicate / Device Farm)
        linked_custs_dev = list(self.device_to_customers.get(dev_id, set()))
        other_custs_on_dev = [c for c in linked_custs_dev if c != cust_id]
        if len(other_custs_on_dev) >= 2:
            signals.append({
                "type": "SHARED_DEVICE_SYNDICATE",
                "severity": "CRITICAL" if len(other_custs_on_dev) >= 3 else "HIGH",
                "description": f"Device fingerprint '{dev_id}' is shared across {len(linked_custs_dev)} distinct customer accounts ({', '.join(other_custs_on_dev[:3])}).",
                "observed_value": f"{len(linked_custs_dev)} accounts on single device",
                "baseline_value": "1 account per device",
                "related_entities": [dev_id] + linked_custs_dev[:4],
            })

        # 2. IP Address Shared Across Excessive Accounts
        linked_custs_ip = list(self.ip_to_customers.get(ip_addr, set()))
        other_custs_on_ip = [c for c in linked_custs_ip if c != cust_id]
        if len(other_custs_on_ip) >= 4:
            signals.append({
                "type": "HIGH_DENSITY_IP_CLUSTER",
                "severity": "MEDIUM",
                "description": f"IP address '{ip_addr}' has routed payments for {len(linked_custs_ip)} accounts, indicating a shared VPN/proxy or commercial gateway.",
                "observed_value": f"{len(linked_custs_ip)} accounts on IP",
                "baseline_value": "1 - 2 accounts per residential IP",
                "related_entities": [ip_addr] + linked_custs_ip[:3],
            })

        return signals

    def get_entity_graph_for_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds a node-edge graph structure suitable for frontend visualization.
        """
        txn_id = tx.get("transaction_id", "txn_current")
        cust_id = tx.get("customer_id", "cust_unknown")
        dev_id = tx.get("device_id", "dev_unknown")
        ip_addr = tx.get("ip_address", "ip_unknown")
        merch_id = tx.get("merchant_id", "merch_unknown")

        nodes = [
            {"id": txn_id, "label": txn_id, "type": "transaction", "risk": "target"},
            {"id": cust_id, "label": cust_id, "type": "customer", "risk": "neutral"},
            {"id": dev_id, "label": dev_id, "type": "device", "risk": "neutral"},
            {"id": ip_addr, "label": ip_addr, "type": "ip", "risk": "neutral"},
            {"id": merch_id, "label": merch_id, "type": "merchant", "risk": "neutral"},
        ]

        edges = [
            {"source": cust_id, "target": txn_id, "label": "initiated"},
            {"source": dev_id, "target": txn_id, "label": "used_by"},
            {"source": ip_addr, "target": txn_id, "label": "routed_via"},
            {"source": txn_id, "target": merch_id, "label": "paid_to"},
        ]

        # Add other accounts linked to same device
        other_custs_dev = [c for c in self.device_to_customers.get(dev_id, set()) if c != cust_id]
        for other_c in other_custs_dev[:4]:
            nodes.append({"id": other_c, "label": other_c, "type": "customer", "risk": "suspicious"})
            edges.append({"source": dev_id, "target": other_c, "label": "also_used_by"})

        # Add other accounts linked to same IP
        other_custs_ip = [c for c in self.ip_to_customers.get(ip_addr, set()) if c != cust_id and c not in other_custs_dev]
        for other_cip in other_custs_ip[:3]:
            nodes.append({"id": other_cip, "label": other_cip, "type": "customer", "risk": "warning"})
            edges.append({"source": ip_addr, "target": other_cip, "label": "shared_ip"})

        return {"nodes": nodes, "edges": edges}


# Global singleton instance
entity_graph = EntityGraphService()

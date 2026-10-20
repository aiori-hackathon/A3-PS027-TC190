"""
Dependency Graph Builder & Aggregator
Transforms raw browser network requests into an interactive Directed Acyclic Graph (DAG)
and prepares assets for multi-stage protocol diagnostics.
"""

from urllib.parse import urlparse
from typing import Dict, Any, List, Set
from ..config import RESOURCE_CRITICALITY_WEIGHTS

class DependencyGraphBuilder:
    """Builds structured node-edge dependency graph and groups resources by domain."""

    @classmethod
    def build_graph(cls, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts crawl requests into graph format (nodes and edges)
        and domain-level grouping.
        """
        target_url = crawl_data["target_url"]
        apex_domain = crawl_data["apex_domain"]
        requests = crawl_data.get("requests", [])

        # Apex root node
        nodes: List[Dict[str, Any]] = [
            {
                "id": f"root_{apex_domain}",
                "label": apex_domain,
                "url": target_url,
                "domain": apex_domain,
                "type": "root",
                "is_first_party": True,
                "criticality": 1.0,
                "is_root": True
            }
        ]
        edges: List[Dict[str, Any]] = []

        seen_domains: Set[str] = {apex_domain}
        domain_groups: Dict[str, Dict[str, Any]] = {
            apex_domain: {
                "domain": apex_domain,
                "is_first_party": True,
                "resource_count": 0,
                "resources": []
            }
        }

        # Process each intercepted request
        for req in requests:
            req_id = req["id"]
            req_url = req["url"]
            req_domain = req["domain"]
            res_type = req["resource_type"] or "other"
            is_first_party = req["is_first_party"]
            criticality = RESOURCE_CRITICALITY_WEIGHTS.get(res_type, 0.2)

            # Ensure domain group exists
            if req_domain not in domain_groups:
                domain_groups[req_domain] = {
                    "domain": req_domain,
                    "is_first_party": is_first_party,
                    "resource_count": 0,
                    "resources": []
                }

            domain_groups[req_domain]["resource_count"] += 1
            domain_groups[req_domain]["resources"].append(req)

            # Add domain node if new
            domain_node_id = f"domain_{req_domain}"
            if req_domain not in seen_domains:
                seen_domains.add(req_domain)
                nodes.append({
                    "id": domain_node_id,
                    "label": req_domain,
                    "domain": req_domain,
                    "type": "domain",
                    "is_first_party": is_first_party,
                    "criticality": 0.8 if is_first_party else 0.5,
                    "is_root": False
                })
                # Edge from Root to Domain
                edges.append({
                    "source": f"root_{apex_domain}",
                    "target": domain_node_id,
                    "relation": "hosts_domain"
                })

            # Add resource node
            resource_node_id = f"node_{req_id}"
            parsed_path = urlparse(req_url).path.split("/")[-1] or "/"
            nodes.append({
                "id": resource_node_id,
                "label": parsed_path[:25],
                "url": req_url,
                "domain": req_domain,
                "type": res_type,
                "status_code": req.get("status_code"),
                "content_type": req.get("content_type"),
                "content_length": req.get("content_length"),
                "is_first_party": is_first_party,
                "criticality": criticality,
                "is_root": False
            })

            # Edge from Domain to Resource
            edges.append({
                "source": domain_node_id if req_domain != apex_domain else f"root_{apex_domain}",
                "target": resource_node_id,
                "relation": f"loads_{res_type}"
            })

        # Separate unique domains and distinct URLs for auditing
        unique_hosts = list(domain_groups.keys())
        unique_urls = list({req["url"] for req in requests})

        return {
            "target_url": target_url,
            "apex_domain": apex_domain,
            "page_title": crawl_data.get("page_title"),
            "total_requests": len(requests),
            "unique_domains_count": len(unique_hosts),
            "first_party_domains": [d for d, v in domain_groups.items() if v["is_first_party"]],
            "third_party_domains": [d for d, v in domain_groups.items() if not v["is_first_party"]],
            "domain_groups": domain_groups,
            "graph": {
                "nodes": nodes,
                "edges": edges
            },
            "unique_hosts": unique_hosts,
            "unique_urls": unique_urls
        }

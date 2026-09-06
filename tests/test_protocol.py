import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from babel.graph import capabilities, discover, inspect, relations, schema
from babel.validate import emit_normalized, validate_tree


class ProtocolTests(unittest.TestCase):
    def test_validate_ok(self):
        result = validate_tree(ROOT)
        self.assertEqual(result["errors"], [], msg=result["errors"])
        self.assertTrue(result["ok"])
        expected = {
            "babel-interface",
            "signal-processor",
            "optical-body-s3",
            "c3-field-swarm",
            "metafield-engine",
        }
        self.assertEqual(set(result["repositories"]), expected)

    def test_discover_graph(self):
        graph = discover(ROOT)
        self.assertTrue(graph["ok"])
        self.assertIn("signal-processor", graph["repositories"])
        caps = [c["name"] for c in graph["repositories"]["signal-processor"]["capabilities"]]
        self.assertIn("ingest-field-observation", caps)
        kinds = {(e["from"], e["type"], e["to"]) for e in graph["edges"]}
        self.assertIn(("signal-processor", "consumes", "optical-body-s3"), kinds)
        self.assertIn(("optical-body-s3", "produces", "metafield-engine"), kinds)
        self.assertIn(("c3-field-swarm", "produces", "metafield-engine"), kinds)

    def test_inspect_and_schema(self):
        info = inspect("optical-body-s3", ROOT)
        self.assertTrue(info["ok"])
        sch = schema("optical-body-s3:field-observation", ROOT)
        self.assertTrue(sch["ok"])
        self.assertTrue(sch["matches"])

    def test_capabilities_and_relations(self):
        caps = capabilities("c3-field-swarm", ROOT)
        names = [c["name"] for c in caps["capabilities"]]
        self.assertIn("emit-field-delta", names)
        rel = relations("c3-field-swarm", ROOT)
        self.assertIn("isolates", rel["relations"])

    def test_normalized_json_serializable(self):
        blob = json.dumps(emit_normalized(validate_tree(ROOT)))
        self.assertIn("metafield-engine", blob)


if __name__ == "__main__":
    unittest.main()

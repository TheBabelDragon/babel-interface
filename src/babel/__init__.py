"""Babel Interface — read-only discovery of TheBabelDragon component graph."""

__version__ = "0.1.0"
PROTOCOL = "0.1"
OWNER = "TheBabelDragon"

RELATION_TYPES = (
    "consumes",
    "produces",
    "compatible_with",
    "observes",
    "controls",
    "extends",
    "depends_on",
    "isolates",
)

CAPABILITY_FIELDS = (
    "name",
    "description",
    "inputs",
    "outputs",
    "operation",
    "side_effects",
    "requires",
    "produces",
)

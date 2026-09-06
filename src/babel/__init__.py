"""Babel Interface — discovery and typed invocation of TheBabelDragon components."""

__version__ = "0.2.0"
PROTOCOL = "0.2"
OWNER = "TheBabelDragon"

INVOKE_PROTOCOL = "babel.invoke.v1"
RESULT_PROTOCOL = "babel.result.v1"

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

KNOWN_EFFECTS = (
    "read",
    "write",
    "network",
    "hardware",
    "filesystem",
    "process",
    "mutation",
)

SAFE_EFFECTS = frozenset({"read"})
UNSAFE_EFFECTS = frozenset(KNOWN_EFFECTS) - SAFE_EFFECTS

EFFECT_ALIASES = {
    "read_hardware": "hardware",
    "side_effect": "mutation",
}

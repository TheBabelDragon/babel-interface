# babel-interface

Self-describing, AI-addressable contract for the [TheBabelDragon](https://github.com/TheBabelDragon) repositories.

The metadata describes reality. It is not a second implementation of the applications.

```
AI
 ↓
babel discover
 ↓
inspect capability graph
 ↓
find compatible interface
 ↓
read schema
 ↓
construct valid input
 ↓
invoke application / interface
 ↓
consume typed output
 ↓
identify next compatible repository
```

## Contract

Every participating repository carries:

```
.babel/
├── manifest.yml
├── capabilities.yml
├── schemas/
├── examples/
└── relations.yml
```

Root discovery lives here:

```
.babel/ecosystem.yml
```

An agent can load that file and walk the graph without reading every README.

## First adapters

| Repository | Role | Human surface | Machine surface |
| --- | --- | --- | --- |
| [signal-processor](https://github.com/TheBabelDragon/signal-processor) | stimulus / session | GitHub Pages | `.babel/` + `producer.js` / `bridge.js` |
| [optical-body-s3](https://github.com/TheBabelDragon/optical-body-s3) | optical body | serial + OLED | FieldObservation JSON |
| [c3-field-swarm](https://github.com/TheBabelDragon/c3-field-swarm) | wireless edge | serial / swarmctl | FieldView, FieldDelta, C3JSON |
| [metafield-engine](https://github.com/TheBabelDragon/metafield-engine) | substrate | HUD `:8765` | World / FieldTick / FieldView |

Copies of the adapter trees live under `adapters/` so this repository can validate offline. The same `.babel/` directory is the payload pushed into each participating repo.

What this protocol does **not** do:

- redesign existing applications
- merge repositories
- alter electrical / wiring invariants
- touch swarm-core, ESP-NOW, field-bus, optical PHY, or application behavior

`c3-field-swarm/bylight_phy` is declared `isolates` — analog PHY stays an island.

## Install

```bash
python3 -m pip install -e .
```

Stdlib + PyYAML.

## Commands

All output is JSON.

```bash
babel discover
babel inspect signal-processor
babel capabilities optical-body-s3
babel schema field-observation
babel schema signal-processor:recipe
babel relations
babel validate
```

Discovery is read-only. The CLI does not hold GitHub credentials, does not run arbitrary shell, and does not rewrite default branches.

## Validation

`babel validate` checks:

- every catalogued manifest
- capability declarations (required fields, mutation side effects)
- referenced repositories
- schema documents
- broken relationships

and emits one normalized capability graph.

```bash
python3 -m babel validate --root .
```

## Human surface

`pages/index.html` is a static viewer of the same graph. Pages visualizes. `.babel/` is authoritative.

## Security boundary

Mutation capabilities, if introduced later, must name their side effects and travel through normal Git branches / commits / PRs.

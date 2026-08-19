# Workflow And Data Flow Architecture

This document maps the operational workflows across the LRA repository family.
It is a routing aid: ownership rules remain in the focused architecture and
governance documents linked from `docs/architecture/README.md`.

Repositories are independent. Governance and shared LaTeX infrastructure are
consumed directly from `lra-governance` and `lra-common`; nothing is fanned out,
and there is no monorepo.

## Repository Workflow Map

```mermaid
flowchart LR
    governance["lra-governance<br/>canonical standards, prompts, validators, canonical YAML"]
    common["lra-common<br/>shared LaTeX infrastructure"]
    volumes["lra-volume-i ... lra-volume-viii<br/>volume-owned content, independent builds"]
    lean["lra-lean<br/>formalization"]
    nurbs["lra-nurbs<br/>geometry and simulation"]
    numerical["lra-numerical-analysis<br/>benchmarks and numerical notes"]
    extractor["lra-pdf-extractor<br/>candidate source ingestion"]
    profiles["lra-source-profiles<br/>source profile staging"]
    explorer["lra-knowledge-explorer<br/>graph extraction and explorer"]
    output["lra-volumes-output<br/>published PDFs"]
    missing["clear failure<br/>lra-governance not resolved"]

    volumes -->|"resolve at runtime"| governance
    lean -->|"resolve at runtime"| governance
    nurbs -->|"resolve at runtime"| governance
    numerical -->|"resolve at runtime"| governance
    extractor -->|"resolve at runtime"| governance
    profiles -->|"resolve at runtime"| governance
    explorer -->|"resolve at runtime"| governance
    volumes -. abort if unresolved .-> missing

    common -->|"Docker image or explicit checkout"| volumes

    extractor -. reviewed candidate artifacts only .-> volumes
    profiles -. reviewed candidate artifacts only .-> volumes

    volumes -->|"independent Docker PDF build"| output
    governance -->|"orchestrated refresh over volume repos"| explorer
    explorer -->|"generated graph data and static explorer"| explorer
```

## Build, Publish, And Knowledge Data Flow

```mermaid
flowchart TB
    subgraph authoring["Authoring Sources"]
        volumeSource["Volume source repos<br/>lra-volume-*"]
        commonSource["Shared LaTeX source<br/>lra-common"]
        governanceSource["Governance + canonical YAML<br/>lra-governance"]
    end

    subgraph governanceRuntime["Governance Checks"]
        leafWrappers["Leaf repo wrappers<br/>tools/governance and scripts"]
        canonicalChecks["Canonical validators<br/>lra-governance/tools/governance"]
        governanceMissing["Fail with actionable message<br/>lra-governance not resolved"]
    end

    subgraph build["PDF Build Workflow"]
        checkout["Build-time checkout @head<br/>volume + lra-common + lra-governance"]
        dockerfile["lra-common/docker/Dockerfile<br/>pinned TeX Live image"]
        image["learning-real-analysis-latex<br/>CI-built Docker image"]
        latexmk["latexmk + LuaLaTeX<br/>inside Docker"]
        verify["PDF validation<br/>nonempty, %PDF-, %%EOF"]
    end

    subgraph publish["Publication"]
        outputRepo["lra-volumes-output"]
    end

    subgraph knowledge["Knowledge Explorer Pipeline"]
        refresh["governance-orchestrated refresh<br/>lra-governance"]
        extraction["theorem and dependency extraction"]
        graphData["knowledge.json<br/>graph-edges.json"]
        explorerApp["lra-knowledge-explorer"]
        pagesExplorer["GitHub Pages explorer"]
    end

    commonSource -->|"image or explicit checkout"| volumeSource
    volumeSource --> leafWrappers
    leafWrappers -->|"delegate"| canonicalChecks
    governanceSource --> canonicalChecks
    canonicalChecks -->|"governance pass/fail"| volumeSource
    leafWrappers -. governance not resolved .-> governanceMissing

    volumeSource --> checkout
    commonSource --> checkout
    governanceSource --> checkout
    checkout --> dockerfile
    dockerfile --> image
    image --> latexmk
    latexmk --> verify
    verify -->|"copy only after validation"| outputRepo

    volumeSource --> refresh
    governanceSource --> refresh
    refresh --> extraction
    extraction --> graphData
    graphData --> explorerApp
    explorerApp --> pagesExplorer
```

## Reading Rules

- Solid arrows are approved build, generation, or runtime-resolution paths.
- Dotted arrows are staging paths that require review before content enters an
  owning source repository, or failure paths when governance cannot be resolved.
- Leaf repository governance tools are wrappers only. They delegate to the
  canonical implementations in `lra-governance/tools/governance`, using
  `LRA_GOVERNANCE_ROOT`, a sibling `lra-governance` checkout, or the build image;
  if none is available, they fail with a clear setup message.
- PDF workflows build through the checked-in Docker image definition and must
  validate the produced PDF before publishing to `lra-volumes-output`.
- Generated explorer data is derived from the volume source repos by the
  governance-orchestrated refresh; it is not hand-authored in volume
  repositories.

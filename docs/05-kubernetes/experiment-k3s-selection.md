# k3s vs Alternatives — Experiment Record

**Status:** Analysis experiment (2026-09-24) — desk evaluation with measured
host constraints; no installations performed (authorization boundary)

## Hypothesis

k3s is the only local Kubernetes distribution that can run safely as a
hard-capped Docker container on this shared host without Docker Desktop
configuration changes.

## Environment

Mac Mini 2018 Intel, Docker Desktop 29.2.1 (VM 7.654 GiB), 20 protected
containers, VM free memory ≈ 4.5–5 GiB (measured).

## Method

Evaluate each candidate against the measured constraints: container-in-VM
feasibility on macOS/Intel, cgroup-cappability, reproducibility via compose,
footprint, and evidence-grade production use.

## Observations

| Candidate | Key observation |
|-----------|-----------------|
| k3s | single static binary/container; cgroup-cappable; compose-reproducible; CNCF-conformant; used in real edge/production |
| kind | requires node images with systemd-in-docker; on macOS effectively needs the VM inside Docker Desktop — workable but heavier, less production-evidence value, no resource-cap story per cluster |
| minikube | VM-driver oriented; docker driver exists but adds management layer (minikube profile state) — hidden state, contrary to reproducibility principle |
| microk8s | snap-based — snap is not natively supported on macOS; eliminated immediately |

## Results

Hypothesis SUPPORTED for this environment. k3s is the only candidate meeting
all four hard constraints (container-in-VM ✓, cgroup caps ✓, compose
reproducibility ✓, no hidden state ✓).

## Conclusion

k3s selected as the candidate for Phase 2 implementation, pending resource
authorization. The selection becomes ADR-0004 at implementation time.

## Decision

Proceed to authorization gate with Option A (k3s in capped container, no
Docker Desktop change) as the recommended path; alternatives preserved in
the fallback set.

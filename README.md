# Avtomatika: Full Feature Showcase

EN | [ES](./README_ES.md) | [RU](./README_RU.md)

This project provides a comprehensive demonstration of the **Avtomatika HLN (Hierarchical Logic Network)** ecosystem. It serves as the "Gold Standard" for E2E testing, covering all architectural patterns and advanced worker capabilities.

## 🏗 System Architecture

The example deploys a full-featured distributed environment:

![Main Blueprint](docs/images/full_showcase_graph.png)

1.  **Orchestrator**: The central engine managing complex blueprints with nested sub-jobs. Powered by `avtomatika` PyPI package.
2.  **GPU Worker**: Demonstrates heavy tasks with **Progress Reporting**, **Artifact Targeting**, and **S3 File Uploads**. Powered by `avtomatika-worker` PyPI package.
3.  **CPU Workers**: Two executors for parallel analysis (one reliable, one glitchy for reputation testing).
4.  **Webhook Receiver**: External service receiving real-time job notifications.
5.  **Infrastructure**: Redis (state), PostgreSQL (history), MinIO (S3), VictoriaMetrics, Grafana, and Jaeger.

## 🌟 Advanced Features Showcase

This example demonstrates 100% of the core **Avtomatika HLN** functionality:

### 1. Robust Dispatching (ZSET Indexing)
All worker discovery is powered by Redis **Sorted Sets (ZSET)**. Expiration timestamps are used as scores, allowing the orchestrator to filter out stale workers atomically during discovery. This eliminates "data missing" race conditions.

### 2. Reliable Work Stealing
Idle workers can "steal" tasks from busy workers' queues to ensure maximum utilization. The system guarantees atomic updates of `assigned_worker_id`, preventing result mismatch errors.

### 3. Human-in-the-Loop
Integration of `actions.await_human_approval()`. The pipeline pauses at the start, moving to `waiting_for_human` status until an external `APPROVED` decision is received via the Public API v1.

### 4. Smart & Cost-Aware Dispatching
*   **Resource Constraints**: Tasks requiring specific CPU/RAM (using GE - Greater or Equal logic).
*   **Artifact Targeting**: Using `installed_artifacts` to target workers that already have specific components (e.g. AI models or presets) installed.
*   **Timeouts**: Fine-grained `dispatch_timeout` and `result_timeout` control.

### 5. Zero-Trust Security (v1.0b26)
*   **mTLS & STS**: Support for mutual TLS authentication and automatic token rotation via Security Token Service.
*   **Cryptographic Signatures**: Every message is signed using HMAC-SHA256.
*   **Identity Chain**: Verification of the full identity chain to prevent event spoofing.
*   **Replay Protection**: Mandatory timestamps for all protocol messages.

### 6. Modern Blueprint Syntax
*   **Conditional Routing**: Use of `.when("condition")` decorators for declarative branching.
*   **Inferred Names**: State names automatically derived from function names.
*   **Parallelism**: Easy `fan-out / fan-in` via `actions.dispatch_parallel()` with individual transition support.

## 🚀 Quick Start

### 1. Launch with Docker (Full Stack)
```bash
docker compose up -d --build
```

### 2. Run Automated Full Validation
Performs a deep audit (linting, graphs, scenario execution with human approval emulation, S3 verification, and metrics):
```bash
make full-check
```

### 3. Interactive Demo Client
```bash
make init
.venv/bin/python3 client.py
```

## 📂 File Structure

*   `blueprints/main.py`: Complex flow with Human-approval, Parallelism, and S3.
*   `blueprints/sub.py`: Modern syntax with `.when()` conditions.
*   `blueprints/media/processor.py`: Example of a modular sub-blueprint for media cleanup. ![Cleanup Graph](docs/images/media_cleanup_graph.png)
*   `workers/gpu.py`: Advanced worker with Progress, Events, and Artifact Targeting.
*   `workers/cpu_*.py`: Simple workers for analysis and reputation testing.

---
*Developed by Dmitrii Gagarin aka madgagarin.*

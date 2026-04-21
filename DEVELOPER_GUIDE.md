# Avtomatika: Developer & Showcase Guide

This guide explains how the **Avtomatika HLN** ecosystem works using this full-featured example.

## 🚀 Quick Start

1.  **Initialize Environment:**
    ```bash
    make init
    ```
2.  **Start the Stack:**
    ```bash
    make up
    ```
3.  **Verify Health:**
    ```bash
    make health
    ```
4.  **Run Comprehensive Tests:**
    ```bash
    make test
    ```

## 🏗️ Architecture Overview

The system consists of three main parts:
1.  **Orchestrator (`avtomatika` package)**: The state-machine engine that manages jobs and dispatches tasks to workers.
2.  **Workers (`avtomatika-worker` package)**: Stateless agents that pull tasks, execute them, and report results.
3.  **Protocol (`rxon` package)**: The Hierarchical Logic Network (HLN) protocol for communication.

### Key Components in this Example
- `full_example.py`: The entry point that starts the Orchestrator with all features enabled.
- `blueprints/`: contains the "Logic" of your automation.
    - `main.py`: A complex workflow with parallel tasks, human approval, and conditional branching.
    - `maintenance.py`: A periodic task triggered by the internal scheduler.
- `workers/`: implementation of different worker types.
    - `gpu.py`: Advanced worker demonstrating progress reporting, real-time events, and S3 offloading.
    - `cpu_*.py`: Simple workers used for load testing and reputation checks.

## 🔒 Security (Zero Trust)

This project implements **Zero Trust** at the protocol level:
- **Mutual Authentication**: Workers must provide a valid `X-Worker-Token` to communicate.
- **Cryptographic Signatures**: Every message (Poll, Result, Event, Heartbeat) is signed using HMAC-SHA256.
- **Identity Chain**: Each event tracks its origin (`origin_worker_id`) and the path it took (`bubbling_chain`), preventing spoofing in complex hierarchies.

### Testing Security
You can verify security by running:
```bash
pytest tests/test_comprehensive.py -k test_security_spoofing_rejected
```

## 🛠️ Customizing the System

### 1. Adding a New Skill
To add a new skill to a worker, use the `@worker.skill` decorator:
```python
@worker.skill("my_new_skill")
async def my_handler(param1, **kwargs):
    return {"result": f"Processed {param1}"}
```

### 2. Modifying Blueprints
Blueprints are defined using a declarative syntax. You can add new states and transitions in `blueprints/main.py`.

**Gold Standard Practices (Beta 21+):**
- **Explicit Parallel Transitions**: When using `actions.dispatch_parallel()`, always provide `transitions` for each task, even if they are aggregated. This ensures the worker service can process individual success/failure signals.
- **Sub-Blueprint Outcomes**: When running sub-blueprints via `actions.run_blueprint()`, always use `success` and `failure` as keys in the `transitions` dictionary to match the Orchestrator's internal signaling.
- **State History**: Use `actions.update_context()` to store intermediate results. In Beta 21, these are automatically moved to `state_history` for persistent archival.

```python
@main_bp.handler("new_state")
async def handle_new_state(job_id, context, actions):
    actions.dispatch_task("my_new_skill", {"param1": "data"})
    # Transition to next state
    actions.go_to("next_state")
```

### 3. S3 Payload Offloading
Heavy data (like videos or large logs) are automatically moved to S3.
- Use `TaskFiles` in the worker to save files.
- The SDK will automatically detect files in the task directory and upload them.
- The Orchestrator will provide presigned URLs to clients.

## 📊 Monitoring & Telemetry
- **Prometheus/Grafana**: Access metrics at `http://localhost:3000`.
- **Jaeger**: Trace job execution at `http://localhost:16686`.
- **Health Check**: Every worker and the orchestrator have a `/status` endpoint.

---
*Developed by Dmitrii Gagarin aka madgagarin.*

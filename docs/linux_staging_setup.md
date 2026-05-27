# Linux Local Staging Setup

This document captures the current local staging setup for the AI Health Coach project.

## Purpose

The Linux laptop is used as a local staging/host machine for:

- FastAPI backend
- Streamlit UI
- SQLite app data
- local network testing from the Windows dev machine

The Linux host is **not** used for Ollama/model inference.

Ollama and heavier AI inference should remain on the stronger Windows dev machine unless a future split-runtime benchmark explicitly changes that.

## Current Host

- Hostname: `itsAlwaysDNS`
- User: `dusty`
- Ubuntu: `24.04.4 LTS`
- CPU: Intel i5-5300U, 2 cores / 4 threads
- RAM: 15 GiB
- LAN IP: `192.168.1.103`
- Project path: `/home/dusty/projects/fitness-ai-platform`

## Current Source of Truth

```text
Repo: drplatforms/fitness-ai-platform
Branch: feature/coaching-decision-layer

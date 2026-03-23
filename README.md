# BWIM Builder Agent

LLM-powered builder agent for the [Build What I Mean](https://github.com/ltl-uva/build_what_i_mean) benchmark.

## Overview

Interprets natural language building instructions and outputs block placements in a 9×9×9 grid using Claude via AWS Bedrock.

## Setup

```bash
uv sync
cp .env.example .env  # Configure your API keys
uv run python src/server.py
```

## Docker

```bash
docker build -t bwim-builder-agent .
docker run -p 9019:9019 --env-file .env bwim-builder-agent
```

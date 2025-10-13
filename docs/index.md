---
layout: default
---

## Overview

This repository contains the beta version of the RAG implementation of the paper (provisional title) "Provisional title: AI-Driven Text Analysis in the Political Economy of Sustainability: Hybrid Retrieval-Augmented Generation and LLM Multi-Agent Approach." 

By **Bastián González-Bustamante** and **Natascha van der Zwan**.

## Model Selection Benchmark

<img style="width: 95%; display: block; margin: auto;" src="https://making-finance-sustainable.github.io/RAG-VIDI-beta/plots/gof_indicators_combined.png">

[See plots per dataset](https://making-finance-sustainable.github.io/RAG-VIDI-beta/benchmark)

## Multi-Agent RAG Orchestration

### Current Pipeline

<img style="width: 95%; display: block; margin: auto;" src="https://making-finance-sustainable.github.io/RAG-VIDI-beta/plots/pipeline_diagram.png">

[See agents prompts](https://making-finance-sustainable.github.io/RAG-VIDI-beta/prompts)

## Frontrunners Preliminary Results

### Open-Source Pipeline

#### Models

- Summariser: `llama3.1:70b`
- Classifier: `gpt-oss:latest`
- Reviewer (presence): `hermes3:latest`
- Framing: `gpt-oss:latest`
- Reviewer (framing): `hermes3:latest`
- Embeddings: `text-embedding-3-large`

#### Reports

- [annual_and_sustainability_report_2023](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_annual_and_sustainability_report_2023)  
- [AP-Fonden-2-2023](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_AP-Fonden-2-2023)
- ERAPF-Annual-Report-2022
- NEST-Annual-Report-2023
- New-Zealand-Superannuation-Annual-Report-2023
- Pensioenfonds-Detailhandel-Annual-Report-2023
- PGGM-Annual-Report-2023
- PSPIB-Annual-Report-2023
- Uni-Super-Fund-Annual-Report-2023
- USS-Report-and-Accounts-2023

### Mixed-Pipeline -- Robustness Check

#### Models

- Summariser: `gpt-5-mini-2025-08-07`
- Classifier: `gpt-oss:latest`
- Reviewer (presence): `gpt-5-2025-08-07`
- Framing: `gpt-oss:latest`
- Reviewer (framing): `gpt-5-2025-08-07`
- Embeddings: `text-embedding-3-large`

#### Reports

**IN PROGRESS**

### Latest Revision

October 13, 2025
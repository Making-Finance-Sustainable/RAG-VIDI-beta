---
layout: default
---

## Overview

This repository contains the beta version of the RAG implementation of the paper (provisional title) "Provisional title: AI-Driven Text Analysis in the Political Economy of Sustainability: Hybrid Retrieval-Augmented Generation and LLM Multi-Agent Approach." 

By **Bastián González-Bustamante** and **Natascha van der Zwan**.

## Document Parsing

### Docling Selection

We experimented with a number of PDF parsing methods, including Pdftools, Pdfplumber, PyMuPDF, Pdfminer, Apache Tika, and Docling. Docling was selected due to its superior performance, consistently balancing precision, comprehensiveness and structural accuracy. However, it is necessary to revisit the picture processing step.

This step allows us to annotate different pictures that appear in the reports as a separate captioning task. We are running additional experiments to reinforce this task using Visual Large Models (VLMs) since this involves considerable trade-offs between performance and computing time.

[SEE AN EXAMPLE OF NORGES BANK](https://making-finance-sustainable.github.io/RAG-VIDI-beta/captioning)

### VLMs Captioning Progress

| <img style="display: block; margin: auto;" src="https://making-finance-sustainable.github.io/RAG-VIDI-beta/badges/smolvlm_01.svg"> | <img style="display: block; margin: auto;" src="https://making-finance-sustainable.github.io/RAG-VIDI-beta/badges/qwen3_39.svg"> |

## Model Selection Benchmark

<img style="width: 95%; display: block; margin: auto;" src="https://making-finance-sustainable.github.io/RAG-VIDI-beta/plots/gof_indicators_combined.png">

[SEE PLOTS PER DATASET](https://making-finance-sustainable.github.io/RAG-VIDI-beta/benchmark)

## Multi-Agent RAG Orchestration

<img style="width: 95%; display: block; margin: auto;" src="https://making-finance-sustainable.github.io/RAG-VIDI-beta/plots/pipeline_diagram.png">

[SEE UPDATED PROMPTS](https://making-finance-sustainable.github.io/RAG-VIDI-beta/prompts)

> **Note.** Some extra changes could be incorporated in the prompts, especially in the framing and prevalence, which do not seem too accurate for the moment.

## Frontrunners Preliminary Results

### Open-Source Pipeline

The selection of models was based on the benchmark above. We are using a fully open-source pipeline in which Llama 3.1 (70B) prepare the summary, GPT-OSS (20B) makes the decisions and Hermes 3 (70B) reviews and overturns with RAG-fed evidence. For robustness checks, we will rely on a mixed pipeline in which Llama 3.1 will be replaced by GPT-5-mini and Hermes 3 by GPT-5, both state-of-the-art closed, flagship OpenAI models.

We will introduce human-in-the-loop revision based on consistency metrics between both pipelines.

#### Models

- Summariser: `llama3.1:70b`
- Classifier: `gpt-oss:latest`
- Reviewer (presence): `hermes3:latest`
- Framing: `gpt-oss:latest`
- Reviewer (framing): `hermes3:latest`
- Embeddings: `text-embedding-3-large`

> **Note.** It is not a significant change to swap the classifier and reviewer (Hermes 3 and GPT-OSS). I will try to rerun the pipeline including MCP (Model Context Protocol). This should improve the orchestration and retrieval quality. It shall be a bit more intensive, but particularly useful for long documents.

#### Reports

1. [annual_and_sustainability_report_2023](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_annual_and_sustainability_report_2023)  
2. [AP-Fonden-2-2023](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_AP-Fonden-2-2023)
3. [ERAPF-Annual-Report-2022](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_ERAPF-Annual-Report-2022)
4. [NEST-Annual-Report-2023](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_NEST-Annual-Report-2023)
5. [New-Zealand-Superannuation-Annual-Report-2023](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_New-Zealand-Superannuation-Annual-Report-2023)
6. [Pensioenfonds-Detailhandel-Annual-Report-2023](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_Pensioenfonds-Detailhandel-Annual-Report-2023)
7. [PGGM-Annual-Report-2023](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_PGGM-Annual-Report-2023)
8. [PSPIB-Annual-Report-2023](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_PSPIB-Annual-Report-2023)
9. [Uni-Super-Fund-Annual-Report-2023](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_Uni-Super-Fund-Annual-Report-2023)
10. [USS-Report-and-Accounts-2023](https://making-finance-sustainable.github.io/RAG-VIDI-beta/rag-reports/rag_USS-Report-and-Accounts-2023)

### Mixed-Pipeline

#### Models

- Summariser: `gpt-5-mini-2025-08-07`
- Classifier: `gpt-oss:latest`
- Reviewer (presence): `gpt-5-2025-08-07`
- Framing: `gpt-oss:latest`
- Reviewer (framing): `gpt-5-2025-08-07`
- Embeddings: `text-embedding-3-large`

#### Reports

> **Note.** Work in progress.

<br />
**Latest update:** October 30, 2025.
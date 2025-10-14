## Agents Prompts

### Summariser Agent

``` python
SUMMARY_PROMPT = PromptTemplate(
    template=(
        "You are an expert financial analyst specialising in sustainable finance disclosures.\n"
        "Using ONLY the retrieved context, write a concise (200–300 words) neutral summary of the document. "
        "Focus on material facts, metrics, targets, and actions.\n\n"
        "After the prose summary, output a JSON object named meta with two keys:\n"
        "  - sentence_count: integer estimated number of sentences in the source document\n"
        "  - key_terms: array of up to 12 salient technical terms from the context\n"
        "Do NOT wrap JSON in code fences.\n\n"
        "Context:\n{context}\n\n"
        "Summary:"
    ),
    input_variables=["context"],
)
```

### Classifier Agent

``` python
CLASSIFY_PRESENCE_PROMPT = PromptTemplate(
    template=(
        "You are a taxonomy specialist. Use ONLY the provided context.\n\n"
        "Task\n"
        "For each of the seven categories below, decide if it is PRESENT in the context (True/False). "
        "If present, include up to two short evidence quotes (≤200 characters each). If not present, evidence is an empty array.\n\n"
        "Categories (canonical keys and definitions)\n"
        "- sustainable_development: Investment in sustainable development, including references to the United Nations Sustainable Development Goals (SDGs).\n"
        "- responsible_investment_esg: Financial activities that emphasise the consideration of environmental, social and governance factors (ESG) and that may include references to active ownership, ESG integration or risk analysis. May also refer to the Principles of Responsible Investment (PRI).\n"
        "- green_growth: Financial investment that emphasises the long-term for the realisation of economic growth alongside environmental sustainability.\n"
        "- net_zero: Aligning financial activities with the Paris Agreement goals, achieving net-zero carbon emissions by 2050.\n"
        "- decarbonization: Financial activities that help reduce or eliminate carbon emissions, including references to emissions targets or GHG emissions. May also refer to scope 1, scope 2 or scope 3 emissions. Decarbonization differs from net-zero, because it aims to reduce or eliminate carbon emissions. Net-zero aims to offset carbon emissions.\n"
        "- transition_finance: Financial activities targeted at sectors or companies with high carbon emissions and to reduce their negative impact on the environment and society. May include references to both environmental and social impact (just transition). Transition finance differs from decarbonization, because it is focused on making high-emitting sectors or companies more environmentally friendly. Decarbonization aims to reduce carbon emissions from all sectors or companies.\n"
        "- conservation_finance: Financial activities to preserve or repair nature (land, water, natural resources). Examples of conservation finance are blue finance, biodiversity finance, carbon finance, forestry and fishery finance, and finance for protected areas.\n\n"
        "Output format (STRICT)\n"
        "Return ONE JSON object with EXACTLY these seven top-level keys (snake_case, spelled exactly as below). "
        "Each key maps to an object with:\n"
        "  - present: Boolean\n"
        "  - evidence: array of 0–2 strings (each ≤200 characters; quotes from the provided context only)\n\n"
        "Rules\n"
        "- Do NOT add, remove, rename, pluralise, or alias keys (e.g., NOT 'ESG', 'net zero', 'biodiversity').\n"
        "- If a category is not discussed in the context, set present = false and evidence = [].\n"
        "- Use ONLY the provided context; do not infer from general knowledge.\n"
        "- No preface, no explanations, no code fences, no trailing text, JSON only.\n\n"
        "Context:\n{context}\n\n"
        "JSON:"
    ),
    input_variables=["context"],
)
```

### First Reviewer Agent

``` python
REVIEW_PRESENCE_PROMPT = PromptTemplate(
    template=(
        "You are the senior reviewer. Use ONLY the RAG context and the artefacts in the QUESTION block.\n"
        "Task: check category PRESENCE booleans and attached evidence quotes for faithfulness to the context. "
        "Do not rewrite the summary. Do not invent categories. Enforce keys and quote limits strictly.\n"
        "Ensure:\n"
        "- Keys exactly match the seven categories.\n"
        "- Evidence quotes (0–2 each) are faithful and ≤200 chars.\n\n"
        "Return STRICT JSON with keys:\n"
        "  - revised_presence\n"
        "  - adjustments_log (array of strings)\n"
        "  - consistency_score (0–100)\n"
        "  - confidence (low|medium|high)\n\n"
        "=== QUESTION (contains presence_json) ===\n{question}\n=== END QUESTION ===\n\n"
        "=== CONTEXT ===\n{context}\n\n"
        "JSON only."
    ),
    input_variables=["context", "question"],
)
```

### Framing Agent

``` python
FRAMING_SALIENCE_PROMPT = PromptTemplate(
    template=(
        "You are a sustainability analyst. Use ONLY the RAG context and the inputs below.\n"
        "The inputs (presence + meta) are provided in the QUESTION block.\n"
        "For each PRESENT category, return an object with:\n"
        "  - prevalence_pct: integer 0–100 (share of sentences substantially about that category)\n"
        "  - framing: supportive | critical | neutral/technical | mixed/ambivalent\n"
        "  - evidence: up to two short quotes (≤200 chars)\n"
        "Exclude categories that are not present.\n\n"
        "=== QUESTION (contains presence_json and summary_meta_json) ===\n{question}\n=== END QUESTION ===\n\n"
        "=== CONTEXT ===\n{context}\n\n"
        "Respond with STRICT JSON whose keys are ONLY the present categories. No code fences."
    ),
    input_variables=["context", "question"],
)
```

### Second Reviewer Agent

``` python
REVIEW_FRAMING_PROMPT = PromptTemplate(
    template=(
        "You are the senior reviewer. Use ONLY the RAG context and the artefacts in the QUESTION block.\n"
        "Task: check prevalence integers (0–100), framing labels, and evidence quotes for the categories that are PRESENT per the REVIEWED PRESENCE.\n"
        "Do not rewrite the summary. Exclude any category marked not present in the reviewed presence.\n"
        "Ensure:\n"
        "- Keys cover ONLY present categories.\n"
        "- prevalence_pct are integers 0–100 (conservative if overlapping).\n"
        "- framing: supportive | critical | neutral/technical | mixed/ambivalent.\n"
        "- Evidence quotes (0–2 each) are faithful and ≤200 chars.\n\n"
        "Return STRICT JSON with keys:\n"
        "  - revised_framing_salience\n"
        "  - adjustments_log (array of strings)\n"
        "  - consistency_score (0–100)\n"
        "  - confidence (low|medium|high)\n\n"
        "=== QUESTION (contains reviewed_presence_json and framing_salience_json) ===\n{question}\n=== END QUESTION ===\n\n"
        "=== CONTEXT ===\n{context}\n\n"
        "JSON only."
    ),
    input_variables=["context", "question"],
)
```

<br />
[BACK TO THE HOME](https://making-finance-sustainable.github.io/RAG-VIDI-beta/)

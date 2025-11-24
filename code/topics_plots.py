## Bastián González-Bustamante
## Making Finance Sustainable VIDI Project
## November 2025

##########################################################################
## 1. Dependencies
##########################################################################
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

##########################################################################
## 2. Load CSV and prepare data
##########################################################################

## Data
csv_path = "data/investment_reports_topics.csv"

df = pd.read_csv(csv_path)

## Required columns
if 'doc_name' not in df.columns:
    raise ValueError(f"{csv_path} must contain a 'doc_name' column.")

## Infer topic columns
topic_cols = [c for c in df.columns if c.endswith('_present')]
if len(topic_cols) == 0:
    raise ValueError("No topic columns found. Expected columns ending with '_present'.")

## Convert topic columns to booleans in a robust way
for col in topic_cols:
    col_upper = df[col].astype(str).str.upper()
    df[col] = col_upper.map({
        'TRUE': True,
        'FALSE': False,
        '1': True,
        '0': False
    }).fillna(False).astype(bool)

n_docs = len(df)
if n_docs == 0:
    raise ValueError("The input CSV has no rows. Nothing to plot.")

##########################################################################
## 3. Topic prevalence (share of documents mentioning each topic)
##########################################################################

## Prevalence as proportion of documents where topic == True
prevalence = df[topic_cols].mean().sort_values(ascending=False)

## Reorder topic columns by prevalence for consistent plotting
ordered_topics = prevalence.index.tolist()
prevalence = prevalence.loc[ordered_topics]

##########################################################################
## 4. Topic co-occurrence matrix
##########################################################################

## Co-occurrence: proportion of documents where topic i and j are both present
## Using matrix multiplication on {0,1} representation
X = df[ordered_topics].astype(int)
coocc_counts = X.T.dot(X)              ## Counts of joint occurrences
coocc_matrix = coocc_counts / n_docs   ## Convert to proportions

##########################################################################
## 5. Topic prevalence bar chart
##########################################################################

## Solarized-inspired palette
topic_colors = [
    "#657b83",  # base00
    "#586e75",  # base01
    "#073642",  # base02
    "#002b36",  # base03
    "#93a1a1",  # base1
    "#839496",  # base0
    "#b58900"   # yellow accent
]

## Check number of colours per topics
if len(topic_colors) < len(ordered_topics):
    ## Repeat colours if there are more topics
    repeats = int(np.ceil(len(ordered_topics) / len(topic_colors)))
    topic_colors = (topic_colors * repeats)[:len(ordered_topics)]

fig1, ax1 = plt.subplots(figsize=(10, 6))

x_pos = np.arange(len(ordered_topics))
ax1.bar(x_pos, prevalence.values, color=topic_colors, edgecolor='none')

ax1.set_xticks(x_pos)
ax1.set_xticklabels(ordered_topics, rotation=45, ha='right', fontsize=9)
ax1.set_ylabel("Share of documents", fontsize=11)
ax1.set_title("Topic prevalence across investment reports", fontsize=14)

## Remove spines
for spine in ['top', 'right']:
    ax1.spines[spine].set_visible(False)

ax1.set_ylim(0, 1.0)
ax1.tick_params(axis='y', length=0)

plt.tight_layout()

##########################################################################
## 6. Topic co-occurrence heatmap
##########################################################################

fig2, ax2 = plt.subplots(figsize=(8, 7))

## Heatmap of co-occurrence proportions
im = ax2.imshow(coocc_matrix.values, cmap="Greys", vmin=0, vmax=1)

ax2.set_xticks(np.arange(len(ordered_topics)))
ax2.set_yticks(np.arange(len(ordered_topics)))
ax2.set_xticklabels(ordered_topics, rotation=45, ha='right', fontsize=9)
ax2.set_yticklabels(ordered_topics, fontsize=9)

ax2.set_title("Topic co-occurrence (share of documents)", fontsize=14)

## Add colour bar
cbar = fig2.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
cbar.ax.set_ylabel("Proportion of documents", rotation=90, va="center")

## Turn off gridlines and adjust spines
for spine in ['top', 'right', 'left', 'bottom']:
    ax2.spines[spine].set_visible(False)

ax2.tick_params(axis='both', length=0)

plt.tight_layout()

##########################################################################
## 7. Save figures
##########################################################################

os.makedirs("results", exist_ok=True)

prev_output = "docs/plots/topic_prevalence"
coocc_output = "docs/plots/topic_cooccurrence"

fig1.savefig(f"{prev_output}.png", dpi=300, bbox_inches='tight', transparent=True)
fig1.savefig(f"{prev_output}.pdf", dpi=300, bbox_inches='tight')

fig2.savefig(f"{coocc_output}.png", dpi=300, bbox_inches='tight', transparent=True)
fig2.savefig(f"{coocc_output}.pdf", dpi=300, bbox_inches='tight')

print("\nTopic prevalence bar chart saved as PNG and PDF in 'results/'.")
print("Topic co-occurrence heatmap saved as PNG and PDF in 'results/'.")
## plt.show()

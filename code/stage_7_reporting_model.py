## Bastián González-Bustamante
## Making Finance Sustainable VIDI Project
## Reporting breadth model
## February 2026

##########################################################################
## 1. Dependencies
##########################################################################

import os
import warnings
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

import statsmodels.formula.api as smf
import statsmodels.api as sm
import statsmodels.genmod.generalized_linear_model as glm

from statsmodels.discrete.count_model import ZeroInflatedPoisson
from statsmodels.discrete.discrete_model import NegativeBinomial

## Use log-likelihood-based BIC for GLM models.
## This resolves the statsmodels FutureWarning about BIC computation.
glm.SET_USE_BIC_LLF(True)

np.random.seed(42)

##########################################################################
## 2. Load CSV and prepare data
##########################################################################

csv_path = "data/tidy/reports_topics_validation.csv"

df = pd.read_csv(csv_path)

required_cols = ["company", "country", "assets", "lang_report"]
missing_required = [c for c in required_cols if c not in df.columns]
if missing_required:
    raise ValueError(
        f"{csv_path} is missing required column(s): {missing_required}. "
        f"Found columns: {list(df.columns)}"
    )

topic_cols = [c for c in df.columns if c.endswith("_present")]
if len(topic_cols) == 0:
    raise ValueError("No topic columns found. Expected columns ending with '_present'.")

df[topic_cols] = df[topic_cols].replace(r"^\s*$", np.nan, regex=True)
df = df.dropna(subset=topic_cols, how="all").copy()

for col in topic_cols:
    col_upper = df[col].astype(str).str.upper().str.strip()
    df[col] = col_upper.map({
        "TRUE": True,
        "FALSE": False,
        "1": True,
        "0": False,
        "YES": True,
        "NO": False
    }).fillna(False).astype(bool)

n_docs = len(df)
if n_docs == 0:
    raise ValueError("The input CSV has no usable rows after cleaning. Nothing to analyse.")

df["country"] = df["country"].astype(str).str.strip()
df["assets"] = pd.to_numeric(df["assets"], errors="coerce")

##########################################################################
## 3. Regions: same recoding as original plots
##########################################################################

country_to_region = {
    ## Europe
    "Norway": "Europe", "Netherlands": "Europe", "France": "Europe", "Germany": "Europe",
    "Sweden": "Europe", "Denmark": "Europe", "UK": "Europe", "Luxembourg": "Europe",
    "Finland": "Europe", "Switzerland": "Europe", "Austria": "Europe", "Portugal": "Europe",
    "Italy": "Europe", "Ireland": "Europe", "Belgium": "Europe", "Iceland": "Europe",

    ## Americas
    "USA": "Americas", "Canada": "Americas", "Mexico": "Americas",
    "Chile": "Americas", "Colombia": "Americas", "Brazil": "Americas",

    ## Middle East
    "UAE": "Middle East", "Saudi Arabia": "Middle East", "Kuwait": "Middle East",
    "Qatar": "Middle East", "Iran": "Middle East", "Israel": "Middle East",

    ## Asia-Pacific
    "Singapore": "Asia-Pacific", "Japan": "Asia-Pacific", "China": "Asia-Pacific",
    "South Korea": "Asia-Pacific", "Hong Kong": "Asia-Pacific", "Malaysia": "Asia-Pacific",
    "Australia": "Asia-Pacific", "Taiwan": "Asia-Pacific", "India": "Asia-Pacific",
    "Vietnam": "Asia-Pacific", "Philippines": "Asia-Pacific", "Thailand": "Asia-Pacific",
    "Brunei": "Asia-Pacific", "New Zealand": "Asia-Pacific",

    ## Africa
    "South Africa": "Africa", "Libya": "Africa",

    ## Eurasia / Central Asia
    "Turkey": "Eurasia", "Russia": "Eurasia", "Kazakhstan": "Eurasia", "Azerbaijan": "Eurasia",
}

df["region"] = df["country"].map(country_to_region).fillna("Other/Unknown")

##########################################################################
## 4. Assets quartiles
##########################################################################

assets_non_missing = df["assets"].dropna()
if assets_non_missing.nunique() < 4:
    raise ValueError(
        "Assets does not have enough distinct non-missing values to form quartiles (need >= 4)."
    )

quartile_order = ["Q1 (low)", "Q2", "Q3", "Q4 (high)"]

df["assets_quartile"] = pd.qcut(
    df["assets"],
    q=4,
    labels=quartile_order
)

##########################################################################
## 5. Derived variables
##########################################################################

df["topic_count"] = df[topic_cols].sum(axis=1).astype(int)

df["lang_report_clean"] = (
    df["lang_report"]
    .astype(str)
    .str.strip()
    .replace({"nan": np.nan, "None": np.nan})
)

df["english_report"] = np.where(df["lang_report_clean"] == "English", 1, 0)

##########################################################################
## 6. Model dataset
##########################################################################

model_df = df.dropna(
    subset=[
        "topic_count",
        "assets_quartile",
        "region",
        "english_report"
    ]
).copy()

region_order = sorted(model_df["region"].dropna().unique().tolist())

## Use Europe as reference category.
## This is substantively motivated by stronger sustainable-finance regulation
## and disclosure expectations in Europe.
if "Europe" in region_order:
    region_order = ["Europe"] + [r for r in region_order if r != "Europe"]
else:
    raise ValueError("Europe is not present in the region variable, so it cannot be used as reference.")

model_df["region"] = pd.Categorical(
    model_df["region"],
    categories=region_order,
    ordered=False
)

model_df["assets_quartile"] = pd.Categorical(
    model_df["assets_quartile"],
    categories=quartile_order,
    ordered=True
)

os.makedirs("results", exist_ok=True)

##########################################################################
## 7. Estimate models and diagnostics
##########################################################################

formula = (
    "topic_count ~ "
    "C(assets_quartile, Treatment(reference='Q1 (low)')) + "
    "C(region, Treatment(reference='Europe')) + "
    "english_report"
)

## Main model: OLS with robust standard errors
ols_model = smf.ols(
    formula=formula,
    data=model_df
).fit(cov_type="HC3")

## Robustness model: Poisson count model with robust standard errors
poisson_model = smf.glm(
    formula=formula,
    data=model_df,
    family=sm.families.Poisson()
).fit(cov_type="HC3")

## Negative binomial regression model as a diagnostic comparison.
## This estimates the overdispersion parameter rather than fixing alpha.
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    nb_model = NegativeBinomial.from_formula(
        formula,
        data=model_df
    ).fit(
        method="bfgs",
        maxiter=300,
        disp=False
    )

## Zero-inflated Poisson as a diagnostic comparison.
## The inflation equation is intercept-only to keep the comparison parsimonious.
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    zip_model = ZeroInflatedPoisson.from_formula(
        formula,
        model_df,
        exog_infl=np.ones((len(model_df), 1)),
        inflation="logit"
    ).fit(
        method="bfgs",
        maxiter=300,
        disp=False
    )

ols_r2 = ols_model.rsquared
ols_adj_r2 = ols_model.rsquared_adj

## Poisson overdispersion diagnostic.
## Values close to 1 suggest that the Poisson variance assumption is acceptable.
poisson_pearson_chi2 = poisson_model.pearson_chi2
poisson_df_resid = poisson_model.df_resid
poisson_dispersion = poisson_pearson_chi2 / poisson_df_resid

## Zero diagnostic.
## Compare observed zeroes with the number of zeroes expected under the fitted Poisson model.
observed_zeros = int((model_df["topic_count"] == 0).sum())
observed_zero_share = observed_zeros / len(model_df)

poisson_mu = poisson_model.predict(model_df)
expected_zeros_poisson = float(np.sum(np.exp(-poisson_mu)))
expected_zero_share_poisson = expected_zeros_poisson / len(model_df)

zero_ratio = observed_zeros / expected_zeros_poisson if expected_zeros_poisson > 0 else np.nan

## Information criteria comparison.
def get_bic(model):
    if hasattr(model, "bic_llf"):
        return model.bic_llf
    return model.bic

count_model_fit = pd.DataFrame({
    "Model": ["Poisson", "Negative binomial", "Zero-inflated Poisson"],
    "AIC": [poisson_model.aic, nb_model.aic, zip_model.aic],
    "BIC": [get_bic(poisson_model), nb_model.bic, zip_model.bic]
})

best_aic_model = count_model_fit.loc[count_model_fit["AIC"].idxmin(), "Model"]
best_bic_model = count_model_fit.loc[count_model_fit["BIC"].idxmin(), "Model"]

##########################################################################
## 8. Helper functions for Markdown model tables
##########################################################################

def significance_stars(p):
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    elif p < 0.10:
        return "+"
    else:
        return ""

def clean_term(term):
    replacements = {
        "Intercept": "Constant",
        "const": "Constant",
        "inflate_const": "Inflation constant",
        "alpha": "NB overdispersion alpha",
        "english_report": "English-language report",
        "C(assets_quartile, Treatment(reference='Q1 (low)'))[T.Q2]": "AUM quartile: Q2",
        "C(assets_quartile, Treatment(reference='Q1 (low)'))[T.Q3]": "AUM quartile: Q3",
        "C(assets_quartile, Treatment(reference='Q1 (low)'))[T.Q4 (high)]": "AUM quartile: Q4 (high)",
    }

    if term.startswith("C(region, Treatment(reference='Europe'))"):
        term = term.replace("C(region, Treatment(reference='Europe'))[T.", "")
        term = term.replace("]", "")
        return f"Region: {term}"

    return replacements.get(term, term)

def model_to_table(model, model_name, include_inflation_terms=False):
    rows = []

    for term in model.params.index:
        ## Keep the zero-inflation constant only when explicitly requested.
        if not include_inflation_terms and str(term).startswith("inflate_"):
            continue

        estimate = model.params[term]
        se = model.bse[term] if term in model.bse.index else np.nan
        pval = model.pvalues[term] if term in model.pvalues.index else np.nan
        stars = significance_stars(pval) if pd.notna(pval) else ""

        rows.append({
            "term": clean_term(term),
            model_name: f"{estimate:.3f}{stars}",
            f"{model_name} SE": f"({se:.3f})" if pd.notna(se) else ""
        })

    return pd.DataFrame(rows)

## Main estimates table: includes all four models.
## For ZIP, the table includes the count equation and excludes the inflation constant.
ols_table = model_to_table(ols_model, "OLS")
poisson_table = model_to_table(poisson_model, "Poisson")
nb_table = model_to_table(nb_model, "NBRM")
zip_table = model_to_table(zip_model, "ZIP", include_inflation_terms=False)

model_table = ols_table.copy()

for tab in [poisson_table, nb_table, zip_table]:
    model_table = pd.merge(
        model_table,
        tab,
        on="term",
        how="outer"
    )

term_order = (
    ["Constant", "AUM quartile: Q2", "AUM quartile: Q3", "AUM quartile: Q4 (high)"] +
    [f"Region: {r}" for r in region_order if r != "Europe"] +
    ["English-language report", "NB overdispersion alpha"]
)

model_table["term_order"] = model_table["term"].apply(
    lambda x: term_order.index(x) if x in term_order else 999
)

model_table = (
    model_table
    .sort_values("term_order")
    .drop(columns="term_order")
    .fillna("")
)

## Separate ZIP inflation equation table.
zip_inflation_table = model_to_table(
    zip_model,
    "ZIP inflation equation",
    include_inflation_terms=True
)

zip_inflation_table = zip_inflation_table[
    zip_inflation_table["term"].str.contains("Inflation", case=False, na=False)
].copy()

##########################################################################
## 9. Model fit statistics and diagnostics
##########################################################################

fit_stats = pd.DataFrame({
    "Statistic": [
        "Observations",
        "R-squared",
        "Adjusted R-squared",
        "AIC",
        "BIC"
    ],
    "OLS": [
        f"{int(ols_model.nobs)}",
        f"{ols_model.rsquared:.3f}",
        f"{ols_model.rsquared_adj:.3f}",
        f"{ols_model.aic:.1f}",
        f"{ols_model.bic:.1f}"
    ],
    "Poisson": [
        f"{int(poisson_model.nobs)}",
        "",
        "",
        f"{poisson_model.aic:.1f}",
        f"{get_bic(poisson_model):.1f}"
    ],
    "NBRM": [
        f"{int(nb_model.nobs)}",
        "",
        "",
        f"{nb_model.aic:.1f}",
        f"{nb_model.bic:.1f}"
    ],
    "ZIP": [
        f"{int(zip_model.nobs)}",
        "",
        "",
        f"{zip_model.aic:.1f}",
        f"{zip_model.bic:.1f}"
    ]
})

count_diagnostics = pd.DataFrame({
    "Diagnostic": [
        "Poisson Pearson dispersion",
        "Observed zeroes",
        "Observed zero share",
        "Expected zeroes under Poisson",
        "Expected zero share under Poisson",
        "Observed / expected zero ratio",
        "Best count model by AIC",
        "Best count model by BIC"
    ],
    "Value": [
        f"{poisson_dispersion:.3f}",
        f"{observed_zeros}",
        f"{observed_zero_share:.3f}",
        f"{expected_zeros_poisson:.1f}",
        f"{expected_zero_share_poisson:.3f}",
        f"{zero_ratio:.3f}",
        best_aic_model,
        best_bic_model
    ]
})

##########################################################################
## 10. Diagnostic interpretation
##########################################################################

if poisson_dispersion < 1.25:
    dispersion_interpretation = (
        "The Pearson dispersion statistic is close to 1, suggesting that "
        "overdispersion is limited and that a Poisson specification is adequate."
    )
elif poisson_dispersion < 1.75:
    dispersion_interpretation = (
        "The Pearson dispersion statistic indicates moderate overdispersion. "
        "The Poisson model remains useful as a parsimonious count-model robustness check, "
        "but the negative binomial model should also be inspected."
    )
else:
    dispersion_interpretation = (
        "The Pearson dispersion statistic indicates substantial overdispersion. "
        "A negative binomial model may be preferable to a Poisson specification."
    )

if 0.80 <= zero_ratio <= 1.25:
    zero_interpretation = (
        "The number of observed zeroes is close to the number expected under the "
        "Poisson model, providing little evidence that a zero-inflated model is required."
    )
elif zero_ratio > 1.25:
    zero_interpretation = (
        "The number of observed zeroes is higher than expected under the Poisson model. "
        "This provides some evidence that a zero-inflated specification may be relevant."
    )
else:
    zero_interpretation = (
        "The number of observed zeroes is lower than expected under the Poisson model. "
        "This does not support the need for a zero-inflated specification."
    )

if best_aic_model == "Poisson" and best_bic_model == "Poisson":
    count_model_interpretation = (
        "AIC and BIC both favour the Poisson model over the negative binomial and "
        "zero-inflated alternatives. Together with the dispersion and zero diagnostics, "
        "this supports using Poisson as the main count-model robustness check."
    )
elif best_bic_model == "Poisson":
    count_model_interpretation = (
        "BIC favours the Poisson model, although AIC selects a different count specification. "
        "Because BIC penalises additional parameters more strongly, this supports retaining "
        "the more parsimonious Poisson model as the main count-model robustness check."
    )
else:
    count_model_interpretation = (
        f"The information criteria do not uniformly favour Poisson. AIC favours {best_aic_model} "
        f"and BIC favours {best_bic_model}. The Poisson results should therefore be interpreted "
        "as a parsimonious robustness check rather than as the uniquely preferred count model."
    )

##########################################################################
## 11. Save Markdown report
##########################################################################

md_output = []

md_output.append("# Reporting breadth models\n")
md_output.append(
    "Outcome: number of sustainable-finance categories detected in each annual report.\n"
)
md_output.append(
    "The main model is an OLS regression with heteroskedasticity-robust HC3 standard errors. "
    "The count-model robustness checks include Poisson, negative binomial regression model (NBRM), "
    "and zero-inflated Poisson (ZIP) specifications. AUM is included as quartile dummies, with "
    "Q1 (low) as the reference category. The reference category for region is Europe. This choice "
    "is substantively motivated by the expectation that sustainable-finance reporting is more "
    "developed in Europe because of stronger regulatory and disclosure frameworks.\n"
)

md_output.append("## Model estimates\n")
md_output.append(model_table.to_markdown(index=False))
md_output.append("\n\n")

if not zip_inflation_table.empty:
    md_output.append("## ZIP inflation equation\n")
    md_output.append(
        "The ZIP model uses an intercept-only inflation equation. The main estimates table reports the count equation.\n"
    )
    md_output.append(zip_inflation_table.to_markdown(index=False))
    md_output.append("\n\n")

md_output.append("## Model fit\n")
md_output.append(fit_stats.to_markdown(index=False))
md_output.append("\n\n")

md_output.append("## Count-model diagnostics\n")
md_output.append(count_diagnostics.to_markdown(index=False))
md_output.append("\n\n")

md_output.append("## Diagnostic interpretation\n")
md_output.append(f"- {dispersion_interpretation}")
md_output.append(f"- {zero_interpretation}")
md_output.append(f"- {count_model_interpretation}\n")

md_output.append("## Notes\n")
md_output.append(f"- Number of annual reports after topic cleaning: {n_docs}.")
md_output.append(f"- Number of observations in the model dataset: {int(ols_model.nobs)}.")
md_output.append(f"- OLS R-squared: {ols_r2:.3f}.")
md_output.append(f"- OLS adjusted R-squared: {ols_adj_r2:.3f}.")
md_output.append("- Significance: + p < 0.10; * p < 0.05; ** p < 0.01; *** p < 0.001.")
md_output.append("- NBRM refers to a negative binomial regression model with estimated overdispersion.")
md_output.append("- ZIP refers to a zero-inflated Poisson model with an intercept-only inflation equation.\n")

with open("results/reporting_breadth_models.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md_output))

##########################################################################
## 12. Predicted values: AUM quartiles
##########################################################################

## For AUM quartiles, hold region at Europe and report language at English.
selected_region = "Europe"

aum_pred_df = pd.DataFrame({
    "assets_quartile": quartile_order,
    "region": selected_region,
    "english_report": 1
})

aum_pred_df["assets_quartile"] = pd.Categorical(
    aum_pred_df["assets_quartile"],
    categories=quartile_order,
    ordered=True
)

aum_pred_df["region"] = pd.Categorical(
    aum_pred_df["region"],
    categories=region_order,
    ordered=False
)

ols_aum_pred = ols_model.get_prediction(aum_pred_df).summary_frame(alpha=0.05)

aum_pred_df["predicted_topic_count"] = ols_aum_pred["mean"]
aum_pred_df["ci_low"] = ols_aum_pred["mean_ci_lower"]
aum_pred_df["ci_high"] = ols_aum_pred["mean_ci_upper"]

##########################################################################
## 13. Predicted values: region
##########################################################################

## For region, hold AUM at Q1 and report language at English.
selected_quartile = "Q1 (low)"

region_pred_df = pd.DataFrame({
    "assets_quartile": selected_quartile,
    "region": region_order,
    "english_report": 1
})

region_pred_df["assets_quartile"] = pd.Categorical(
    region_pred_df["assets_quartile"],
    categories=quartile_order,
    ordered=True
)

region_pred_df["region"] = pd.Categorical(
    region_pred_df["region"],
    categories=region_order,
    ordered=False
)

ols_region_pred = ols_model.get_prediction(region_pred_df).summary_frame(alpha=0.05)

region_pred_df["predicted_topic_count"] = ols_region_pred["mean"]
region_pred_df["ci_low"] = ols_region_pred["mean_ci_lower"]
region_pred_df["ci_high"] = ols_region_pred["mean_ci_upper"]

##########################################################################
## 14. Predicted-value figure
##########################################################################

sns.set_theme(style="white")

## Pastel colours consistent with Figures 1 and 2
pastel_palette = sns.color_palette("pastel", n_colors=8)

aum_color = pastel_palette[0]
region_color = pastel_palette[2]
edge_color = "#2F2F2F"
grid_color = "#F2F2F2"

fig, axes = plt.subplots(
    nrows=1,
    ncols=2,
    figsize=(12, 5.8),
    sharey=True,
    gridspec_kw={"width_ratios": [1, 1.25]}
)

ax1, ax2 = axes

##########################################################################
## 14.1 Panel A: Predicted reporting breadth by AUM quartile
##########################################################################

x_aum = np.arange(len(aum_pred_df))

ax1.errorbar(
    x=x_aum,
    y=aum_pred_df["predicted_topic_count"],
    yerr=[
        aum_pred_df["predicted_topic_count"] - aum_pred_df["ci_low"],
        aum_pred_df["ci_high"] - aum_pred_df["predicted_topic_count"]
    ],
    fmt="o",
    color=aum_color,
    ecolor=aum_color,
    markeredgecolor=edge_color,
    markeredgewidth=0.8,
    elinewidth=1.5,
    capsize=4,
    markersize=7,
    zorder=3
)

ax1.plot(
    x_aum,
    aum_pred_df["predicted_topic_count"],
    color=aum_color,
    linewidth=1.5,
    alpha=0.9,
    zorder=2
)

ax1.set_xticks(x_aum)
ax1.set_xticklabels(aum_pred_df["assets_quartile"], fontsize=9)

ax1.set_xlabel("AUM quartile", fontsize=11)
ax1.set_ylabel("Predicted number of topics", fontsize=11)

ax1.set_title(
    "Predicted reporting breadth by AUM quartile",
    fontsize=14,
    pad=20
)

ax1.text(
    -0.06,
    1.10,
    "a)",
    transform=ax1.transAxes,
    fontsize=13,
    fontweight="bold",
    ha="left",
    va="top",
    clip_on=False
)

for spine in ax1.spines.values():
    spine.set_visible(False)

ax1.tick_params(axis="both", length=0)
ax1.grid(axis="y", color=grid_color, linewidth=0.8)

##########################################################################
## 14.2 Panel B: Predicted reporting breadth by region
##########################################################################

x_region = np.arange(len(region_pred_df))

ax2.errorbar(
    x=x_region,
    y=region_pred_df["predicted_topic_count"],
    yerr=[
        region_pred_df["predicted_topic_count"] - region_pred_df["ci_low"],
        region_pred_df["ci_high"] - region_pred_df["predicted_topic_count"]
    ],
    fmt="o",
    color=region_color,
    ecolor=region_color,
    markeredgecolor=edge_color,
    markeredgewidth=0.8,
    elinewidth=1.5,
    capsize=4,
    markersize=7,
    zorder=3
)

ax2.set_xticks(x_region)
ax2.set_xticklabels(region_pred_df["region"], rotation=30, ha="right", fontsize=9)

ax2.set_xlabel("Region", fontsize=11)
ax2.set_ylabel("")

ax2.set_title(
    "Predicted reporting breadth by region",
    fontsize=14,
    pad=20
)

ax2.text(
    -0.06,
    1.10,
    "b)",
    transform=ax2.transAxes,
    fontsize=13,
    fontweight="bold",
    ha="left",
    va="top",
    clip_on=False
)

for spine in ax2.spines.values():
    spine.set_visible(False)

ax2.tick_params(axis="both", length=0)
ax2.grid(axis="y", color=grid_color, linewidth=0.8)

##########################################################################
## 14.3 Shared y-axis range
##########################################################################

all_ci_low = min(
    aum_pred_df["ci_low"].min(),
    region_pred_df["ci_low"].min()
)

all_ci_high = max(
    aum_pred_df["ci_high"].max(),
    region_pred_df["ci_high"].max()
)

y_lower = min(-0.6, all_ci_low - 0.25)
y_upper = max(7.2, all_ci_high + 0.25)

ax1.set_ylim(y_lower, y_upper)
ax2.set_ylim(y_lower, y_upper)

##########################################################################
## 14.4 Figure note and spacing
##########################################################################

note = (
    f"Note. Predicted values are based on the OLS model with HC3 robust standard errors "
    f"(R² = {ols_r2:.3f}; adjusted R² = {ols_adj_r2:.3f}). "
    f"The left panel holds region at {selected_region} and report language at English. "
    f"The right panel holds AUM at {selected_quartile} and report language at English. "
    "Vertical bars indicate 95% confidence intervals."
)

## Place the note below the plot area. 
## This avoids overlap with axis labels and rotated region labels.
## fig.text(
    ## 0.01,
    ## 0.035,
    ## note,
    ## ha="left",
    ## va="bottom",
    ## fontsize=9,
    ## style="italic",
    ## wrap=True
## )

fig.subplots_adjust(
    left=0.08,
    right=0.98,
    top=0.82,
    bottom=0.30,
    wspace=0.18
)

##########################################################################
## 15. Save figure
##########################################################################

fig_output = "results/reporting_breadth_predicted_values"

fig.savefig(f"{fig_output}.png", dpi=300, bbox_inches="tight", transparent=True)
fig.savefig(f"{fig_output}.pdf", dpi=300, bbox_inches="tight")

##########################################################################
## 16. Console output
##########################################################################

print("\nReporting breadth models saved.")
print("Markdown report: results/reporting_breadth_models.md")
print(f"Figure PNG: {fig_output}.png")
print(f"Figure PDF: {fig_output}.pdf")

## print("\nCount-model diagnostics:")
## print(count_diagnostics.to_string(index=False))

## print("\nCount-model information criteria:")
## print(count_model_fit.to_string(index=False))

## print("\nOLS model summary:")
## print(ols_model.summary())

## print("\nPoisson model summary:")
## print(poisson_model.summary())

## print("\nNegative binomial model summary:")
## print(nb_model.summary())

## print("\nZero-inflated Poisson model summary:")
## print(zip_model.summary())

## plt.show()
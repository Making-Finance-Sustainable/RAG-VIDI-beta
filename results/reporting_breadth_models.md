# Reporting breadth models

Outcome: number of sustainable-finance categories detected in each annual report.

The main model is an OLS regression with heteroskedasticity-robust HC3 standard errors. The count-model robustness checks include Poisson, negative binomial regression model (NBRM), and zero-inflated Poisson (ZIP) specifications. AUM is included as quartile dummies, with Q1 (low) as the reference category. The reference category for region is Europe. This choice is substantively motivated by the expectation that sustainable-finance reporting is more developed in Europe because of stronger regulatory and disclosure frameworks.

## Model estimates

| term                    | OLS       | OLS SE   | Poisson   | Poisson SE   | NBRM      | NBRM SE   | ZIP       | ZIP SE   |
|:------------------------|:----------|:---------|:----------|:-------------|:----------|:----------|:----------|:---------|
| Constant                | 2.328***  | (0.230)  | 0.802***  | (0.100)      | 0.813***  | (0.121)   | 0.837***  | (0.114)  |
| AUM quartile: Q2        | 0.120     | (0.256)  | 0.059     | (0.117)      | 0.047     | (0.119)   | 0.074     | (0.113)  |
| AUM quartile: Q3        | 0.417     | (0.277)  | 0.165     | (0.117)      | 0.160     | (0.117)   | 0.171     | (0.111)  |
| AUM quartile: Q4 (high) | 0.549+    | (0.317)  | 0.231+    | (0.132)      | 0.231+    | (0.124)   | 0.280*    | (0.118)  |
| Region: Africa          | -2.452**  | (0.817)  | -1.089**  | (0.399)      | -1.090*   | (0.532)   | -1.057*   | (0.526)  |
| Region: Americas        | -1.888*** | (0.239)  | -0.800*** | (0.108)      | -0.797*** | (0.098)   | -0.709*** | (0.095)  |
| Region: Asia-Pacific    | -0.307    | (0.332)  | -0.117    | (0.099)      | -0.114    | (0.117)   | -0.081    | (0.107)  |
| Region: Eurasia         | -0.408    | (1.067)  | -0.150    | (0.209)      | -0.150    | (0.363)   | -0.171    | (0.324)  |
| Region: Middle East     | 0.289     | (0.679)  | 0.027     | (0.159)      | 0.018     | (0.228)   | 0.036     | (0.208)  |
| English-language report | 0.953***  | (0.266)  | 0.365***  | (0.104)      | 0.355**   | (0.120)   | 0.329**   | (0.115)  |
| NB overdispersion alpha |           |          |           |              | 0.078+    | (0.047)   |           |          |



## ZIP inflation equation

The ZIP model uses an intercept-only inflation equation. The main estimates table reports the count equation.

| term               | ZIP inflation equation   | ZIP inflation equation SE   |
|:-------------------|:-------------------------|:----------------------------|
| Inflation constant | -2.657***                | (0.379)                     |



## Model fit

| Statistic          |      OLS |   Poisson |   NBRM |    ZIP |
|:-------------------|---------:|----------:|-------:|-------:|
| Observations       |  315     |     315   |  315   |  315   |
| R-squared          |    0.238 |           |        |        |
| Adjusted R-squared |    0.215 |           |        |        |
| AIC                | 1242.3   |    1205.3 | 1203.7 | 1199.1 |
| BIC                | 1279.9   |    1242.8 | 1244.9 | 1240.4 |



## Count-model diagnostics

| Diagnostic                        | Value                 |
|:----------------------------------|:----------------------|
| Poisson Pearson dispersion        | 1.360                 |
| Observed zeroes                   | 59                    |
| Observed zero share               | 0.187                 |
| Expected zeroes under Poisson     | 39.0                  |
| Expected zero share under Poisson | 0.124                 |
| Observed / expected zero ratio    | 1.513                 |
| Best count model by AIC           | Zero-inflated Poisson |
| Best count model by BIC           | Zero-inflated Poisson |



## Diagnostic interpretation

- The Pearson dispersion statistic indicates moderate overdispersion. The Poisson model remains useful as a parsimonious count-model robustness check, but the negative binomial model should also be inspected.
- The number of observed zeroes is higher than expected under the Poisson model. This provides some evidence that a zero-inflated specification may be relevant.
- The information criteria do not uniformly favour Poisson. AIC favours Zero-inflated Poisson and BIC favours Zero-inflated Poisson. The Poisson results should therefore be interpreted as a parsimonious robustness check rather than as the uniquely preferred count model.

## Notes

- Number of annual reports after topic cleaning: 319.
- Number of observations in the model dataset: 315.
- OLS R-squared: 0.238.
- OLS adjusted R-squared: 0.215.
- Significance: + p < 0.10; * p < 0.05; ** p < 0.01; *** p < 0.001.
- NBRM refers to a negative binomial regression model with estimated overdispersion.
- ZIP refers to a zero-inflated Poisson model with an intercept-only inflation equation.

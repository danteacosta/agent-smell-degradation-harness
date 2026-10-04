# Cross-check of scripts/h1b_agq.py with lme4 (run in the same container as validate.R).
# Reduced model: the four numeric requirements are dropped (their likelihood is 1 as
# beta_numeric -> +inf) and the project intercept, estimated at 0, is omitted.
library(lme4)
library(jsonlite)
d <- read.csv('/evidence/design.csv'); d$case <- factor(d$case)
out <- list(R = R.version.string, lme4 = as.character(packageVersion('lme4')))
fits <- list(reduced_42 = subset(d, numeric == 0), all_46_without_numeric = d)
for (name in names(fits)) {
  x <- droplevels(fits[[name]])
  fit <- glmer(y ~ context_cue + derived_state + memorized + (1 | case), data = x, family = binomial,
               nAGQ = 25, control = glmerControl(optimizer = 'bobyqa', optCtrl = list(maxfun = 200000)))
  ci <- tryCatch(confint(fit, parm = 'beta_', method = 'profile'), error = function(e) conditionMessage(e))
  out[[name]] <- list(n = nrow(x), logLik = as.numeric(logLik(fit)), fixef = as.list(fixef(fit)),
                      sd_case = as.data.frame(VarCorr(fit))$sdcor, profile = ci)
}
write_json(out, '/evidence/lme4-agq25-validation.json', pretty = TRUE, auto_unbox = TRUE, digits = 16)
print(out)

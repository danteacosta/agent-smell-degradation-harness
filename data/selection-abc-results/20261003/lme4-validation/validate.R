library(lme4)
library(jsonlite)
d <- read.csv('/evidence/design.csv'); d$case <- factor(d$case); d$project <- factor(d$project)
output <- list(R=R.version.string,lme4=as.character(packageVersion('lme4')),n=nrow(d))
for (name in c('full','without_numeric')) {
  terms <- if(name=='full') 'context_cue + numeric + derived_state + memorized' else 'context_cue + derived_state + memorized'
  formula <- as.formula(paste('y ~',terms,'+ (1|project) + (1|case)'))
  warnings <- character()
  fit <- withCallingHandlers(tryCatch(glmer(formula,data=d,family=binomial,nAGQ=1,control=glmerControl(optimizer='bobyqa',optCtrl=list(maxfun=200000))),error=function(e)e),warning=function(w){warnings <<- c(warnings,conditionMessage(w));invokeRestart('muffleWarning')})
  if(inherits(fit,'error')) { output[[name]]<-list(error=conditionMessage(fit),warnings=warnings);next }
  ciwarnings <- character()
  ci <- withCallingHandlers(tryCatch(confint(fit,parm='beta_',method='profile',oldNames=FALSE),error=function(e)e),warning=function(w){ciwarnings <<- c(ciwarnings,conditionMessage(w));invokeRestart('muffleWarning')})
  output[[name]] <- list(coefficients=as.list(fixef(fit)),odds_ratios=as.list(exp(fixef(fit))),logLik=as.numeric(logLik(fit)),variance=as.data.frame(VarCorr(fit)),singular=isSingular(fit),convergence=fit@optinfo$conv,warnings=warnings,profile_warnings=ciwarnings,profile=if(inherits(ci,'error')) NULL else ci,profile_error=if(inherits(ci,'error')) conditionMessage(ci) else NULL)
}
write_json(output,'/evidence/lme4-validation.json',pretty=TRUE,auto_unbox=TRUE,digits=16,na='null')
print(output)

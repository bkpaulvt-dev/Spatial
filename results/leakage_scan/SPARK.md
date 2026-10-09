# Candidate leakage lines: SPARK

Screening output; unreviewed. {'L1': 0, 'L2': 0, 'L3': 7, 'L4': 0, 'L5': 0}

## L3 (7)
- `R/utilties.R:131` `if (sum(is.na(Pvals))>0){`
- `R/sparkx.R:55` `if(sum(is.na(GeneNames))>0){GeneNames[is.na(GeneNames)]<- "NAgene"}`
- `R/sparkx.R:122` `if(sum(is.na(geneName))>0){geneName[is.na(geneName)]<- "NAgene"}`
- `R/sparkx.R:309` `if (sum(is.na(Pvals))>0){`
- `R/vctesting.R:133` `if((class(model1) != "try-error") & (!any(is.na(model1$Y)))){`
- `R/vctesting.R:309` `if((class(model1) != "try-error") && (!any(is.na(model1$Y)))){`
- `R/vcestimating.R:112` `if((class(model1) != "try-error")&&(!any(is.na(model1$Y)))){`


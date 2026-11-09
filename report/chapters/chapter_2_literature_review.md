# Chapter 2 - Literature review

(Keys refer to `report/references.bib`; confirm bibliographic details before submission.)

## 2.1 Fraud detection with machine learning
Surveys by Ngai et al. (2011) and Bhattacharyya et al. (2011) establish supervised learning (logistic regression, trees, ensembles) as the
standard approach to card and financial fraud. Random Forests (Breiman, 2001) and gradient boosting, notably XGBoost (Chen & Guestrin, 2016), are
consistently strong on tabular data. Bahnsen et al. (2016) show that engineered behavioural features (periodic and history-based aggregates)
improve detection more than model choice alone, motivating the history features used here.

## 2.2 Class imbalance and evaluation
Extreme imbalance makes accuracy uninformative. Davis & Goadrich (2006) and Saito & Rehmsmeier (2015) argue that precision-recall analysis is more
informative than ROC when positives are rare. Dal Pozzolo et al. (2015) show that resampling alters posterior probabilities, which supports using
class weights and keeping probabilities usable for risk tiers. Chronological evaluation avoids optimistic bias from temporal leakage.

## 2.3 Anomaly detection
Chandola et al. (2009) survey anomaly detection. Isolation Forest (Liu et al., 2008) and Local Outlier Factor (Breunig et al., 2000) need no labels, suiting
delayed-label or novel-attack settings, typically at lower accuracy than supervised models.

## 2.4 Hyper-parameter optimisation
Random search is more efficient than grid search in the same budget (Bergstra & Bengio, 2012); it is used with average-precision scoring.

## 2.5 Trust in electronic commerce and FinTech
Trust is multi-dimensional: competence, benevolence, integrity (McKnight et al., 2002), and interacts with perceived risk and usefulness
(Davis, 1989; Gefen et al., 2003; Pavlou, 2003). Perceived security and privacy assurance are central antecedents; reliability and transparency
shape continued use. These inform the five survey dimensions.

## 2.6 Measurement and privacy
Likert scales (Likert, 1932) are assessed with Cronbach's alpha (Cronbach, 1951). k-anonymity (Sweeney, 2002) limits re-identification through
quasi-identifiers such as age band and education.

## 2.7 Gap
Prior work rarely joins (a) model-level security performance, (b) consumer-perceived trust, and (c) live operational monitoring in a reproducible artefact.
This project addresses that gap while acknowledging that the combination index is exploratory.

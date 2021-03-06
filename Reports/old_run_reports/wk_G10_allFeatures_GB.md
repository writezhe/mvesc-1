# Report for wk G10 allFeatures GB
weekly update Grade 10 model (xc)

### Model Options
* label used: definite
* initial cohort grade: 9
* test cohorts: 2011
	 * 128 positive examples, 1881 negative examples
* train cohorts: 2008, 2009, 2010
	 * 96 postive examples, 3046 negative examples
* cross-validation scheme: leave cohort out
	 * searching n_estimators in 500
	 * chose n_estimators = 500
	 * searching learning_rate in 0.01
	 * chose learning_rate = 0.01
	 * searching subsample in 0.5
	 * chose subsample = 0.5
	 * searching max_depth in 30
	 * chose max_depth = 30
	 * using custom_precision_10
* imputation strategy: median plus dummies
* scaling strategy: robust

### Features Used
* grades
	 * gpa_gr_9
* snapshots
	 * gifted_gr_9
	 * oss_gr_9
	 * disability_gr_9
	 * limited_english_gr_9
	 * discipline_incidents_gr_9
	 * district_gr_9
	 * special_ed_gr_9
	 * days_absent_gr_9
	 * iss_gr_9
	 * days_absent_unexcused_gr_9
	 * disadvantagement_gr_9
* oaa_normalized
	 * eighth_science_normalized
	 * eighth_math_normalized
	 * eighth_read_normalized
* demographics
	 * ethnicity
	 * gender
* mobility
	 * n_cities_to_gr_9
	 * street_transition_in_gr_9
	 * avg_city_change_to_gr_9
	 * n_districts_to_gr_9
	 * city_transition_in_gr_9
	 * avg_address_change_to_gr_9
	 * n_records_to_gr_9
	 * n_addresses_to_gr_9
	 * avg_district_change_to_gr_9
	 * district_transition_in_gr_9
	 * mid_year_withdraw_gr_9

### Performance Metrics
on average, model run in 121.57 seconds (1 times) <br/>precision on top 15%: 0.1788 <br/>precision on top 10%: 0.2289 <br/>precision on top 5%: 0.2574 <br/>recall on top 15%: 0.4219 <br/>recall on top 10%: 0.3594 <br/>recall on top 5%: 0.2031 <br/>AUC value is: 0.7499 <br/>![wk_G10_allFeatures_3_GB_pr_vs_threshold.png](figs/wk_G10_allFeatures_3_GB_pr_vs_threshold.png)
![wk_G10_allFeatures_3_GB_score_dist.png](figs/wk_G10_allFeatures_3_GB_score_dist.png)
![wk_G10_allFeatures_GB_pr_vs_threshold.png](figs/wk_G10_allFeatures_GB_pr_vs_threshold.png)
![wk_G10_allFeatures_3_GB_confusion_mat_0.3.png](figs/wk_G10_allFeatures_3_GB_confusion_mat_0.3.png)
![wk_G10_allFeatures_GB_confusion_mat_0.3.png](figs/wk_G10_allFeatures_GB_confusion_mat_0.3.png)
![wk_G10_allFeatures_GB_precision_recall_at_k.png](figs/wk_G10_allFeatures_GB_precision_recall_at_k.png)
![wk_G10_allFeatures_3_GB_precision_recall_at_k.png](figs/wk_G10_allFeatures_3_GB_precision_recall_at_k.png)
![wk_G10_allFeatures_GB_score_dist.png](figs/wk_G10_allFeatures_GB_score_dist.png)

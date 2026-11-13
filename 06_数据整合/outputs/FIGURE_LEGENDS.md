# Figure legends and source data

## Figure A | Housing and educational facilities

An offline OSM reference map juxtaposes the mapped subset of residences and primary/kindergarten campuses. Residence shading encodes archived comparable platform sale references, in 10,000 CNY/m². Reference months differ. White residence markers indicate missing or non-comparable sale evidence; the Liede Garden diamond represents a phase-5 reference, distinct from the transport-origin POI. Rental examples retain separate units and unmatched dwelling sizes. Campus shapes encode stage and colors encode ownership category. Grey crosses are unresolved map candidates and are excluded from accepted campus counts. Approximate GCJ-02 conversion is flagged in source data. No price surface, income classification, school quality inference or geographic census is claimed. OSM attribution: © OpenStreetMap contributors, ODbL.

Source data: `figure_source_data/figure_A_housing.csv`, `figure_A_campuses.csv`, `figure_A_unresolved.csv`. These contain canonical IDs and source references; full observations are in `data/housing_observations.csv`, `data/positions.csv`, `data/source_registry.csv`.

## Figure B | Housing, admission channels and modeled walks

Nine route/channel comparisons describe three purposeful residential cases. Address-linked schools are conditional on full eligibility verification. Xian Cun is one migrant-points listed choice; it is neither an allocation nor an established nearest eligible destination. Nanguo Primary is also listed for the separate HK/Macao channel. No actual household admission, commute or fee burden was observed. Housing labels describe distinct contextual evidence, not household income. Times are archived 2026 Amap POI-to-POI estimates, without confirmed gates. There are no statistical tests or population confidence intervals.

Source data: `figure_source_data/figure_B_comparisons.csv` and `figure_B_housing_context.csv`, linked through route, housing observation, residence and rule IDs to `data/transport_routes.csv`, `data/housing_observations.csv`, `data/admission_rules.csv` and `data/source_registry.csv`.

# Integrated research figure contract

Backend: Python / matplotlib exclusively; UTM zone 49N (EPSG:32649) is used only for a local metric display of WGS84 points. This is a course evidence package, not a journal submission specification.

## Figure A - Housing × education

- Claim: archived housing cost references and educational facilities can be juxtaposed for the mapped subset; coverage and comparability remain incomplete.
- Evidence: a main OSM-reference map of residences and campuses, with subordinate housing metric / missingness information. Campus stage and ownership use separate encodings.
- Archetype: asymmetric mixed-modality figure, with the map as the hero panel.
- Housing price, rent, policy rent and unverified rights remain distinct. No interpolation, regional price surface, income classification, density or causal effect is estimated.
- The Liede phase-5 reference and transport-origin point remain different positions. Unresolved candidates use separate marks and never inherit a confirmed entity link.

## Figure B - Housing × admission × accessibility

- Claim: at the same sampled residential origin, different conditional or listed channels refer to different modeled walks.
- Evidence: nine residence/channel comparisons from the original route model; district allocation for renters and actual admission remain unknown.
- Archetype: quantitative comparison grid, three origins sharing a minutes axis.
- Xian Cun is one listed migrant-points choice. No nearest-eligible-school, assignment, probability, household average or actual commute claim is made.

## Export and review

- Intended use: standalone review and insertion by the poster/report team; no existing poster is changed.
- Formats: editable SVG and PDF, 300-dpi PNG preview, source CSV and explanatory legends. Fixed SVG hash salt and absent PDF timestamps support repeatability.
- Layout: approximately 300 mm wide for A and 280 mm for B; ordinary text at least 9 pt. White background; restrained blue/green/amber palette; marker shapes retain meaning in grayscale.
- Statistics: purposeful case sample, no hypothesis tests, confidence intervals, error bars or p-values. Sample/coverage counts derive from current output tables, not hardcoded completeness assumptions.
- QA: inspect Python-produced PNGs and text extents, verify sources and labels, check exported SVG text and PDF structure. Numerical coordinate round-trip checks do not establish geographic field accuracy.

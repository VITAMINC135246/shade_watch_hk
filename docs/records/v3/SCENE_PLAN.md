# Predeclared multi-tile regional pilots

Prepared 2026-10-08 (Hong Kong). **Not executed.** Each region is a 2 × 2
block (1.5 × 1.2 km; 7.2 million native pixels). DSM support extends 1 km
beyond every target tile. Geographic scene labels are hypotheses, not a formal
terrain/land-use survey. Coarse height samples in the profile only inspect input
DSM and are not shade accuracy or full coverage evidence.

| Region | Scene hypothesis | Native tiles |
| --- | --- | --- |
| Central / Mid-Levels | dense high-rise and urban slope | `11SW8D`, `11SW9C`, `11SW13B`, `11SW14A` |
| Mong Kok | dense urban plain | `11NW19B`, `11NW20A`, `11NW19D`, `11NW20C` |
| Tai Mo Shan | high mountain and ridge | `7SW1B`, `7SW2A`, `7SW1D`, `7SW2C` |
| Yuen Long | lowland and mixed development | `6NW9D`, `6NW10C`, `6NW14B`, `6NW15A` |
| Lantau South | steep mountain and coast | `9SE24C`, `9SE24D`, `13NE4A`, `13NE4B` |
| Cheung Chau | island and missing-water support | `14NW19B`, `14NW20A`, `14NW19D`, `14NW20C` |
| HKUST / Clear Water Bay | coastal slope and baseline continuity | `12NW6C`, `12NW6D`, `12NW11A`, `12NW11B` |

These expand V3 C15 (at least two contrasting regional pilots) into seven scenes.
V1/V2 acceptance did not require territory-representative terrain sampling.
Use exact names, timestamps, bounds and coarse-data findings in
`config/v3/pilots.template.json`. Do not replace failed samples after seeing outcomes.

The island/coast blocks intentionally include missing target/support cells where
present. Report quality flags; never fill water with zero elevation. Regional
pilots do not prove administrative boundary coverage or observational accuracy.

# Coastline and sea-surface source data (Lands Department iB5000)

Read-only source input for the planned sea-support policy. Everything in this
folder except this README is ignored by Git. Do not edit, re-export or
reproject files in place; derived products belong in a new, versioned
directory outside `data/raw/`.

## Provenance

- Dataset: Digital Topographic Map iB5000, Survey and Mapping Office,
  Lands Department, HKSAR Government.
- Obtained from the CSDI Portal / DATA.GOV.HK dataset page
  (https://data.gov.hk/en-data/dataset/hk-landsd-openmap-development-hkms-digital-b5k;
  CSDI dataset ID `landsd_rcd_1637224243141_96556`), "Seamless FGDB" and
  "FGDB Data Dictionary & Resource File".
- Downloaded by the user on 2026-10-29. Dataset page revision date:
  2026-10-11; FGDB table timestamps: 2026-10-12.
- Terms: the DATA.GOV.HK / CSDI terms of use shown on the dataset page.
  `resources_iB5000_FGDB/LICENSE.txt` is the SIL Open Font Licence for a
  bundled font, not the data licence.

## Layout

- `ib5000_seamless_20261012/iB5000.gdb/`: seamless Esri File Geodatabase
  (411 files, about 326 MB).
- `resources_iB5000_FGDB/`: data dictionary
  (`iB5000 Data Dictionary - FGDB v1.3.pdf`, SHA-256
  `edce002dd9390a2e2a49e41767e6dfef41278cb6e3c010756d24da5461c88aef`),
  catalogue, metadata (`iB5000.xml`, `iB5000.html`), FAQ, ArcGIS template
  and fonts.

## Layers relevant to Shade Watch

- `Hydrography/HydrographyPoly`, `FEATURESUBTYPE = 3` (CoastLine):
  `SEF` = Sea Fill (sea surface), `LAF` = Coastline and Land Fill (land).
- `Hydrography/HydrographyLine`, `FEATURESUBTYPE = 2` (CoastLine_Line):
  `HWM` high water mark, `SEW` seawall/pier/dolphin, and related codes.
  Reference only.
- `HydrographyPoly`, `FEATURESUBTYPE = 1`, `FEATURECODE = RES`: reservoirs.
- Coordinate system: Hong Kong 1980 Grid (same grid as the CEDD DSM,
  EPSG:2326). Map features are generalized to 1:5000 scale (metadata); no
  numeric positional accuracy is stated.

## Planning check (2026-10-29; diagnostic only, not acceptance evidence)

Performed read-only in a separate Claude workspace with a minimal FGDB reader
and 0.5 m pixel-centre rasterization. Production work must re-derive these
figures with a standard library and record any differences.

- Feature counts: `HydrographyPoly` 7,116 rows (`LAF` 1,111; `SEF` 345);
  `HydrographyLine` 56,705 rows (`HWM` 4,093; `SEW` 1,771). Codes match the
  data dictionary.
- `LAF` total area 1,114.7 km^2 (attribute `Shape_Area`).
- Cheung Chau 2x2 target plus 1 km halo (23 DSM tiles): of 34,647,367 DSM
  NoData pixels, 34,617,537 lie in `SEF` minus `LAF`; 29,830 lie in `LAF`
  (coastal slivers and two harbour piers). 357,470 DSM-valid pixels lie in
  `SEF` (median elevation 1.67 m; intertidal beaches, rocks, breakwaters).
- Territory, 25 m overview: inside DSM tile footprints, 11.8 km^2 is neither
  `LAF` nor `SEF` (Shenzhen side of the northern boundary). Nine lattice
  cells with land but no DSM file are 100% inside reservoir polygons
  (Plover Cove 8, High Island 1).
- CEDD 2020 DSM vertical datum: HKPD; horizontal HK1980 Grid; stated accuracy
  +/-0.1 m vertical on flat open terrain, +/-0.3 m horizontal (95%); acquired
  2019-12-20 to 2020-02-02. Source:
  `../dsm/Metedata for LiDAR Data (2020).html`.

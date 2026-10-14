# FIT3179 Data Visualisation 2: Birds of Melbourne

Project memory for Claude Code. Started as a handoff from a claude.ai chat (10 Oct 2026), then checked against the
real folder and updated on 11 Oct 2026. Do not invent data; check every claim against the data files.

## Working style the student wants
- Be direct and honest. No flattery. Challenge weak reasoning, point out risks and wasted time.
- When debugging, explain the cause so the student learns (they must defend everything in a Week 12 interview).
- Verify annotations against the data before writing them. Earlier, a subtitle overstated a pattern and had to be corrected.
- **Build only what the student asks for. Don't decide page layout, chart placement or text for them** (14 Oct 2026:
  a full layout with every chart placed was rejected and stripped back). Suggest, then let them decide.

## Assignment essentials (Monash FIT3179, Semester 2 2026)
- Due **Sunday 25 Oct 2026, 11:55 PM**. Late penalty 5%/day. Interview in the Week 12 studio.
- Must use **Vega-Lite or Vega**. Final product: ONE publicly accessible GitHub Pages URL, one scrollable page,
  no buttons/links that swap major sections (show/hide is fine), no horizontal scroll on a small laptop.
- JSON spec for every chart must be in the repo, human-readable (formatted, not inline in HTML).
- **At least 3 different map idioms** (two choropleths = one idiom). Fewer than 3 caps "Idioms and complexity" at 4% of 8%.
- **More than 10 charts** (small multiples count as one). HD needs **8+ advanced idioms**.
- Staff "single source of truth" list. BASIC: bar (incl. stacked, 100%, grouped), dot plot (not connected),
  line (incl. indexed), area, pie/donut, scatter, bubble, packed bubble. Everything else is ADVANCED, e.g. heatmap,
  jitter plot, lollipop, slope chart, bump chart, waffle, treemap, Sankey, stream graph, connected dot plot, butterfly.
  Staff also confirmed on Ed: **all map idioms are advanced**. Misused advanced idioms are not counted and may be penalised.
- Data: real, reliable, most recent available; **combine two different sources**; total download size a few MB.
- Audience: average Australian. No jargon, no stats knowledge assumed. Plain-English labels.
- Must show authorship, date, data sources with URLs, and **acknowledge AI use**.
- Sketch: hand-drawn A4 (digital = 0 per brief; student asked staff on Ed in thread "Sketch on an Ipad", check the answer).
  The final page must match the sketch. The sketch was NOT finished as of 11 Oct 2026.

## Story (student's chosen structure, 11 Oct 2026)
Domain: citizen science. Main story: **who and where people report birds**, not where birds "are".
The student chose this order and naming over a suggested alternative (moving Act 3 before Act 2): keep it.
1. **Where are they reported?** States rate map, Melbourne suburbs rate map, raw-counts (proportional symbol) map.
2. **What is reported?** Lollipop of 15 most reported species; slope chart (records vs birds counted); ridgeline of
   seasonal birds; bump chart of monthly ranks.
3. **What impacts bird observations?** Canopy dot map; trees-vs-records connected dot plot (City of Melbourne,
   iNaturalist only). Wording on the page must say "linked to", not "causes": parks have trees and paths and visitors.
4. **Who reports them?** Observer jitter plot; weekday x hour heatmap (iNaturalist only).
5. Closing (from the earlier plan): what the data can't tell you (eBird hotspot pins, records are not birds, observer
   effort), stream graph of records by source (TODO), possible buffer chart of the hotspot finding; sources, author, date.

## Time window: calendar year 2024 (decided 11 Oct 2026)
- The first download (calendar 2025) had **no eBird records Sep-Dec 2025**: eBird's 2025 data in the ALA stops in
  August, while BirdLife and iNaturalist cover all 12 months. eBird is ~80% of records, so 2025 totals were skewed.
- Chosen fix: use **1 Jan - 31 Dec 2024**, where every source is complete. Checked with the ALA API on 11 Oct 2026
  (Victoria, same filters as the download):

  | Source | 2024 records | Smallest month |
  |---|---|---|
  | eBird Australia | 2,111,128 | 115,588 (Jul) |
  | BirdLife Australia, Birdata | 234,864 | 13,760 (Jun) |
  | iNaturalist Australia | 78,995 | 4,472 (Jul) |
  | All sources | 2,427,834 | |

- Say on the page why 2024 is used: it is the latest full year, because eBird's 2025 records stop in August.
- Rejected: Jan-Aug 2025 (drops ~40% of Birdata and iNaturalist records), Sep 2024-Aug 2025 (complete, but a confusing
  label for a general reader), keep 2025 and disclose (charts stay skewed).
- Consequence: every data file and every hard-coded annotation number in the specs had to be regenerated for 2024
  (done 11 Oct 2026; all files are now `_2024`).

## Folder layout
```
Fit3179 Data Visualization/
  raw_data/                         # raw downloads, OUTSIDE the repo (GitHub rejects files over 100 MB)
    ala_2024_birds_vic/ + .zip      # 2024 ALA download (2.8 GB CSV, 442 MB zip)
    ala_2025_birds_vic/ + .zip      # OLD 2025 download, superseded; can be deleted once the 2024 pipeline works
    Geopackage_2021_G01_VIC_GDA2020.zip   # ABS 2021 Census G01, Victoria
    abs_g01_vic/G01_VIC_GDA2020.gpkg      # the same, unzipped (used by build_data.py)
    work_<year>/                    # build_data.py cache: joined Melbourne records, species common names
  Fit3179birds/                     # project root = future GitHub repo
    index.html                      # final single page, being laid out by the student (see Next steps 5)
    css/style.css                   # page styles (currently just the 3-column grid)
    preview.html                    # test page that embeds every spec: DELETE before submission
    lollipop.html, suburbs.html     # test pages: DELETE before submission
    Map1_australiabirdsper1000.json # exact duplicate of js/map_states.vl.json: delete
    js/*.vl.json                    # one spec per chart
    data/*                          # small aggregated files only
    processing_scripts/*.py         # see "Processing scripts"
    .venv/                          # Python 3.14: pandas, geopandas, shapely, pyogrio, pyproj (gitignored)
    .claude/launch.json             # local server "site" on port 8000 (gitignored)
```
- Data URLs in specs are **relative to index.html**, e.g. `data/x.csv`, even though specs live in `js/`.
- Library tags: `vega@6`, `vega-lite@6`, `vega-embed@7` from cdn.jsdelivr.net. Embed: `vegaEmbed('#id', 'js/x.vl.json')`.
- Test with VS Code Live Server (open the folder via File > Open Folder) or `python3 -m http.server 8000` in the
  project root. Blank chart = check the browser console for a 404.
- Never publish observer names. Observer IDs are anonymised (`obs00001`).
- Not a git repo yet. `.gitignore` already excludes .venv, zip, gpkg, .claude, .DS_Store.
- The disk is nearly full (about 10 GB free on 11 Oct 2026). Don't keep extra copies of raw CSVs.

## Data sources
1. **Atlas of Living Australia (ALA)** occurrence download, **2024**. Filters: Lifeform Birds, Country Australia,
   State Victoria, Record type Human observation, eventDate 2024-01-01 to 2024-12-31, data profile "ALA General"
   (the default quality filters). Pre-filtered search (2,427,834 records on 11 Oct 2026):
   https://biocache.ala.org.au/occurrences/search?q=*%3A*&fq=stateProvince%3A%22Victoria%22&fq=speciesGroup%3A%22Birds%22&fq=country%3A%22Australia%22&fq=basisOfRecord%3A%22HUMAN_OBSERVATION%22&fq=eventDate%3A%5B2024-01-01T00%3A00%3A00Z%20TO%202024-12-31T23%3A59%3A59Z%5D&qualityProfile=ALA
   **DOI: https://doi.org/10.26197/ala.2f2e2a93-a954-4910-b216-1ecc3ce18693** (downloaded 11 Oct 2026, 2,427,834
   records; the README confirms the filters above). Licences per the download's citation.csv: eBird CC0,
   BirdLife Birdata CC BY-NC 3.0, iNaturalist mixed per record; cite each provider (see citation.csv).
   (Old 2025 download, superseded: https://doi.org/10.26197/ala.ddc1462c-bf27-46ad-9547-4b1f12543ee1 , 1,713,114 records.)
2. **State bird counts, 2024**: ALA API, same filters without the state filter, faceted by `stateProvince`,
   queried 11 Oct 2026. NSW 2,616,590; Vic 2,427,834; Qld 2,314,121; WA 699,364; SA 510,397; Tas 469,118;
   ACT 345,652; NT 333,959. ALA keeps adding records, so counts drift slightly (2025 counts rose ~0.2% from 8 to 11 Oct).
3. **ABS estimated resident population, 30 June 2024**, by state: ABS Data API dataflow `ERP_Q` (Quarterly Population
   Estimates), accessed 11 Oct 2026. NSW 8,492,050; Vic 6,950,961; Qld 5,571,890; WA 2,978,147; SA 1,882,164;
   Tas 574,765; ACT 478,430; NT 260,884; Australia 27,194,286.
   Cite as ABS, National, state and territory population: https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population
4. **ABS 2021 Census GeoPackage, G01, Victoria (GDA2020)**: suburb (SAL) boundaries + `Tot_P_P` population,
   plus Greater Melbourne (GCCSA 2GMEL) boundary. CC BY 4.0. Suburb-level population only exists from the Census.
5. State boundaries: github.com/rowanhogan/australian-states. **Checked 11 Oct 2026: the repo has NO licence**, so there
   is no right to reuse it. Replace with ABS ASGS 2021 state (STE) boundaries (CC BY 4.0) before submission.
6. Planned: City of Melbourne **Tree Canopies 2021 (Urban Forest)**, CC BY 4.0, dataset id `tree-canopies-2021-urban-forest`,
   https://data.melbourne.vic.gov.au/explore/dataset/tree-canopies-2021-urban-forest/ . 57,980 canopy polygons (public +
   private land) from 2021 multispectral imagery; the newest canopy layer published (checked 11 Oct 2026). Only geometry,
   no attributes. Pixel-traced outlines (~136 vertices each): GeoJSON export ~340 MB, so it must be simplified or
   gridded before use. Exports: `.../api/explore/v2.1/catalog/datasets/tree-canopies-2021-urban-forest/exports/{geojson,shp,parquet}`.
   City of Melbourne boundary = ABS LGA `LGA24600` (37.5 km²) in the GeoPackage already downloaded.
   **Downloaded 11 Oct 2026** to `../raw_data/com_canopy_2021/canopy_2021_{west,east}.zip`. The shapefile export
   silently stops at 50,000 shapes, so it was fetched in two halves split at longitude 144.95 (`where=in_bbox(geo_point_2d,
   -38.5, 144.0, -37.0, 144.95)` and `not in_bbox(...)`): 26,069 + 31,911 = 57,980. Imagery date 11 Aug 2021.
   Computed tree cover of the whole City area (incl. river, roads, port): **11.3%** (4.25 km² of 37.54 km²).
   Council context (secondary sources, cite the council's Urban Forest Strategy if used): public-realm (streets and
   parks) canopy 22% baseline in 2012, target 40% by 2040; a 2014 whole-city estimate was 13%. Don't compare 11.3%
   with the 22% figure: different area.
   Also available: "Trees, with species and dimensions (Urban Forest)", 82,064 council trees, updated Sep 2025.

### ALA API notes
- Base: `https://biocache-ws.ala.org.au/ws/occurrences/search?q=*:*&fq=...&qualityProfile=ALA&pageSize=0&facets=<field>`
- Field names: `stateProvince`, `speciesGroup`, `country`, `basisOfRecord`, `eventDate` (not `occurrenceDate`),
  `dataResourceName`, `month`. Date filter: `eventDate:[2024-01-01T00:00:00Z TO 2024-12-31T23:59:59Z]`.
- With `qualityProfile=ALA` the API reproduced the 2025 download (eBird 1,385,763 in both). Without it, counts are ~8% higher.

## Known data issues (must be handled on the page)
- **Subspecies split species names** (e.g. "Southern Victoria Australian Magpie"). Always aggregate by the `species`
  column (binomial) and map to the most common species-level vernacular name. Display "Spotted Dove" (ALA:
  Spotted Turtle-dove) and "Common Blackbird" (ALA: Eurasian Blackbird).
- **Observer and time-of-day exist only for iNaturalist.** eBird has no observer or time; Birdata lists every record
  as "Birds Australia". Observer/time charts must be labelled iNaturalist-only.
- eBird makes one record per species per checklist: **records are not sightings and not birds**.
- **eBird locations are hotspot points, not where the bird was.** City of Melbourne 2024: eBird 64,562 records at only
  474 distinct points (median coordinate uncertainty 1,000 m); one point, Royal Botanic Gardens Melbourne, holds 19,156
  (30%); Royal Park's two hotspots 11,605 + 10,442. iNaturalist: 3,396 records at 2,927 points, median uncertainty 10 m.
  Birdata: 3,174 at 81 survey sites. So fine-scale comparisons (records vs tree canopy) must use iNaturalist only.
  Suburb-level counts are mostly fine (hotspots sit inside the park they name) but a hotspot near a border can put
  thousands of records in one suburb. Good material for the "what the data can't tell you" section.
- `individualCount` exists for ~91% (eBird, Birdata). "Birds counted" can double-count the same flock.
- Records per 1,000 residents uses 2021 Census population with 2024 records; say so on the page.
- Suburbs under 1,000 residents are greyed (`minPop` param).
- Checked on the 2024 data (11 Oct 2026):
  - Cocoroc (Western Treatment Plant) 57,416 records, 0 residents; Braeside 27,494 records, 25 residents.
  - **Somers** now has the highest rate (4,113 per 1,000; 7,637 records, 1,857 residents; ~25% Birdata surveys,
    likely Coolart Wetlands, unverified). Parkville is 2nd (3,944). Parkville's records are common wild birds
    (Noisy Miner, Rainbow Lorikeet, Red Wattlebird, Magpie-lark, Magpie, Myna; 91% eBird), not zoo exhibits.
  - **Monday 12pm heatmap spike (987 records) is one person**: anonymised observer obs00032 made 421 of them, across
    21 different Mondays at varied times (not a batch upload or a default time). Without them the cell is 566.
    obs00032 made 853 of their 1,479 records on Mondays. The heatmap subtitle now says this.
  - iNaturalist spike 20-22 Sep 2024 (~450-500 records a day, 7,404 in Sep vs ~3,000 usual). Cause not checked
    (maybe a bioblitz event): verify before annotating.
  - eventTime has explicit +10:00/+11:00 offsets, so hours are local time.
- ALA processed `eventDate` can shift dates; date part + `eventTime` (local) were used for weekday/hour.
- Slope chart: the legend group "Reported often, usually seen in small numbers" wrongly included Rainbow Lorikeet
  (4th by birds counted). Fix the grouping and labels when regenerating.

## Key numbers (2024, from build_data.py output; re-verify after any rerun)
- Victoria 2,427,834 records; Greater Melbourne 1,060,628 (eBird 912,689; Birdata 103,265; iNaturalist 43,606).
- 572 suburbs, 141 greyed (<1,000 residents), median rate 65. Tarneit 388 records, 56,370 residents.
- Top 5 by records: Cocoroc 57,416; Bundoora 36,254; Altona 30,298; Parkville 27,900; Braeside 27,494.
- Top species: Australian Magpie 39,060 (3.7%), Rainbow Lorikeet, Little Raven, Noisy Miner, Magpie-lark,
  Red Wattlebird, Common Myna (7th, introduced), Welcome Swallow, Superb Fairy-wren, Pacific Black Duck,
  Spotted Dove (11th, introduced). By birds counted: Eurasian Coot 1st (677,279), 15th by records;
  Australian Shelduck 3rd by birds, 111th by records. Welcome Swallow is 8th both ways.
- iNaturalist Melbourne: 2,509 observers; top observer 4,246 (9.7%, ~1 in 10); top 1% (25 people) 44.6%;
  top 10% 79.7%; 972 made one record. Average weekend day +23% vs average weekday; 1.2% before 7am.
- States (per 1,000): NT 1,280.1, Tas 816.2, ACT 722.5, Qld 415.3, Vic 349.3, NSW 308.1, SA 271.2, WA 234.8.

## Charts: status (11 Oct 2026)
All 8 specs use the 2024 data and render in a browser with no errors (checked with preview.html). Every annotation
number was cross-checked against the data files. The `_2025` data files were moved to the Trash.
**Wording is still Claude's/the chat's: the student must rewrite titles and subtitles in their own voice.**

| Chart | Spec | Data | Idiom | Status |
|---|---|---|---|---|
| States rate map | map_states.vl.json | au_states.geojson, state_bird_records_2024.csv | choropleth | built, 2024 |
| Suburb rate map | map_suburbs.vl.json | melb_suburbs.geojson, melb_suburb_bird_records_2024.csv | choropleth | built, 2024; callout now Somers (was Parkville) |
| Raw counts map | map_proportional.vl.json | melb_suburbs.geojson, melb_suburb_points_2024.csv | proportional symbol | built, 2024 |
| Top 15 species | lollipop_species.vl.json | melb_top15_species_2024.csv | lollipop | built, 2024 |
| Records vs birds | slope_records_vs_birds.vl.json | melb_records_vs_birds_rank_2024.csv | slope | built, 2024; legend groups fixed (3 groups) |
| Weekday x hour | heatmap_weekday_hour.vl.json | inat_weekday_hour_2024.csv | heatmap | built, 2024; Monday-noon line added |
| Observers | jitter_observers.vl.json | inat_observer_records_2024.csv | jitter | built, 2024; log x-axis since 11 Oct (on a linear 0-5,000 axis 99.6% of dots sat in the leftmost 50 px); labels above the dots with leader lines |
| Canopy + iNat records | map_canopy_dots.vl.json | com_outline.geojson, com_canopy_grid_2021.csv, com_inat_points_2024.csv | dot map over a tree-cover grid (3rd map idiom) | built 11 Oct |
| Trees vs records by CoM suburb | dotplot_canopy_records.vl.json | com_suburb_canopy_records_2024.csv | connected dot plot | built 11 Oct; Carlton's two dots overlap (6.3% both) |
| Monthly species ranks | bump_monthly_ranks.vl.json | melb_species_month_rank_2024.csv | bump | built 11 Oct; ranks among the 10 birds shown (1-10, every slot filled); `rank_all` (among all species, up to 16th) is in the tooltip. Highlights Common Myna (10th Apr -> 2nd Dec), Red Wattlebird (9th Feb -> 4th Oct-Dec), Welcome Swallow (between 10th and 7th). Little Raven (2nd Apr-Oct, 6th in summer) is a cleaner alternative highlight |
| Seasonal birds | ridgeline_seasonal.vl.json | melb_seasonal_species_2024.csv | ridgeline | built 11 Oct; 3 most seasonal birds per season (500+ records), effort-adjusted (share of each month's records) |
| Records by source over the year | - | melb_source_month_2024.csv (ready) | stream graph | TODO |
| Keen vs casual observers | - | - | butterfly | not built: no meaningful difference (~1 pp in 2025 data) |
| Bird groups | - | - | waffle | removed 11 Oct 2026 by the student: didn't fit the story (spec, data and script step deleted) |

Built: **11 charts, 10 distinct advanced idioms** (choropleth, proportional symbol, dot map, lollipop, slope, ridgeline,
bump, connected dot plot, jitter, heatmap). Passes "more than 10 charts" with no spare: the stream graph (closing)
would give one spare; a bar chart of the eBird hotspot finding would be a second.

## City of Melbourne canopy story (2024 iNat records, 2021 canopy; from build_canopy.py)
- City area 37.54 km², tree cover 11.3%. iNat records inside the City 3,396; 443 dropped (location blurred > 100 m,
  e.g. hidden sensitive species); 2,953 mapped. **28.8% were made under a tree canopy outline** (27.5% for records
  with known accuracy, 31.7% unknown accuracy: robust). Within 10 m of a canopy: 80% of records vs 48% of the area.
- Parkville (Royal Park) 20.2% of trees / 34.4% of records; Melbourne (CBD + Royal Botanic Gardens) 21.5% / 34.9%;
  together 42% / 69%. East Melbourne (Fitzroy Gardens) 10.6% / 3.2%. North Melbourne 7.0% / 0.3%.
  Port Melbourne 5.0% / 10.6% (Westgate Park). Suburbs crossing the City boundary count only the part inside it.
- Not causal: parks have both trees and walking paths. GPS error (~10 m) blurs 'under a tree' towards the City average,
  so 29% is if anything an underestimate.

## Vega-Lite lessons from this project
- Polygons drawn "inside out" (a giant shape covering the map) = wrong winding order. Fix: shapely `orient(p, sign=-1.0)`
  (clockwise exteriors) before writing GeoJSON. The Python `topojson` library re-winds rings: use GeoJSON instead.
- In layered charts, define shared axes (e.g. `x`) ONCE in the top-level `encoding`, or formats like "," get ignored (5e+3).
- Use `",d"` or `",.0f"` formats on legends; `","` sometimes printed 1e+3.
- `align` is not an encoding channel: split text into separate layers with `mark.align`.
- Threshold color legends render as misleading gradients: use a calculated ordinal band field with an explicit domain.
- Raise `labelLimit` to stop label truncation. `"type":"topojson"` needs `"feature"`; GeoJSON needs `"property":"features"`.
- Edited a spec or data file but the chart looks unchanged = browser cache. Hard refresh (Cmd+Shift+R). preview.html
  passes `vega.loader({http: {cache: 'no-cache'}})` to vegaEmbed so it always fetches fresh files.
- Labels drawn outside a shape (TAS, ACT over the sea) must not use a fill-based white text colour rule.
- Grid cells as `rect` marks with `longitude`/`latitude`/`longitude2`/`latitude2` (cell corner + fixed degree offsets
  computed in a `calculate`): far smaller than GeoJSON squares.
- Text halo: a white text layer with a thick white stroke underneath, then the real text layer on top. A stroke on
  the same text mark draws over the letters.
- With `"width": "container"`, Vega sometimes reserves room for text outside the plot (bump-chart names, ridgeline
  names) and sometimes not (suburb map's Tarneit label, lollipop's 39,060). Extra padding where Vega already
  reserves room is counted twice and squeezes the plot. Always measure in the browser before adding padding.
- Heavily skewed counts (median 2, max 4,246) need a log scale. Log needs values >= 1 (every observer has >= 1
  record). Explain it in plain words on the axis ("each gridline is 10 times the one before"). Whole-number counts
  form vertical stripes at 1, 2, 3...: that is real, not a bug; label the x = 1 stripe with its count.

## Processing scripts (run from the project root)
- `processing_scripts/fetch_state_data.py --year 2024`: state bird counts (ALA API) + 30 June populations (ABS API)
  -> `data/state_bird_records_<year>.csv` (columns `state, bird_records, population, records_per_1000_residents`;
  note `population`, not `population_2025`: update map_states.vl.json). **2024 file already written (11 Oct 2026).**
- `processing_scripts/build_canopy.py --year 2024` (run after build_data.py, ~2 min): canopy + iNat -> 
  `com_canopy_grid_2021.csv` (0.0006 x 0.0005 degree cells, ~54 m, only cells with trees, 170 KB),
  `com_outline.geojson` (14 suburb parts clipped to the City, with label points), `com_inat_points_2024.csv`,
  `com_suburb_canopy_records_2024.csv`. Uses iNaturalist only (see eBird hotspot issue).
- `processing_scripts/build_data.py --year 2024`: raw ALA CSV + ABS GeoPackage -> every Melbourne file in `data/`:
  suburb CSV, suburb GeoJSON, points CSV, top 15, slope, iNat heatmap + observers, and two new files for
  the planned charts: `melb_source_month_<year>.csv` (stream graph) and `melb_species_month_rank_<year>.csv` (bump:
  monthly rank among all species of the year's top 10). The joined record table is cached in
  `../raw_data/work_<year>/` (also `species_common_names.csv`); `--skip-join` reuses it. Takes about a minute.
- **Validated 11 Oct 2026:** run on the 2025 download it reproduced the chat's 2025 files exactly (same rows; only row
  order of ties differs), except the slope chart's `change` column, which is now direction-based and correct:
  "Ranks higher by number of records" / "Ranks higher by number of birds counted". slope_records_vs_birds.vl.json's
  colour domain must be updated to these labels. Its y domain `[-0.5, 34]` must cover the largest `y_*` value.
- Expects the ALA CSV in `../raw_data/ala_<year>_birds_vic/` (or pass `--ala`), and the GeoPackage unzipped in
  `../raw_data/abs_g01_vic/` (done). It checks the needed columns exist and prints the key numbers for annotations.
- The older scripts (`assign_suburbs.py`, `melb_suburbs.py`, `prep_melb.py`, `prep_charts.py`, `prep_charts2.py`)
  are superseded: they used sandbox paths and a missing 2017 suburbs file. Keep for history or delete.

## Next steps (in order)
1. ~~Download 2024 ALA data~~ (done 11 Oct 2026).
2. ~~Regenerate all data for 2024 and update every spec~~ (done 11 Oct 2026). If the data is ever rebuilt, these
   values are hard-coded in specs: lollipop x domain + subtitle; jitter top-observer value (in a `calculate`), x
   domain, label text; suburb and proportional map callout positions/text, legend values; states map label colour
   threshold (>1000); heatmap and slope subtitles.
3. ~~Canopy data, canopy dot map, connected dot plot~~ (done 11 Oct 2026).
4. Build the bump chart and stream graph to pass 10 charts; keep the sketch consistent with the final set.
5. index.html (student's layout, 14 Oct 2026): centred title "Birds in our back yards", then 3 equal columns
   (`.columns`, page max-width 1440px): left = placeholder text, middle = states map, right = empty. The student is
   placing things themselves. map_states.vl.json uses `"width": "container"`, height 380 (a map keeps its shape, so
   a lower height stops it filling a wide column). Columns: 449px at a 1460px window, 389px at 1280px; no sideways
   scroll at either. Subtitle split over two lines and legend moved below the map so they fit.
   Row 2: the suburbs rate map in a `.span-2` box (columns 1-2), filling it: map_suburbs.vl.json uses
   `"width": "container"`, height 950 (Melbourne is taller than wide, so this height is needed to fill ~930px), and
   `padding.left` 60 because the right-aligned Tarneit label and the title otherwise stick out past the chart's left
   edge (container-width charts don't make room for text beyond the map). Chart ~1,010px tall. At 1280px the map
   is narrower (682px drawn) but the height is fixed, so ~100px gaps open above and below it; an adaptive height
   (CSS container query + `"height": "container"`) was offered, not done.
   Row 2, column 3: the lollipop (top half of the cell). lollipop_species.vl.json: `"width": "container"`, height
   368, `padding.right` 45 (room for the 39,060 value label), subtitle split over 4 lines (same words), legend moved
   below the chart (bottom-right overlapped the Grey Butcherbird label at 1280px). Chart 515px tall = 51% of the
   row at both 1280 and 1460px; nothing outside the column.
   Row 2, column 3, bottom half: the bump chart under the lollipop. bump_monthly_ranks.vl.json: `"width": "container"`,
   height 300, subtitle split over 6 lines (same words), default padding. Jan-Dec spans 250px at 1280 (every 2nd
   month label shown) and 310px at 1460 (all 12). ~70px spare below it. Lesson: here Vega already reserves room for
   the end-of-line bird names, so extra right padding (tried 120) only adds an empty strip; measure before padding.
   Row 3 (one chart per column): ridgeline | canopy dot map | trees-vs-records dot plot.
   - ridgeline_seasonal.vl.json: rebuilt 14 Oct 2026 as ONE layered chart (no facet), because a faceted chart can't
     use `"width": "container"`. Each bird gets a row number (`window` dense_rank by peak month, then name); its area
     runs from `y2` = row (baseline) up to `ridge_top` = row - profile/max_profile * 2.3, on a reversed y scale, so
     ridges overlap like before. Names are a text layer at January (right-aligned); invisible points give a
     tooltip per month (an area's tooltip only ever showed its first point, January). Fills its column: ridges
     299px wide at 1460, 239px at 1280. Subtitle split over 6 lines, legend below.
   - map_canopy_dots.vl.json: `"width": "container"`, height 430, subtitle split over 6 lines, legend below the map
     in 3 columns (top-right covered Carlton North/Parkville), South Wharf label on two lines (clashed with Southbank).
   - dotplot_canopy_records.vl.json: `"width": "container"`, subtitle split over 6 lines, x-axis title on 2 lines.
   All three: title 12px (was 13), subtitle 10px (was 12) via `title.fontSize` / `title.subtitleFontSize`.
   Checked at 1280 and 1460: nothing outside its column, no label clashes, no sideways scroll.
   Every vegaEmbed call uses `{ actions: false }` (no three-dot menu).
   Still to do: narrative text, typography (rubric HD wants a non-standard typeface matching the topic),
   author name, AI acknowledgement, replace state boundaries, stream graph in the closing section.
6. Rewrite all titles and subtitles in the student's own voice. Delete test pages and the Map1 duplicate. `git init`,
   publish via GitHub Pages (public repo, Settings > Pages > main / root). Test logged out / incognito.
7. Submission: GitHub URL, sketch PDF URL in the repo, What/Why/How description, AI acknowledgement.

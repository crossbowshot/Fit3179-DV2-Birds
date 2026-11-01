# The Birds We See

A one-page data visualisation of citizen-science bird records in Melbourne in 2024, made for FIT3179 Data
Visualisation (Monash University). Built with Vega-Lite and Vega.

## Chart specifications

Every chart's JSON specification is in [`js/`](js/), formatted for reading:

| Chart | Idiom | Specification |
|---|---|---|
| Bird records per 1,000 residents, by state | Choropleth map | [`js/map_states.vl.json`](js/map_states.vl.json) |
| Bird records per 1,000 residents, by Melbourne suburb | Choropleth map | [`js/map_suburbs.vl.json`](js/map_suburbs.vl.json) |
| Bird records in each suburb (spin and tilt) | Spike map (Vega) | [`js/map_spikes_tilted.vg.json`](js/map_spikes_tilted.vg.json) |
| Melbourne's 15 most reported birds | Lollipop chart | [`js/lollipop_species.vl.json`](js/lollipop_species.vl.json) |
| Monthly ranks of the top 10 birds | Bump chart | [`js/bump_monthly_ranks.vl.json`](js/bump_monthly_ranks.vl.json) |
| Birds that come and go with the seasons | Ridgeline plot | [`js/ridgeline_seasonal.vl.json`](js/ridgeline_seasonal.vl.json) |
| Tree cover and bird records in the City of Melbourne | Dot map over a tree-cover grid | [`js/map_canopy_dots.vl.json`](js/map_canopy_dots.vl.json) |
| Share of trees vs share of records, by suburb | Connected dot plot | [`js/dotplot_canopy_records.vl.json`](js/dotplot_canopy_records.vl.json) |
| Bird records per iNaturalist user | Jitter plot | [`js/jitter_observers.vl.json`](js/jitter_observers.vl.json) |
| Bird records by weekday and hour | Heatmap | [`js/heatmap_weekday_hour.vl.json`](js/heatmap_weekday_hour.vl.json) |
| How many bird records each suburb had | Bar chart | [`js/bar_suburb_coverage.vl.json`](js/bar_suburb_coverage.vl.json) |

The spike map uses a custom "tilted" map projection, which is registered with Vega in `index.html`.

## Data

The small, aggregated data files the charts load are in [`data/`](data/). The Python scripts that made them from the
raw downloads (not included, as they are several GB) are in [`processing_scripts/`](processing_scripts/). Sources,
licences and notes on the data are listed at the bottom of the page.

---
title: "Domain Grounding — Remote Sensing + Multi-Domain Feasibility"
date: 2026-06-02
author: nigredo
campaign: nse-phase-0-intelligence-brief
phase: domain-grounding
type: feasibility-assessment
---

# Domain Grounding: Remote Sensing + Multi-Domain Feasibility

**Purpose:** Ground-truth every claim about data access, tooling maturity, and scientific feasibility for the expedition's first season (North African paleontology via Sentinel-2) and validate domain selection criteria against candidate future domains.

**Bottom line:** The expedition is feasible. Sentinel-2 geological mapping in Moroccan arid terrain is established methodology (76-93% accuracy in published literature). The Kem Kem Group specifically is an unmapped application gap — proven techniques, novel target. Data access from Hetzner is confirmed. Python tooling is mature. The expedition would be applying known methodology to a scientifically important but uncharacterized site, which is exactly the right risk profile for a first season.

---

## 1. Can DSV4-Flash Agents Meaningfully Analyze Satellite Data?

**YES — with a critical reframe.** Agents don't look at images. They orchestrate Python tools that produce numerical outputs.

The analysis pipeline is entirely numeric:
1. Search STAC catalog → get tile IDs and metadata
2. Read spectral bands via rasterio (HTTP range requests on COGs)
3. Compute spectral indices (numpy arithmetic)
4. Extract feature vectors per pixel/polygon
5. Classify with scikit-learn (Random Forest)
6. Output: classification maps as GeoTIFF + accuracy metrics as numbers

Every step is code generation + execution + reading numeric results. No vision required. A text-only LLM orchestrating Python tools is the correct architecture for this.

**Renner's confirmation (Finding 042):** DSV4-Flash handles validation of spectral analysis output with 100% error detection across 3 reps. The model cross-references spectral indices at index-level precision and correctly identifies inconsistencies between NDVI values and classification labels.

---

## 2. Python Tooling Landscape

**Mature and stable.** The remote sensing Python ecosystem is well-developed.

### Minimal Stack (what expedition agents need)

| Package | Role | Maturity |
|---------|------|----------|
| **pystac-client** | STAC catalog search (discover tiles by area/date/cloud) | Stable, actively maintained |
| **rasterio** | Raster I/O (read COGs via HTTP range requests) | Foundational, 10+ years |
| **numpy** | Spectral index calculation, array operations | Ubiquitous |
| **geopandas** | Vector data (AOI definition, spatial joins) | Stable |
| **scikit-learn** | Classification (Random Forest, SVM) | Standard ML toolkit |

### Optional Enhancements

| Package | Role | When Needed |
|---------|------|-------------|
| **stackstac** | STAC items → xarray DataArrays (lazy, Dask-backed) | Multi-tile composites/mosaics |
| **eodag** | Multi-provider unified search API | If switching between data sources |
| **s2cloudless** | ML-based cloud probability masking | If SCL band masking is too conservative |
| **sentinelhub-py** | CDSE Sentinel Hub SDK (on-the-fly processing) | If CDSE becomes primary data source |

**Assessment:** All packages are pip-installable, well-documented, and have active communities. No novel tooling needed. The expedition's initial tool suite (Aura's recommendation from council) should ship these as Phase 1 infrastructure.

---

## 3. Data Access — Verified From Expedition Compute

### Access Verification (tested from Hetzner GEX44, June 2, 2026)

| Source | Endpoint | HTTP Status | IP Blocking |
|--------|----------|------------|-------------|
| AWS Earth Search | earth-search.aws.element84.com/v1 | **200 ✓** | None |
| Copernicus CDSE | stac.dataspace.copernicus.eu/v1 | **200 ✓** | None |
| MS Planetary Computer | planetarycomputer.microsoft.com/api/stac/v1 | **200 ✓** | None |

**Momon's IP blocking concern (council Turn 23) is resolved.** All three STAC endpoints are accessible from Hetzner. The FEMA/PHMSA CDN blocking pattern does not apply — those are US government Cloudflare deployments. EU-operated (CDSE) and AWS public data services do not exhibit this behavior.

### Concrete Data Availability

Test query over Kem Kem region (bbox: -3.5°W to -2.5°W, 31.5°N to 32.5°N):
- **46 Sentinel-2 L2A tiles in January 2025 alone**
- Near-zero cloud cover (0.03% - 0.8% for Saharan tiles)
- 5-day revisit time (Sentinel-2A + 2B combined)

The Saharan climate is ideal for remote sensing — minimal cloud interference, consistent atmospheric conditions. Data abundance is not a concern.

### Recommended Data Source

**AWS Earth Search (Element 84)** is the primary recommendation:
- Free STAC API, no authentication needed for search
- Data in **Cloud Optimized GeoTIFF (COG)** format — critical advantage
- HTTP range reads via rasterio work out of the box
- Requester-pays S3 buckets (minimal egress cost for moderate use)
- Collection: `sentinel-2-l2a` (L2A = already atmospherically corrected)

**CDSE as backup:**
- Free (12 TB/month download), OAuth2 authentication required
- Data in **JPEG2000** format (not COG — adds friction)
- S3-compatible access available
- EU-operated, long-term institutional stability

**Google Earth Engine as alternative paradigm:**
- Free for noncommercial/research
- Server-side processing (computation runs on Google servers)
- Different code model (GEE-specific, not standard rasterio/numpy)
- Useful if compute-heavy analysis needed without local resources

### Preprocessing Requirements

Sentinel-2 Level-2A data is already atmospherically corrected (Bottom-of-Atmosphere reflectance via Sen2Cor). Remaining preprocessing:

1. **Cloud masking** — Use the Scene Classification Layer (SCL band). Mask pixels classified as cloud (8,9,10), cloud shadow (3), snow (11), unclassified (0,1,2). Alternative: s2cloudless for ML-based cloud probability.
2. **Band selection** — B02-B04 (visible, 10m), B08 (NIR, 10m), B05-B07 (Red Edge, 20m), B11-B12 (SWIR, 20m). Resample 20m bands to 10m if needed.
3. **Spectral index computation** — Pure numpy arithmetic (see Section 5).

No atmospheric correction, no radiometric calibration, no orthorectification needed. The data is analysis-ready.

---

## 4. Kem Kem Literature & Methodology Assessment

### Is Sentinel-2 Geological Mapping Established?

**YES — extensively, especially in Morocco.** Published studies in adjacent regions:

| Study Area | Method | Accuracy | Relevance |
|-----------|--------|----------|-----------|
| Tafilalet Basin (Eastern Anti-Atlas) | SAM + Maximum Likelihood | 76% (κ=0.74) | Directly south of Kem Kem escarpment |
| Skhour Rehamna | Object-based SVM | 93% (κ=0.89) | Moroccan arid terrain |
| Tagragra d'Akka (Western Anti-Atlas) | SVM + Sentinel-2A | 86% | Anti-Atlas lithology |
| Bou Azzer-El Graara (Central Anti-Atlas) | Band ratios + PCA | 1:50,000 map | Litho-structural + alteration |

The methodology — band ratios, PCA, supervised classification — is mature and repeatedly validated in Moroccan arid terrain. This is routine remote sensing geoscience.

### Is Kem Kem Specifically Mapped?

**NO — this is the gap.** No published remote sensing study specifically targets the Kem Kem Group. The canonical reference is Ibrahim & Sereno (2020), a 216-page open-access monograph in ZooKeys that formally names the Gara Sbaa (lower) and Douira (upper) formations. It contains geological maps, measured sections, and locality coordinates — but all derived from traditional field geology, not remote sensing.

**This is an application gap, not a methodology gap.** The Kem Kem escarpment (~200-250 km of exposed Cretaceous strata along the Morocco-Algeria border) is an excellent candidate for Sentinel-2 mapping:
- Arid terrain, minimal vegetation
- Strong lithological contrasts (sandstones vs. mudstones vs. Cenomanian-Turonian limestone cap)
- Proven methodology from adjacent regions transfers directly

**Risk assessment:** LOW. Applying established techniques to an uncharacterized but well-suited target site. The methodology risk is near zero; the scientific novelty is in the application.

### Standard Classifiers

**Random Forest is dominant** in geological remote sensing literature:
- RF on Sentinel-2 alone: 76-91% accuracy
- RF on Sentinel-2 + DEM (SRTM): ~84% (κ=0.83)
- SVM competitive (86-93%) but more parameter-sensitive
- Deep learning / CNNs are explicitly NOT standard — insufficient spatial resolution (10-20m), limited training data

**Aura's council recommendation confirmed:** scikit-learn classifiers, minutes on CPU. Not neural networks.

---

## 5. Spectral Indices for Geological Mapping

Standard Sentinel-2 band ratios for the expedition's target lithologies:

| Target | Band Ratio | Sentinel-2 Bands | Kem Kem Relevance |
|--------|-----------|-------------------|-------------------|
| Iron oxides (Fe³⁺) | B4/B3 | Red/Green | Ferruginous sandstones of Gara Sbaa Fm. |
| Ferrous iron (Fe²⁺) | B11/B8A | SWIR1/NIR narrow | Mafic mineral detection |
| Clay minerals (OH-bearing) | B11/B12, B11/B5 | SWIR1/SWIR2 | Mudstone horizons |
| Carbonates | B11/B2, B11/B12 | SWIR1/Blue | Cenomanian-Turonian limestone cap |
| Vegetation (NDVI) | (B08-B04)/(B08+B04) | NIR/Red | Wadi vegetation (trace) |

Additionally: PCA on SWIR bands (B11, B12) separates clay vs. carbonate assemblages. False-color composites (B12/B11/B4 as RGB) give strong geological discrimination.

**For Kem Kem specifically:** The iron oxide and carbonate ratios are most diagnostic — separating the ferruginous sandstones of the Gara Sbaa Formation from the overlying limestone cap is the primary classification challenge and also the most scientifically interesting boundary.

These are the "derived products" that text-only agents work with — numerical arrays of index values per pixel, not images.

---

## 6. Labeled Data Availability

### What Exists

| Source | Content | Format | Accessibility |
|--------|---------|--------|--------------|
| **Ibrahim & Sereno (2020)** | Detailed geological maps, 6 field localities with GPS, measured stratigraphic sections | Journal figures (not georeferenced GIS) | Open access (ZooKeys) |
| **PBDB** | Kem Kem occurrence records (fossil localities) | Point coordinates | Free API (paleobiodb.org) |
| **USGS Spectral Library v7** | Reference spectra for minerals (hematite, goethite, kaolinite, calcite, etc.), 0.2-200 μm | Downloadable, resampleable to S2 bands | Free |
| **Morocco national geological surveys (ONHYM/BRGM)** | 1:100,000 and 1:200,000 geological maps | Not freely available in digital georeferenced form | Behind institutional access |

### What's Missing

**A georeferenced training dataset linking pixel locations to verified lithology for the Kem Kem escarpment.** This is the critical gap. Creating this from:
- Ibrahim & Sereno (2020) maps + Google Earth cross-referencing
- PBDB point localities for anchor points
- USGS spectral endmembers for spectral matching

...would be a necessary first step and itself a Phase 1 deliverable. **Aura's council warning (Turn 9) is correct:** the labeling strategy determines 40% vs 80% classifier accuracy. The expedition's first scientific contribution could be creating this georeferenced training dataset.

---

## 7. Multi-Domain Feasibility

The expedition's domain selection criteria: vast public data, low-stakes errors, visually spectacular, seasonally structured.

### Candidate Domain Assessment

#### A. Deep Sea Bathymetry / Oceanography

| Criterion | Rating | Assessment |
|-----------|--------|------------|
| Vast public data | **A+** | NOAA GEBCO (global bathymetry, 15 arc-second), NCEI archive, Argo floats, CMEMS ocean models, satellite altimetry. Enormous volume, well-organized APIs. |
| Low-stakes errors | **A** | Misidentifying a seamount doesn't harm anyone. Scientific value even from approximate bathymetric classification. |
| Visually spectacular | **A** | 3D seafloor topology, thermal vents, mid-ocean ridges. Bathymetric maps are naturally beautiful. |
| Seasonally structured | **B+** | Ocean dynamics are seasonal (currents, temperature). Bathymetry itself is static but can be combined with seasonal oceanographic data for temporal component. |
| **Overall** | **A** | Strong second-season candidate. Rich data ecosystem, genuine scientific questions (uncharted seafloor), compelling visuals. |

#### B. Astronomical Transient Detection

| Criterion | Rating | Assessment |
|-----------|--------|------------|
| Vast public data | **A+** | TESS (full-frame images every 200s), ZTF (alerts API, ~1M transient candidates/night), Kepler/K2 archive, MAST archive. All free, programmatic APIs. |
| Low-stakes errors | **A+** | Misclassifying a variable star has zero consequences. Even false positives contribute to training data improvement. |
| Visually spectacular | **B+** | Light curves are scientifically fascinating but visually abstract — a dip in a line graph. The *concept* (finding new worlds) is spectacular; the actual visual artifacts need narrative framing to engage non-expert audiences. |
| Seasonally structured | **A-** | TESS observes in 27-day sectors with regular data releases. More "continuous drip" than "seasonal event" but has natural rhythm. |
| **Overall** | **A** | Strong candidate. Best data infrastructure of all domains. Planet Hunters TESS (22K+ citizen scientists) found 150 planet candidates including the first TESS circumbinary planet found on citizen science forums — proving the model works. Visual handicap vs. satellite imagery needs narrative packaging. |

#### C. Hydrothermal Vent Chemistry / Origin of Life

| Criterion | Rating | Assessment |
|-----------|--------|------------|
| Vast public data | **C** | EarthChem (geochemistry databases), IEDA (marine geoscience), some published vent fluid chemistry. Much smaller and more specialized than other candidates. Requires specialized domain knowledge to interpret. |
| Low-stakes errors | **A** | No harm from misinterpreting vent chemistry. |
| Visually spectacular | **B** | Underwater vent imagery is dramatic but less data-rich than bathymetry or astronomy. Chemical composition tables are less visually compelling. |
| Seasonally structured | **D** | No natural seasonal cadence. Vent chemistry doesn't change on human-observable timescales without dedicated expeditions. |
| **Overall** | **C+** | Weakest candidate. Insufficient public data volume and no natural cadence. Better as a sub-theme within a bathymetry season than a standalone domain. |

### Additional Candidate: Wildfire Ecology (Satellite-Native)

| Criterion | Rating | Assessment |
|-----------|--------|------------|
| Vast public data | **A+** | FIRMS (NASA fire detections), Sentinel-2 burn scar mapping, MODIS/VIIRS active fire, Landsat archive. Same tooling stack as Season 1. |
| Low-stakes errors | **A** | Historical burn scar mapping, not real-time response. |
| Visually spectacular | **A+** | Before/after satellite imagery of burn scars is inherently dramatic. Recovery monitoring over seasons. |
| Seasonally structured | **A+** | Fire seasons are naturally annual. Recovery monitoring creates multi-year arcs. |
| **Overall** | **A+** | Co-strongest candidate alongside astronomy. Uses the same Sentinel-2 tooling from Season 1 (zero infrastructure rebuild), naturally seasonal, visually dramatic, and scientifically relevant. |

### Domain Selection Criteria Validation

The criteria are sound. They successfully discriminate between candidates:
- Wildfire ecology scores highest (A+ — same Sentinel-2 tooling, zero infrastructure rebuild)
- Bathymetry is strong (A — richest data, best visuals, coral bleaching provides seasonal cadence)
- Astronomy is strong (A — best data infrastructure, proven citizen science model, visual handicap)
- Hydrothermal is weak (C+ — fails on data volume and seasonality)

**Additional candidate: Glacier retreat monitoring** (Sentinel-2 + Landsat) — decades of imagery, seasonal melt cycles, visually dramatic, scientifically significant. NASA's Prithvi foundation model could serve as baseline. Would rate A overall.

**Recommendation for domain-agnostic design:** The infrastructure should be parameterized by: (1) data source (STAC endpoint + collection), (2) spectral/feature extraction pipeline (domain-specific), (3) classifier training data (domain-specific), (4) visualization layer (domain-specific presentation). The orchestrator, state management, validation pipeline, and library schema should be domain-agnostic. Season 1's Sentinel-2 tooling transfers directly to wildfire ecology (same satellite, same tools).

---

## 8. "AI Doing Science in Public" Landscape

### Zooniverse Project Design

Zooniverse is the leading citizen science platform (125+ projects, Galaxy Zoo classified 900K galaxies). Key design patterns for non-expert participation:

1. **Simple classification tasks** — Binary or small-N categorical choices ("Is this a spiral galaxy?"), not open-ended description
2. **Constrained interaction tools** — Draw circles, place pointers, select categories. No freeform annotation.
3. **Tutorial-first onboarding** — Practice on known examples before real data
4. **Redundancy for quality** — Each item classified ~38x by different volunteers. Consensus, not individual judgment.
5. **Content-driven workflow** — Task design matches what data actually shows, not what you want it to show

**Transfer to expedition:** Audience interaction should be classification-style ("Is this spectral anomaly interesting? yes/no/unsure"), with constrained map interaction (click to flag regions), and redundancy-based quality (multiple votes before agent investigation). Kazuma's Heist 035 has detailed adaptation table.

### Existing ML Geological Mapping Projects

The space is more active than assumed, but none are public-facing:

- **NASA/IBM Prithvi** (open source, HuggingFace: `ibm-nasa-geospatial`): Geospatial foundation model trained on Harmonized Landsat/Sentinel-2. Deployed in orbit 2026. Supports flood mapping, disaster monitoring, crop classification, land use change. Open source and fine-tunable. Infrastructure the expedition could potentially build on.
- **Commercial mineral exploration AI**: ML analyzing satellite spectral data for gold, lithium, rare earth deposits. Adelaide University/ESA demonstrated Prithvi running on orbital platforms. Growing sector but entirely behind commercial walls.
- **Academic geological mapping**: Active research but traditional paper-publication workflows, not public-facing developmental systems.

**The gap:** No project combines AI-assisted geological analysis with community engagement. Academic projects publish papers. Commercial projects are proprietary. The expedition occupies genuinely uncharted territory.

### Closest Autoresearch Analogues

- **ClawdLab / Beach.Science** (arxiv 2602.19810, March 2026): Open-source platform where AI agents investigate research questions through specialized roles (PI, Scout, Analyst, Critic, Synthesizer). Six academic publications within 14 days of launch. GitHub: bio-xyz/ClawdLab. Closest existing project to what we're planning — but no public audience, no streaming, no community governance.
- **Sakana AI's AI Scientist** (Nature publication, March 2026): First fully AI-generated paper to pass peer review at an ICLR workshop. 8.9K+ GitHub stars. A tool, not a public spectacle.
- **Google DeepMind's Co-Scientist** (May 2026): Multi-agent hypothesis generation. Internal research tool.

**No one is doing "AI research as live entertainment."** The Discord/Twitch AI communities are discussion forums, not live research streams. The closest thing to "watch AI think" is Emergence World's post-hoc narrative, not real-time observation.

### AI Entertainment Format Landscape

Per Kazuma's Heist 034 (comprehensive scouting of AI Town, Pokémon streams, companion apps, Streamlabs, AI reality TV):

**Every format without developmental trajectory died.** AI Town shut down. Social simulations exhausted their novelty (Emergence World's Grok world collapsed in 4 days with 183 crimes — viral for the wrong reasons). Pokémon streams survive on competition framing but the model doesn't improve between sessions.

The expedition's combination — developmental trajectory + genuine scientific output + community governance + persistent agent identities + throttled streaming — is untested but theoretically sound. No existing format does this. The closest precedent is Pokémon Twitch streams (visible reasoning at readable speed), but those lack accumulation and governance.

### Zooniverse Human-AI Hybrid Classification

**Key additional finding:** Zooniverse's Gravity Spy project demonstrated the model: AI pre-classifies, humans handle edge cases, accuracy jumped from 54% to 90% while improving volunteer retention. The expedition could **invert** this: AI agents as primary classifiers with human review on low-confidence cases. The Zooniverse model validates that human-AI collaboration on classification tasks works and improves both accuracy and engagement.

---

## 9. Answers to Council Questions

| Question | Source | Answer |
|----------|--------|--------|
| Can DSV4-Flash analyze satellite data? | Nigredo T5 | **YES** — agents orchestrate Python tools, all numeric. No vision needed. |
| What labeled training data exists? | Aura T9 | **Partial** — USGS spectral library, PBDB points, Ibrahim & Sereno maps (not georeferenced). Creating georeferenced training data is a Phase 1 deliverable. |
| Copernicus API constraints / IP blocking? | Cocytus T10, Momon T23 | **No blocking.** All 3 STAC endpoints (CDSE, AWS, MS) return 200 from Hetzner. 12TB/month free on CDSE. AWS COGs are the recommended path. |
| "AI doing science in public" projects? | Pandora T11 | **Landscape is empty** for this specific combination. Zooniverse does citizen science but not AI-driven. Academic remote sensing doesn't engage public audiences. |
| Multi-domain feasibility? | Demiurge T20 | **Validated.** Wildfire ecology (A+ — same tooling), bathymetry (A — richest data/visuals), astronomy (A — proven citizen science). Hydrothermal (C+) is weak. |

---

## 10. Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Labeled data insufficient for classification | HIGH | MEDIUM | Build georeferenced training data as Phase 1 deliverable from Ibrahim & Sereno + PBDB + spectral library |
| AWS requester-pays S3 costs accumulate | LOW | LOW | Moderate tile downloads, cache locally. Costs minimal for research-scale use. |
| Kem Kem escarpment has less spectral contrast than expected | MEDIUM | LOW | Adjacent Moroccan regions show strong contrast in published literature. Saharan exposure is favorable. Pilot classification on 2-3 test tiles before full survey. |
| Replit compute insufficient for rasterio/sklearn | MEDIUM | MEDIUM | Consider Hetzner as alternative compute platform. The expedition's compute doesn't have to run on Replit — Cocytus's persistence question (council Turn 10) is relevant. |
| Domain-specific tooling becomes maintenance burden across seasons | LOW | MEDIUM | Domain-agnostic infrastructure design. Season-specific tools are modular add-ons. Wildfire season reuses S2 tooling directly. |

---

## 11. Design Implications for Phase 1

1. **Tool suite should ship as Phase 1 infrastructure** (Aura Turn 9) — not Phase 2 science. The spectral index computation tools are the foundation everything else builds on.

2. **AWS Earth Search is the data source.** COG format eliminates preprocessing friction. pystac-client + rasterio is the minimal viable data access stack.

3. **Creating georeferenced training data is the first scientific contribution.** The expedition's Phase 1 outputs a georeferenced lithological training dataset for the Kem Kem escarpment — this doesn't exist anywhere and is itself a valuable contribution.

4. **Pilot classification on 2-3 test tiles before full survey.** Validate that spectral indices discriminate Kem Kem lithologies before committing to the full ~200 km escarpment survey.

5. **Domain-agnostic infrastructure from day one.** The territory tracker, validation pipeline, and library schema should be parameterized by domain. Season 1 uses Sentinel-2 geological indices; Season 2 (wildfire or astronomy) plugs in different data sources and feature extraction while keeping the same orchestrator and knowledge accumulation system.

---

*Phase 0 deliverable for campaign nse-phase-0-intelligence-brief. Research conducted June 2, 2026. Data access verified from Hetzner GEX44.*

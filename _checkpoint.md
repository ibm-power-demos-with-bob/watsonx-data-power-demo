# 🔖 Checkpoint — watsonx.data on IBM Power Demo
## Session 24 — Lisa Funnell scholarship added (deployed, `ibmi` mode)

- Source: https://lisafunnell.com/articles/ (abstracts only on that page). Read in full: Flow article "Nomi/No Me?" (flowjournal.org) and the Participations survey paper (working PDF: `https://www.participations.org/17-02-04-funnell.pdf`; the link on her page 404s; fetch tool can't read PDFs, so download and extract with `pypdf`). Tandfonline is 403 to bots, so Craig-era / phases items are abstract-level only.
- Corpus 141 -> **148**: `setup/_add_funnell_flow_passages.py` appends 7 verbatim Flow quotes (`source_type` "Scholarly commentary", licence "Copyright L. Funnell (short quote)", `doc_id` `FLOW_2019_n`). Re-run order: that script, `_embed_bond_corpus.py`, `9-load-bond-data-pg.py`. 3 of the 7 reach the Act 5 top 8 (Grace Jones 0.446, Naomie Harris x2). None of the Lashana Lynch quotes rank.
- `bond-query.ts`: Act 5 gets a "Source" column and 148 counts; Acts 1 and 3 get a "Ratings Are Crowd Data" caveat (Flow: review-bombing); Act 4 gets "What Scholarship Says (Funnell)" incl. the survey figures (n=511, 50.5% improved, 61% strong and empowered, top qualities). Labelled as opinion, not film data. About panel updated.
- Craig-era item (Funnell 2018, J. Popular Film & TV) now uses the journal abstract the user pasted from tandfonline (cookie-accept needed in a browser; bots get 403): qualities spread over >=2 characters per film, "outlier women" Vesper Lynd / Camille Montes / M, Spectre reinstates the archetype via Madeleine Swann. Our depth scores: Vesper 9, Camille 8; M not in the cast list. The three-phase item (Funnell 2008) is still abstract-from-her-page only.
- Not done: depth-score-by-phase view (Funnell's three phases); deliberately skipped as the demo is "fun", not deep.
- **Next (optional):** (1) resolve the 12 no-excerpt rows, (2) add Rachel Grant / Cucinotta / Deckers, (3) check the slides for old wording, (4) a few quotes from the Participations paper into the Act 5 corpus if wanted.
- Gotcha: two parallel `search_and_replace` calls on the same file can clobber each other (happened twice). Edit one at a time and grep to confirm.



## Session 23 — CORPUS NOW REAL (Wikipedia), FICTIONAL CORPUS REMOVED. Redeployed (`ibmi` mode), all 6 acts return data.

- **Provenance finding:** the Bond task export (`bob-task-56959ee…-2026-10-29.md`) shows the old 20-excerpt corpus was **hand-written by Bob** in `scripts/generate_semantic_corpus.py` (Variety, Rolling Stone, actress "quotes" etc. were invented). No source was ever fetched. It is gone from the repo data; a backup of the old files is in `%TEMP%` only (`*.FICTIONAL.json`). Do not reuse.
- **New corpus:** `setup/_fetch_bond_wikipedia_corpus.py` pulls each actress's English Wikipedia article via the MediaWiki API and keeps up to 2 verbatim passages that mention the Bond film / character / "Bond". Result: **141 excerpts, 74 actresses, 76 of 88 rows**. Each has `source_url` (permalink with `oldid`), `page_title`, `revision_id`, `licence` (CC BY-SA 4.0), `retrieved_at`. The script backs off on HTTP 429 (run takes ~8-9 min; run it with a long timeout).
- **No excerpt (12 rows):** Alexandra Bastedo, Elaine Taylor, Geraldine Chaplin, Mireille Darc, Tracey Crisp, Jeanne Roland, Tsai Chin, Jane Seymour (LALD), Cherry Gillespie, Daisy Beaumont, Nina Muschallik, Tonia Sotiropoulou (no page or no passage mentioning the film). Possible fix: `TITLE_OVERRIDES` in the script, or read the film page's cast notes.
- **Honest limits:** these are encyclopedia **biographies**, not reviews or interviews. Many say little about agency, so Act 5 cosine scores are modest (top 0.475). The UI says this ("Reading The Scores"). The Lynn-Holly quote on the slide is still not in the corpus.
- **Pipeline changes:** `9-load-bond-data-pg.py` — `bond_semantic_reviews` gains `source_url`, `licence`, `retrieved_at`; inserts now go via psql stdin (text has double quotes). `bond-query.ts` Act 5 returns `source_url`, Source (permalink) column (new `link` format in `bond-investigation.tsx`), "illustrative" wording replaced with Wikipedia wording. `_embed_bond_corpus.py` re-run (141 docs, 384-dim). Postgres: 88 / 7 / 141 rows.
- **Roster cross-check (MI6-HQ):** 52 of MI6-HQ's 57 names already in our 88 (+2 spelling variants). Missing: Rachel Grant (Peaceful, DAD), Maria Grazia Cucinotta (Cigar Girl, TWINE), Daphne Deckers (TND), Emily Bolton, Sue Vanner. Our extra ~35 are Fandom/non-Eon names. IMDb list is blocked to bots. Not yet added.
- **Next:** (1) optionally add Rachel Grant / Cucinotta / Deckers (needs IMDb nconst resolution via cached dumps), (2) resolve the 12 no-excerpt rows, (3) Lynn-Holly quote is in the user's deck, not the demo: dropped, (4) slides are the user's to rework.
- **UI honesty pass (done, deployed):** removed all "on IBM Power" claims about the Presto engine. The Presto host (`watsonxdata.gym.lan`, checked over SSH) is **x86_64 / VMware**; the page says watsonx.data is *supported* on Power. PostgreSQL (RHEL ppc64le) and Db2 for i are on Power. Added an "About this demo's data" panel on `/bond-investigation` (IMDb-derived / Fandom+MI6-HQ cast / hand-curated character attributes / Wikipedia text / where it runs). Renamed "Vote Inflation" to "Decade Vote Volume", "Weighted Score" to "Vote-Weighted Score (derived)", agency columns marked "(editorial)". Act 4 story: IMDb cannot say whether a character survived or what she did, so that data comes from another source and is federated in. Honest caveat kept in the UI: in this demo those attributes are hand-curated and loaded in the same table as the IMDb-derived columns, not from a separate live system.


## Current Status
**Session 21 — BOND DATASET WIDENED 43 → 88, TRAJECTORY NOW ACTING-ONLY, ACT SUMMARY TEXT COMPUTED FROM LIVE DATA (see Session 21 notes below). UI redeployed in `ibmi` mode.**

**Session 21 — Bond dataset widening + de-hardcoding.**

- **Trigger:** Lynn-Holly Johnson (Bibi Dahl, *For Your Eyes Only*) was missing; her quote is on the "Curse of the Bond Girls" slide. She was never in the original 43 (curated list), not filtered out. Added (`nm0000468`).
- **Dataset 43 → 88 rows** from the Fandom "Bond Girl Actresses" category (124 names; MediaWiki API works, page fetch 403s). Film-cast only; games/radio/singers/voice dubbers excluded. Non-canon films kept (1967 *Casino Royale*, *Never Say Never Again*, 1954 TV) under a new `bond_era` = `Non-Eon`. Identity safety: nconst accepted only if in the Bond film's IMDb principals, or unique actress match with a credit within ±5y of the Bond year. 12 unresolved names left out (Aliza Gur, Catherine Von Schell, Diane Hartford, Emily Bolton, Lola Larson, Mai Ling, Michaela Clavell, Priscilla Barnes, Serena Gordon, Stephanie Sigman, Sue Vanner, Tracy Reed).
- **Role fields are editorial judgment** (role_category, depth score, flags, description) for all 45 added rows; no `data_confidence` column exists yet. The IMDb list of 54 could not be fetched (IMDb blocks bots); never compared with the Fandom 124.
- **Trajectory fix:** `career_trajectory` and `post_bond_active_years` now use ACTING credits only (IMDb category actress/actor), because self/archive appearances made e.g. Tania Mallet "Thriving". Credit counts and rating averages unchanged. New label "No Further Acting Credits" (was "No Further Screen Credits"). 46 rows changed.
- **De-hardcoded `bond-query.ts`:** Act 1-6 summaryStats now computed from query results (avg delta over non-null only; Act 4 names/finding; Act 5 matches; Act 6 no fake 0.85 — shows "—"). Act 3 null score shows "— (no rated credits)".
- **Row counts are expected, not bugs:** Act 1 = 78 (10 have no pre-Bond rating); Act 3/6 = 87 (Linda Christian 1954 has no 1950s benchmark — decided to leave out); source = 88 in both PG and Db2 for i.
- **Live findings (honest numbers):** Act 1: 28/76 (37%) lower after Bond, avg +0.18. Act 4: high-agency career 27.0 yrs vs low 29.9; prior career 10.6 vs 7.8; ratings 6.66 vs 6.58 (does NOT show longer careers for high agency). Act 6: only 17/87 have review text.
- **Open items:** (1) Act 5 "Vector Match" is `0.94 - idx*0.02` in `9-load-bond-data-pg.py:172` = file order, not a real vector score — fix with real embeddings or relabel. (2) Act 6 "The Final Answer" line oversells the "curse was a myth". (3) Lynn-Holly's quote is not in `bond_semantic_corpus.json` (needs confirmed source/wording). (4) Optional `data_confidence` column and a UI view of the 124 vs 54 vs 88 coverage gap.
- **Scripts (re-runnable; need cached IMDb dumps in `%TEMP%/imdb`, else re-run `_imdb_fix_fetch.py`):** `setup/_add_bond_actress_lynn_holly.py`, `setup/_bond_cast_scan.py`, `setup/_add_bond_actresses_fandom.py`, `setup/_recompute_bond_trajectory_acting.py`. After any JSON change: `python setup/9-load-bond-data-pg.py` then `python setup/9b-load-bond-data-ibmi.py`; UI text changes need `$env:BOND_PRIMARY_SOURCE='ibmi'; python setup/_deploy_ui.py`. API takes `?act=N` (query string, not POST body).
- **Slide framing agreed:** Acts 1, 2, 4 = single-table (what you can do today); Acts 3, 5, 6 = what modernisation adds (cross-source join, text, all fused).

**NEXT SESSION, STEP 1 — corpus provenance.** The user believes `bond_semantic_corpus.json` may have come from links checked earlier in the week and will look for them in earlier tasks. Repo history shows the file was added in one commit (`1ad307d`, 2026-10-27) with no source links, and nothing in the repo records where the text came from. If the user supplies the links: (1) check each of the 20 excerpts against its source; (2) where one matches, put the real quote and URL in, add a `source_url` column (`bond_semantic_reviews`, `9-load-bond-data-pg.py`); (3) re-run `setup/_embed_bond_corpus.py`, then `setup/9-load-bond-data-pg.py`; (4) update the on-screen "illustrative" wording in `bond-query.ts` only for excerpts that are verified; (5) redeploy (`$env:BOND_PRIMARY_SOURCE='ibmi'; python setup/_deploy_ui.py`) and run `python setup/_verify_bond_wording.py`. If no links turn up, keep the "illustrative sample" labelling. The user said not to worry about the slides.

**DONE (Session 22b) — Act 5/6 now use REAL static embeddings (supersedes the "keyword LIKE" description below).**
- `setup/_embed_bond_corpus.py` (run on the laptop, needs `pip install sentence-transformers`) embeds the 20 excerpts + one fixed question (Q1) with Hugging Face `sentence-transformers/all-MiniLM-L6-v2` (384-dim, normalised) → `demo-ui/src/data/bond/bond_semantic_embeddings.json`. Nothing runs on Power.
- `9-load-bond-data-pg.py` now loads `bond_semantic_reviews` (text + `embedding_model` + `embedding` as JSON text, replacing the fake `vector_similarity_score`) and a new `bond_semantic_queries` table (Q1). One INSERT per row (the embeddings are ~4 KB each).
- Act 5 SQL: `json_parse(...)` → `ARRAY(DOUBLE)`, `zip_with` + `reduce` = dot product = cosine, brute force over 20 rows, top 8. Presto output matches the laptop ranking exactly (`setup/_test_bond_cosine.py`). Act 6 left-joins each actress's best cosine to Q1 ("Agency Similarity (Q1)").
- Honest limits (stated on screen): only Q1 is embedded (no live query embedding), no vector index/DB, no RAG, corpus is 20 illustrative excerpts (publication names are labels). "We could add": live embedding (watsonx.ai), a vector store, RAG over real licensed text.
- Caveat on the results: MiniLM ranks Diana Rigg #1 (0.455) but Honor Blackman only #10 (0.235) and Barbara Bach #13; an Ursula Andress interview is #3. This is what the model really returns, so don't oversell it; a different model or question wording would change it.
- Next-session options: swap in a stronger model (e.g. bge/e5) and re-run the embed script; replace the corpus with real sourced text; update the slides.

**DONE (Session 22) — Act 5/6 claims made accurate, redeployed (`ibmi` mode), all 6 acts re-checked live with `python setup/_verify_bond_wording.py`.**
- Act 5 now runs a real keyword query (`LOWER(CAST(text AS VARCHAR)) LIKE` on agency/equal/operative/combat/professional; the CAST is needed because Presto reads the PG `text` column as CLOB) and returns 3 rows (1970+). The fake `vector_similarity_score` is no longer queried or shown. Labelled "Text Retrieval (Illustrative Sample)"; the corpus is flagged as 20 illustrative excerpts whose publication names are labels, not verified quotes. Vector search / RAG appear only as "We could add ...".
- Act 6: the "Semantic Agency" column is now "Review Excerpts" (COUNT of matching excerpts, 17 of 87 actresses). "Final Answer" and "Smartphone Value" lines are replaced by data-driven "What The Data Shows" (69 of 87 Thriving, descriptive only) and "What We Could Add".
- Also corrected: the "60M credits" claims (Acts 1, 2 and the tab text), the Act 1-4 `bondTakeaway` / `enterpriseTranslation` lines that overstated findings (Act 4 now states that high agency does NOT show longer careers; the Act 3 decade benchmark is context, not an adjustment).
- Still open: the `vector_similarity_score` column is still loaded by `setup/9-load-bond-data-pg.py:172` (file-order value, unused by the UI; drop it or leave it). The corpus provenance is still unverified: replace it with real sourced text, or keep the illustrative label. The Lynn-Holly quote is not in the corpus. Slides may still carry the old wording ("semantic search", "60M credits", "curse was a myth"); check them.
- Gotcha: do NOT edit `.ts` files with PowerShell `Get-Content | Set-Content` (it adds a BOM and mangles UTF-8); use the edit tools or Python.

**(Earlier) NEXT TASK notes — user directive: "be fairly accurate to the data"; say "we could" for Vector/RAG; "don't say we did things we have not done. No vibe coding!". Original findings:**
- **Corpus provenance is unverified:** `demo-ui/src/data/bond/bond_semantic_corpus.json` = 20 short hand-written texts (200-300 chars) attributed to named real publications/interviews (e.g. "Variety (1962)", "The New York Times", "Rolling Stone", "BBC Radio 4 Arts Profile"). Repo grep found NO disclosure that they are authored/illustrative. Either label as an illustrative sample or replace with verified sources. Only 17 actresses have any text.
- **Act 5 is not a vector search:** SQL is `WHERE film_year >= 1970 ORDER BY vector_similarity_score DESC LIMIT 10` on a stored column; the score is `round(0.94 - idx*0.02, 3)` in `setup/9-load-bond-data-pg.py:172` = file order. The summary line "Semantic Query: Independent agency, technical or tactical combat equality" is not used by the query.
- **Claims to correct (all in these files):** `demo-ui/src/pages/bond-investigation.tsx` lines 10, 13, 14 ("Aggregates 60M credits over 60 years", "Executes semantic similarity search across 60 years of contemporary press reviews"); `demo-ui/src/pages/api/bond-query.ts`: catalog roles "derived from ~60M IMDb credits" (Acts 1, 2), Act 5 title/subtitle/role ("Semantic Search", "60 years of reviews & interviews, scored for similarity"), "Vector Match" column header, Act 5 "Semantic Query"/"Semantic Power" lines, Act 6 role text, Act 6 "The Final Answer" ("curse was a 1-dimensional myth") and "The Smartphone Value" ("seamlessly unites ... semantic AI").
- **Honest data facts to base wording on:** Act 1: 28/76 (37%) lower after Bond (avg +0.18). Act 4: high agency does NOT show longer careers (27.0 vs 29.9 yrs). Lynn-Holly Johnson: rating delta -0.82, score 2.13, ~19 acting credits over 29 yrs (ratings fell, career thinned; not "never worked again"). Act 6: 17/87 have review text.
- **Suggested approach:** (1) relabel Act 5 as "text retrieval on a curated sample" and the score as "curated relevance (illustrative)" or drop the column; (2) add an on-screen note that the corpus is an illustrative sample; (3) in `businessInsight`/slides use "we could add embeddings + RAG (e.g. watsonx.ai / vector store)" rather than implying it ran; (4) rewrite Act 6 final line to what the data supports (no clear overall curse; individual cases like Lynn-Holly are real); (5) redeploy with `$env:BOND_PRIMARY_SOURCE='ibmi'; python setup/_deploy_ui.py` and re-check all acts via `?act=N`.

**Session 20 — FULL STACK DEPLOYED, BOND STRATEGIC INTELLIGENCE INTEGRATED, BOND DATA CORRECTED.**

- Demo UI: `http://pvm01-edaaiu5k.p1356.pok-systems.techzone.ibm.com:3000` (or SSH tunnel `-L 3000:localhost:3000`)
- **Demo 1 (Operational Agility - Satnav)**: Both scenarios (`supplier-cyber-incident` ~6s, `eu-wildfire` ~5s) live and verified.
- **Demo 2 (Strategic Intelligence - Smartphone)**: Interactive 6-Act Bond Investigation (`/bond-investigation`) deployed on remote RHEL UI with live query execution, 3-clock confounder breakdown, and commercial enterprise translation bridge.
- Verified: all endpoints (`/`, `/live`, `/sources`, `/bond-investigation`, `/api/bond-query`) return HTTP 200.
- `SATELLITE_CONNECTOR_ID` now filled in `reservation.py`; agent shows `WSR04 Connected`.

**Session 19 deployment gotchas (found this session):**
- `data/olist/*.csv` are gitignored and were **0-byte placeholders** (sellers/products/translation) → `8-load-edb-olist.py` fails with "No columns to parse". Fix: re-download from Kaggle (`kaggle.api.dataset_download_files('olistbr/brazilian-ecommerce', ...)`; `~/.kaggle/kaggle.json` is present) and copy into `data/olist/`.
- `demo-ui/` source had been deleted from the working tree (still in git) → restored with `git checkout HEAD -- demo-ui`. Check `git status` before deploying.
- `_smoke_test_ui.py` now reads `reservation.py` (was hard-coded to old reservation). Its `/api/wxd-query-internal` check always shows "Internal Server Error" — that file is a helper module with no route; ignore it. Use `setup/_check_ui_queries.py` (inject-signal + POST /api/alerts) for a real end-to-end test.
- `_start_satellite_agent.py` prints a ✅ that crashes on Windows cp1252 console (harmless; set `PYTHONIOENCODING=utf-8`).

---

**Session 20 (later) — Bond data source made tailorable; IBM i supported; UI de-branded.**

- **UI no longer names the source DB** (no PostgreSQL / Iceberg / Milvus / Satellite wording). Catalog panel shows table name + generic type ("Relational table", "Benchmark table", "Semantic review index"). The SQL panel still shows the real catalog (`pg_olist...` / `ibmi_olist...`) — needed for the query to run.
- **Tailorable primary source:** `BOND_PRIMARY_SOURCE=ibmi|pg` (env in `~/demo-ui/.env.local`, read by `bond-query.ts`). `ibmi` = career table in Db2 for i (`OLIST.BOND_CAREER_ANALYSIS`, loaded by `setup/9b-load-bond-data-ibmi.py`); `pg` (default) = PostgreSQL stands in (e.g. for Oracle on AIX, avoids licensing). Benchmarks + reviews always in PostgreSQL, so in `ibmi` mode Acts 3 and 6 are real cross-source joins.
- **Switch without rebuild:** `python setup/_set_bond_source.py ibmi|pg` (~10s). Fresh deploy: `$env:BOND_PRIMARY_SOURCE='ibmi'; python setup/_deploy_ui.py`. Verify: `python setup/_verify_bond_source.py`. IBM i table check via Presto: `python setup/_test_bond_ibmi.py`.
- **Current state: UI deployed in `ibmi` mode.** All 6 acts verified in both modes. ibmi mode is slower (Act 6 ~40s vs ~24s; Acts 1-4 ~25s vs ~12s).
- **Honest wording for slides:** Acts 1-2 (and 4) are plain single-table SQL either DB could do. Act 3 = first join (career + industry benchmarks); genuinely cross-source only in `ibmi` mode. Act 5 "semantic" = precomputed similarity score column in a table, NOT a live Milvus/vector search (no Milvus service exists in the engines dump). Act 6 = all three in one query.
- **Gotcha:** an interrupted `_deploy_ui.py` leaves stale `next` worker processes on the RHEL host; `pkill -f demo-ui/node_modules/next` before redeploying.

**Session 20 — Bond data fix (Act 6 oddities).**

- **Problem:** Grace Jones showed 0 lifetime credits / 0 active years, Denise Richards 1 credit. Cause: 5 rows in `demo-ui/src/data/bond/bond_actress_career_analysis.json` had an IMDb `nconst` pointing at a *different person with the same name* (also Jane Seymour, Barbara Bach, Daniela Bianchi).
- **Fix:** corrected `nconst` and recomputed career fields from the public IMDb datasets (method validated against Maud Adams / Britt Ekland: exact match on credits, years, ratings). All five are now "Thriving Long-Term Career" (Jones 100 credits/41 yrs, Richards 549/28, Seymour 681/53, Bach 85/47, Bianchi 25/63). The other 38 rows were checked against IMDb and are correct.
- **Redeployed:** reloaded Postgres with `python setup/9-load-bond-data-pg.py` (43 / 7 / 20 rows); `setup/_verify_live_bond_acts.py` shows all 6 acts OK. No UI rebuild needed (data is read from Postgres via Presto).
- **Helper scripts (re-runnable):** `setup/_imdb_fix_fetch.py` (streams IMDb datasets, ~15 min, writes `%TEMP%/imdb/extract.json`) and `setup/_fix_bond_nconsts.py` (applies the fix to the JSON).
- **Demo talking points / known caveats (demo-grade data):**
  - Credits are all IMDb credit types (TV episodes, talk shows, archive footage), so counts like 549/681 mean "credits", not films.
  - `*_avg_score*` columns for the 5 fixed rows are an approximation (~5% off the original formula); not shown on the Act 6 screen.
  - "Decade Avg Votes" (Act 3) = industry-wide mean IMDb votes per rated movie for the film's decade, from `industry_decade_benchmarks` (Iceberg side); same value repeats for every film in a decade. It is shown as context (Clock 3), not applied as an adjustment. Mean peaks in the 2000s then falls in the 2010s/2020s (likely more low-vote releases, newer titles, streaming effects — plausible, not proven from this data).
  - (Resolved in Session 21: headline text in `bond-query.ts` is now computed from the data.)

---

**Earlier in session 19 — IBM i Phase 1 COMPLETE.**

IBM i OLIST loaded via `setup/_diagnose_ibmi.py` (CUSTOMERS 99,441 / ORDERS 99,441 / ORDERITEMS 112,650 / PRODUCTS 32,951) and compat views applied via `_apply_ibmi_compat_views.py` (all 4 views exist). Verify with `python setup/_check_ibmi_load.py`.

Root causes of the earlier load failures (all fixed in `_diagnose_ibmi.py`):
1. `CREATE SCHEMA` in DDL conflicts with `CRTLIB` — RUNSQLSTM aborts silently. Fix: strip it before upload.
2. Failed CPYFRMIMPF attempts corrupted the file member. Fix: DLTLIB/CRTLIB reset.
3. Note: `CHKOBJ OBJ(OLIST/V_CUSTOMERS)` reports false MISSING — long SQL names get system names `V_CUS00001`/`V_ORD00001`. Check via `QSYS2.SYSTABLES` instead (`_check_ibmi_load.py`). `_check_ibmi_views.py` has this false-negative bug.

All three TechZone environments are Ready and fully operational. Federation is live:
- IBM i Db2 (`ibmi_olist`) — 99,441 customers, 112,650 order items queryable via Presto
- PostgreSQL 16 on RHEL (`pg_olist`) — 3,095 suppliers, 112,650 purchase orders
- Cross-catalog join confirmed working (PG ↔ IBM i 3-way join)
- Demo UI running on RHEL at `http://pvm01-4r13fr3k.p604.pok-systems.techzone.ibm.com:3000`

> Full session history → [`_session-log.md`](_session-log.md)
> Environment details → [`checkpoint-environments.md`](checkpoint-environments.md)

---

## Active Reservations (Session 19 — current)

All three are **Ready**. All expire **31 Oct 2026** (~12:05–12:10 UTC).

| Environment | Request ID | Status | Expires |
|---|---|---|---|
| **IBM i + RHEL** | `6ae08c9014551a1d930e9d4d` | ✅ Ready | 31 Oct 12:05 UTC |
| **watsonx.data Dev Image** | `6ae08cfd2416223c66b20f81` | ✅ Ready | 31 Oct 12:10 UTC |
| **IBM Satellite** | `6ae08d3493a341e8c94fe628` | ✅ Ready | 31 Oct 11:45 UTC |

### IBM i + RHEL credentials
| Field | Value |
|---|---|
| `RESERVATION_PREFIX` | `edaaiu5k` |
| `RESERVATION_VLAN` | `p1356` |
| `RHEL_HOST` | `pvm01-edaaiu5k.p1356.pok-systems.techzone.ibm.com` (IP: `129.40.97.178`) |
| `IBMI_HOST` | `pvm02-edaaiu5k.p1356.pok-systems.techzone.ibm.com` (IP: `129.40.97.182`) |
| `SSH_USER` | `UH6OWE8` |
| `SSH_KEY` | `C:\Users\029878866\Downloads\pvm-edaaiu5k-key.pem` ✅ saved |
| `IBMI_PASSWORD` | `a.Eh3A*03XuYEoq` |
| `IBMI_RDB` | `PVM02XED` (confirmed via DSPRDBDIRE) |

### watsonx.data Dev Image credentials
| Field | Value |
|---|---|
| `WXD_HOST` | `eu-de.services.cloud.techzone.ibm.com` |
| `WXD_SSH_PORT` | `39957` |
| `WXD_PRESTO_PORT` | `27799` |
| `WXD_SSH_USER` | `watsonx` / `WXD_SSH_PASS` = `watsonx.data` |
| `WXD_API_USER` | `ibmlhadmin` / `WXD_API_PASS` = `password` |

### IBM Satellite credentials
| Field | Value |
|---|---|
| `SATELLITE_IAM_APIKEY` | `Pauy15VZw_g3_vv5YHxFpIVI2QIgY5vXZP2sRtB2YDn3` |
| `SATELLITE_CONNECTOR_ID` | **Still needed** — check IBM Cloud console → Satellite → Connectors → `wxd-power-connector` |
| `SATELLITE_REGION` | `eu-gb` |

> `setup/reservation.py` is already populated with all of the above. `SATELLITE_CONNECTOR_ID` is the only remaining blank.

---

## What Is Known-Good This Session

- **IBM i RDB name**: `PVM02X4R` (confirmed live via `DSPRDBDIRE`)
- **Satellite endpoints**: both updated and verified via API:
  - `ibmi-db2` → `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33180` → `129.40.252.51:8471` ✅
  - `pg-olist`  → `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33156` → `129.40.252.57:5432` ✅
- **Satellite connector ID**: `U2F0ZWxsaXRlQ29ubmVjdG9yOiJkYTdoc29tbDFxc2Zhb2FhbGhqZyI` (persists across reservations for this user; new users must look it up from the IBM Cloud UI)
- **Dev Image JWT auth**: `POST https://localhost:9443/lakehouse/api/v2/auth/authenticate` with body `{"username":"ibmlhadmin","password":"password","instance_id":"0000-0000-0000-0000","instance_name":"lh-default"}` → returns `accessToken` ✅
- **Dev Image registration payload**: credentials go inside `database_details` (not top-level) in v2.2
- **Dev Image always does a live connection test** before registering a catalog — no skip option exists. Registration will fail until Satellite agent is running on RHEL.

---

## What Was Done This Session (Session 19 — Deployment)

- DRDA password set: `CPC2205: User profile UH6OWE8 changed.` ✅
- `IBMI_RDB` confirmed: `PVM02XED` ✅
- `reservation.py` fully populated (all except `SATELLITE_CONNECTOR_ID`) ✅
- SSH key saved to `C:\Users\029878866\Downloads\pvm-edaaiu5k-key.pem` ✅
- Recipe fixes committed: `d7f3a96` (requirements.txt, .gitattributes, parse_ts fix, VLAN fix, Step 8b)
- **IBM i data load NOT YET COMPLETE** — blocked by two bugs found and fixed during this session:
  - DDL `CREATE SCHEMA` conflict: fixed in `_diagnose_ibmi.py` (strips the line before RUNSQLSTM)
  - `DLTLIB OLIST` succeeded (`CPC2194`) and `CRTLIB OLIST` succeeded (`CPC2102`) — library is clean
  - Final script `_diagnose_ibmi.py` runs DDL + full data load in one pass — was mid-run when context limit hit
- `setup/_diagnose_ibmi.py` is the **complete Phase 1 reset + load script** — run it first in the new session

---

## What Was Done This Session (Session 18 — Recipe Fixes)

- **Fix: Satellite ACL gap** — Step 8b added to RUNBOOK.md: new users must authorise their IAM Service ID on `wxd-power-connector` before starting the agent. `_start_satellite_agent.py` now resolves and prints the Service ID automatically.
- **Fix: Satellite API outage guidance** — Added guidance to Step 8 for HTTP 503 / LG0009 errors (IBM Cloud Satellite Link API outage not reflected on status page).
- **Fix: Timestamp format bug** — `parse_ts()` in `6-load-ibmi-olist.py` now outputs `YYYY-MM-DD-HH.MM.SS` (IBM i CPYFRMIMPF format) not `YYYY-MM-DD HH:MM:SS` (SQL format). This fixes CPF2817 field errors on ORDERS and ORDERITEMS.
- **Fix: Hard-coded VLAN** — `reservation.py.template` previously hard-coded `.p1223.` in the FQDN. Replaced with `RESERVATION_VLAN` variable (separate from `RESERVATION_PREFIX`). RUNBOOK prerequisites table updated. This was the issue Andrew observed with the `p1226` reference.
- **Fix: Missing requirements.txt** — Added `setup/requirements.txt` listing `paramiko`, `pandas`, `psycopg2-binary`, `kaggle`, `requests`, `ibm-cloud-sdk-core`.
- **Fix: CRLF line endings** — Added `.gitattributes` enforcing `eol=lf` for `*.del`, `*.sql`, `*.sh`, and `*.py` files. The existing `.del` files in `data/olist_transformed/` should be recommitted after this to strip the Windows CRLF endings from git history.

---

## What Was Done This Session (Session 17)

- IBM i DRDA password set via `setup/0-set-ibmi-password.py`
- IBM i OLIST library loaded (99,441 customers, 112,650 order items, 32,951 products, 99,441 orders)
- IBM i compat views created: `V_CUSTOMERS`, `V_ORDERS`, `V_ORDERITEMS`, `V_PRODUCTS` (no SECTOR col)
- RHEL: PostgreSQL 16 installed from PGDG repo (ppc64le), initialised, remote access configured
- RHEL: EDB olist data loaded — 3,095 suppliers, 23 warehouses, 112,650 purchase orders (GBP/GB)
- RHEL: PostgreSQL compat views applied (`v_suppliers`, `v_warehouses`, `v_tier2_suppliers`, `v_purchase_orders`)
- Satellite connector agent started via podman (ICR login required) — confirmed `WSR04 Connected`
- `pg_olist` and `ibmi_olist` registered in watsonx.data; `catalog_engine` rows inserted manually
- `setup/7-register-catalogs.py` password fixed: `edbadmin` (not `edbadmin1`)
- `test_federation_live.py` fixed: IBM i uses `count("customer id")` not `count(*)`
- Presto restarted to pick up new catalog_engine rows (45–60s boot time)
- Demo UI built and started on RHEL port 3000 — all pages HTTP 200, `/api/detect-signals` ok
- Query latency fix: `v_compromised_exposure` pre-aggregated view added to PostgreSQL; cyber exposure query now reads 1 row instead of 3-way join over 112k rows — ~35s → ~5s
- Poll interval reduced: 1,500ms → 500ms in `wxd-query-internal.ts`

---

## Next Steps (for a NEW TechZone reservation)

All steps are now scripted. On a fresh reservation, run in this order:

```bash
# Phase 1 — IBM i
python3 setup/0-set-ibmi-password.py --host <ibmi-fqdn> --user <user> --key <key> --password <pass>
python3 setup/6-load-ibmi-olist.py --host <ibmi-fqdn> --user <user> --ssh-key <key> --create-schema --skip-download --data-dir ./data/olist
python3 setup/_apply_ibmi_compat_views.py       # (update HOST/USER/KEY at top first)

# Phase 2 — RHEL
python3 setup/_setup_pg.py                       # creates edbadmin/olist DB
python3 setup/8-load-edb-olist.py --host <rhel-fqdn> --ssh-user <user> --ssh-key <key> --db-user edbadmin --db-password edbadmin --db-port 5432 --create-schema --skip-download --data-dir ./data/olist
python3 setup/_apply_pg_compat_views.py          # applies v_suppliers etc.
python3 setup/_configure_pg_remote.py            # listen_addresses=* + md5 auth
python3 setup/_restart_pg.py                     # full restart to pick up listen_addresses
python3 setup/2-configure-satellite.py           # update Satellite endpoints if IPs changed
python3 setup/_start_satellite_agent.py          # podman login ICR + start agent
python3 setup/_check_satellite_status.py         # confirm WSR04 Connected

# Phase 3 — watsonx.data
python3 setup/7-register-catalogs.py
python3 setup/_fix_catalog_engine.py             # insert catalog_engine rows + restart Presto
# wait ~60s for Presto to boot
python3 setup/test_federation_live.py
python3 setup/test_cross_catalog_join.py

# Phase 4 — Demo UI
python3 setup/_deploy_ui.py                      # uploads, builds, starts on port 3000
python3 setup/_check_ui.py                       # smoke test
```

---

## Known Quirks

- **Cyber query latency ~5s** — this is correct and expected; the spinner reinforces the "live federation" story. The `v_compromised_exposure` view pushes aggregation down to PostgreSQL (predicate pushdown), so Presto reads 1 row over the Satellite tunnel rather than joining 112k rows. Do not try to make it faster — 5s looks real, <1s looks fake.
- **IBM i `COUNT(*)`** fails with `SQL0206` — always use `COUNT("column_name")` for IBM i tables
- **IBM i `SELECT 1`** also fails — Presto/JDBC sends it as a NULL literal which IBM i rejects
- **`V_PRODUCTS` has no `SECTOR` column** — the SECTOR enrichment step hasn't been run; view works without it
- **Demo UI port 3000** is not exposed externally through TechZone network — access via SSH tunnel: `ssh -L 3000:localhost:3000 -i <key> <user>@<rhel-fqdn>` then browse `http://localhost:3000`
- **IBM i column names have spaces** not underscores — e.g. `"customer id"`, `"order id"`, `"seller id"`. Always quote them in Presto SQL
- **podman not docker** on RHEL 9 ppc64le — use `sudo podman` for all container ops
- **NodeSource doesn't support ppc64le** — Node.js installed from RHEL repos (v16), which works fine for Next.js 14

---

## Starting a New Task

### Continuing with the CURRENT reservation (session 19/20 active through 31 Oct)

```
Continuing the watsonx.data on IBM Power demo — session 20.
Read _checkpoint.md for the current state. The full stack is live:
  IBM i + RHEL: UH6OWE8 / a.Eh3A*03XuYEoq / pvm-edaaiu5k-key.pem
  Dev Image: SSH 39957 / Presto 27799 / eu-de.services.cloud.techzone.ibm.com
  Demo UI: http://pvm01-edaaiu5k.p1356.pok-systems.techzone.ibm.com:3000
  Bond UI: http://pvm01-edaaiu5k.p1356.pok-systems.techzone.ibm.com:3000/bond-investigation
```

### Starting a FRESH TechZone reservation

```
New TechZone reservation for the watsonx.data on IBM Power demo.
Read setup/RUNBOOK.md for the authoritative setup steps.

I have updated setup/reservation.py with the new credentials:
  RESERVATION_PREFIX = "<new-prefix>"
  SSH_USER  = "<USER>"
  SSH_KEY   = r"C:\Users\029878866\Downloads\<key>.pem"
  IBMI_PASSWORD = "<password>"
  IBMI_RDB      = "<RDBNAME>"
  WXD_SSH_PORT  = <port>
  WXD_PRESTO_PORT = <port>

Please run each phase of the RUNBOOK in order (Phases 1–4).
All credentials are in reservation.py — no need to edit individual scripts.
```

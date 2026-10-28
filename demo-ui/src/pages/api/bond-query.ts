import type { NextApiRequest, NextApiResponse } from 'next'
import { runPrestoQueryInternal } from './wxd-query-internal'

// ---------------------------------------------------------------------------
// Tailorable primary data source for the career table (the "system of record").
//   BOND_PRIMARY_SOURCE=pg   (default) PostgreSQL stands in (e.g. for Oracle on AIX)
//   BOND_PRIMARY_SOURCE=ibmi            Db2 for i holds it (IBM i audiences)
// The benchmark and review tables always come from PostgreSQL, so with 'ibmi'
// Acts 3 and 6 are genuine cross-source joins (Db2 for i + PostgreSQL).
// ---------------------------------------------------------------------------
const PRIMARY_IS_IBMI = (process.env.BOND_PRIMARY_SOURCE ?? 'pg').toLowerCase() === 'ibmi'
const CAREER_TABLE = PRIMARY_IS_IBMI
  ? 'ibmi_olist.olist.bond_career_analysis'
  : 'pg_olist.public.bond_career_analysis'
const CAREER_ENGINE = PRIMARY_IS_IBMI ? 'Db2 for i (system of record)' : 'Relational table'

export interface BondQueryResult {
  act: number
  title: string
  subtitle: string
  sql: string
  catalogsQueried: Array<{ name: string; engine: string; role: string }>
  executionTimeMs: number
  columns: Array<{ key: string; header: string; format?: 'number' | 'score' | 'tag' | 'text' }>
  rows: any[]
  summaryStats: Record<string, string | number>
  businessInsight: {
    bondTakeaway: string
    enterpriseTranslation: string
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const act = parseInt((req.query.act as string) || '1', 10)
  const startTime = Date.now()

  try {
    switch (act) {
      case 1: {
        const sql = `SELECT
    actress_name,
    film_title,
    release_year,
    pre_bond_avg_rating,
    post_bond_avg_rating_lifetime AS post_bond_avg_rating,
    rating_delta_naive AS rating_delta
FROM ${CAREER_TABLE}
WHERE pre_bond_avg_rating IS NOT NULL
ORDER BY release_year ASC`

        const prestoResult = await runPrestoQueryInternal(sql)
        const executionTimeMs = Date.now() - startTime

        const rows = prestoResult.rows.map((r: any[]) => {
          const delta = r[5] !== null ? Number(r[5]) : null
          return {
            actress_name: r[0],
            film_title: r[1],
            release_year: r[2],
            pre_bond_avg_rating: r[3] !== null ? Number(r[3]) : null,
            post_bond_avg_rating: r[4] !== null ? Number(r[4]) : null,
            rating_delta: delta,
            status: delta === null ? 'No Post-Bond Rating' : delta < 0 ? 'Negative Delta' : 'Positive Delta',
          }
        })

        // Average only over rows that actually have a delta (a null delta is not a delta of 0)
        const deltas = rows.map((r) => r.rating_delta).filter((d): d is number => d !== null)
        const avgDelta = (deltas.reduce((a, d) => a + d, 0) / (deltas.length || 1)).toFixed(2)
        const negCount = deltas.filter((d) => d < 0).length

        const result: BondQueryResult = {
          act: 1,
          title: 'Act 1 — The Naive Question ("The Nokia 3310 Approach")',
          subtitle: 'Does an actress\'s average IMDb rating drop after appearing in a Bond film?',
          sql,
          catalogsQueried: [
            { name: 'bond_career_analysis', engine: CAREER_ENGINE, role: 'Career credits & ratings (derived from public IMDb datasets)' }
          ],
          executionTimeMs,
          columns: [
            { key: 'actress_name', header: 'Actress' },
            { key: 'film_title', header: 'Bond Film' },
            { key: 'release_year', header: 'Year', format: 'number' },
            { key: 'pre_bond_avg_rating', header: 'Pre-Bond Rating', format: 'score' },
            { key: 'post_bond_avg_rating', header: 'Post-Bond Rating', format: 'score' },
            { key: 'rating_delta', header: 'Delta', format: 'score' },
            { key: 'status', header: 'Naive Status', format: 'tag' },
          ],
          rows,
          summaryStats: {
            'Live Records Fetched': `${rows.length} Actresses (with a pre-Bond rating)`,
            'Presto Query Latency': `${executionTimeMs} ms`,
            'Average Rating Delta': `${avgDelta} pts`,
            'Initial Conclusion': `${negCount} of ${deltas.length} actresses (${Math.round((100 * negCount) / (deltas.length || 1))}%) show a lower average rating after Bond`
          },
          businessInsight: {
            bondTakeaway: 'A single pre/post rating average gives a partial picture: it ignores career length, volume and era.',
            enterpriseTranslation: 'A 1-table report on customer spend before/after a portal launch can mislead, because it hides account lifecycle context.'
          }
        }
        return res.status(200).json(result)
      }

      case 2: {
        const sql = `SELECT
    bond_era,
    COUNT(DISTINCT actress_name) AS actress_count,
    ROUND(AVG(pre_bond_credits), 1) AS avg_pre_credits,
    ROUND(AVG(post_bond_credits_5y), 1) AS avg_post_5y,
    ROUND(AVG(post_bond_credits_lifetime), 1) AS avg_post_lifetime,
    ROUND(AVG(post_bond_active_years), 1) AS avg_active_years,
    ROUND(AVG(rating_delta_naive), 2) AS avg_rating_delta,
    COUNT(*) AS cast_rows
FROM ${CAREER_TABLE}
GROUP BY bond_era
ORDER BY MIN(release_year) ASC`

        const prestoResult = await runPrestoQueryInternal(sql)
        const executionTimeMs = Date.now() - startTime

        const rows = prestoResult.rows.map((r: any[]) => ({
          bond_era: r[0],
          actress_count: Number(r[1]),
          avg_pre_credits: Number(r[2]),
          avg_post_5y: Number(r[3]),
          avg_post_lifetime: Number(r[4]),
          avg_active_years: Number(r[5]),
          avg_rating_delta: r[6] !== null ? Number(r[6]) : 0,
          cast_rows: Number(r[7]),
        }))

        // Overall means, weighted by the number of rows behind each era average
        const totalRows = rows.reduce((a, r) => a + r.cast_rows, 0) || 1
        const wMean = (key: 'avg_active_years' | 'avg_post_lifetime') =>
          (rows.reduce((a, r) => a + r[key] * r.cast_rows, 0) / totalRows).toFixed(1)

        const result: BondQueryResult = {
          act: 2,
          title: 'Act 2 — Compared with What? (Career Longevity Baseline)',
          subtitle: 'Did screen careers actually end, or did Bond simply set an exceptional baseline?',
          sql,
          catalogsQueried: [
            { name: 'bond_career_analysis', engine: CAREER_ENGINE, role: 'Career credit timelines (derived from public IMDb datasets)' }
          ],
          executionTimeMs,
          columns: [
            { key: 'bond_era', header: 'Bond Era' },
            { key: 'actress_count', header: 'Cast Count', format: 'number' },
            { key: 'avg_pre_credits', header: 'Avg Pre-Bond Credits', format: 'number' },
            { key: 'avg_post_5y', header: 'Avg Post-Bond (5 Yrs)', format: 'number' },
            { key: 'avg_post_lifetime', header: 'Avg Lifetime Post-Credits', format: 'number' },
            { key: 'avg_active_years', header: 'Avg Post-Bond Career (Yrs)', format: 'number' },
            { key: 'avg_rating_delta', header: 'Rating Delta', format: 'score' },
          ],
          rows,
          summaryStats: {
            'Presto Query Latency': `${executionTimeMs} ms`,
            'Mean Post-Bond Career': `${wMean('avg_active_years')} Active Years (acting credits)`,
            'Mean Post-Bond Credits': `${wMean('avg_post_lifetime')} Screen Appearances (all credits)`,
            'Longevity Finding': 'On average, acting careers continued for decades after the Bond film.'
          },
          businessInsight: {
            bondTakeaway: 'Judged by credit volume and career span rather than a single rating average, most of this cast kept working.',
            enterpriseTranslation: 'High-value transactional spikes distort normal baseline trends unless evaluated across longitudinal windows.'
          }
        }
        return res.status(200).json(result)
      }

      case 3: {
        const sql = `SELECT
    b.actress_name,
    b.film_title,
    b.release_year,
    b.age_at_bond,
    b.age_group,
    b.prior_career_years,
    ind.mean_votes_per_movie AS decade_avg_votes,
    b.post_bond_avg_score_lifetime AS weighted_success_score,
    b.career_trajectory,
    b.bond_era
FROM ${CAREER_TABLE} b
JOIN pg_olist.public.industry_decade_benchmarks ind
  ON ind.decade = CONCAT(CAST((b.release_year / 10) * 10 AS VARCHAR), 's')
ORDER BY b.release_year ASC`

        const prestoResult = await runPrestoQueryInternal(sql)
        const executionTimeMs = Date.now() - startTime

        const rows = prestoResult.rows.map((r: any[]) => ({
          actress_name: r[0],
          film_title: r[1],
          release_year: Number(r[2]),
          age_at_bond: r[3] !== null ? Number(r[3]) : 'N/A',
          age_group: r[4],
          decade_mean_votes: Number(r[6]),
          post_bond_avg_score: r[7] !== null ? Number(r[7]) : '— (no rated credits)',
          career_trajectory: r[8],
        }))

        // Clock summaries computed from the returned rows
        const ages = rows.map((r) => r.age_at_bond).filter((a): a is number => typeof a === 'number')
        const meanAge = (ages.reduce((a, b) => a + b, 0) / (ages.length || 1)).toFixed(1)
        const eraCount = new Set(prestoResult.rows.map((r: any[]) => r[9])).size
        const decadeOf = (y: number) => `${Math.floor(y / 10) * 10}s`
        const firstRow = rows[0]
        const lastRow = rows[rows.length - 1]
        // Compare the earliest decade with the decade of highest average votes (recent films have had less time to accrue votes)
        const peakRow = rows.reduce((best, r) => (r.decade_mean_votes > best.decade_mean_votes ? r : best), rows[0])
        const votes = (n: number) => Math.round(n).toLocaleString('en-US')

        const result: BondQueryResult = {
          act: 3,
          title: 'Act 3 — The 3-Clock Confounder Model',
          subtitle: 'Fusing Actress Career Clock, Franchise Clock, and Decade Vote Inflation',
          sql,
          catalogsQueried: [
            { name: 'bond_career_analysis', engine: CAREER_ENGINE, role: 'Performer bio & credits' },
            { name: 'industry_decade_benchmarks', engine: 'Benchmark table', role: 'Cinema industry macro benchmarks by decade' }
          ],
          executionTimeMs,
          columns: [
            { key: 'actress_name', header: 'Actress' },
            { key: 'film_title', header: 'Film' },
            { key: 'release_year', header: 'Year', format: 'number' },
            { key: 'age_at_bond', header: 'Age at Bond', format: 'number' },
            { key: 'age_group', header: 'Career Stage', format: 'tag' },
            { key: 'decade_mean_votes', header: 'Decade Avg Votes', format: 'number' },
            { key: 'post_bond_avg_score', header: 'Weighted Score', format: 'score' },
            { key: 'career_trajectory', header: 'Trajectory', format: 'tag' },
          ],
          rows,
          summaryStats: {
            'Presto Query Latency': `${executionTimeMs} ms`,
            'Live Records Fetched': `${rows.length} Actresses (with a decade benchmark)`,
            'Clock 1 (Age)': `Average age at casting: ${meanAge} years`,
            'Clock 2 (Franchise)': firstRow ? `${eraCount} distinct eras spanning ${firstRow.release_year}–${lastRow.release_year}` : 'n/a',
            'Clock 3 (Vote Inflation)': firstRow ? `${decadeOf(firstRow.release_year)} avg votes (${votes(firstRow.decade_mean_votes)}) vs ${decadeOf(peakRow.release_year)} avg votes (${votes(peakRow.decade_mean_votes)}, peak decade)` : 'n/a'
          },
          businessInsight: {
            bondTakeaway: 'Vote counts differ widely by decade, so raw scores from different eras are not directly comparable. Here the decade benchmark is shown as context; it is not applied as an adjustment.',
            enterpriseTranslation: 'Comparing raw customer metrics from 2012 with 2026 without normalizing for market macro conditions yields invalid conclusions.'
          }
        }
        return res.status(200).json(result)
      }

      case 4: {
        const sql = `SELECT
    CASE
        WHEN character_depth_score >= 8 THEN 'High Agency (8-10): Professional Equals / Masterminds'
        WHEN character_depth_score >= 5 THEN 'Moderate Agency (5-7): Active Allies / Operatives'
        ELSE 'Low Agency (1-4): Decorative / Early Tropes'
    END AS agency_tier,
    COUNT(*) AS character_count,
    ROUND(AVG(character_depth_score), 2) AS avg_depth_score,
    ROUND(AVG(prior_career_years), 1) AS avg_prior_career_years,
    ROUND(AVG(pre_bond_credits), 1) AS avg_pre_bond_credits,
    ROUND(AVG(post_bond_credits_lifetime), 1) AS avg_post_credits_lifetime,
    ROUND(AVG(post_bond_active_years), 1) AS avg_post_active_years,
    ROUND(AVG(post_bond_avg_rating_lifetime), 2) AS avg_post_rating,
    array_join(slice(array_agg(actress_name ORDER BY character_depth_score DESC, post_bond_credits_lifetime DESC), 1, 8), ', ') AS top_examples
FROM ${CAREER_TABLE}
GROUP BY 1
ORDER BY avg_depth_score DESC`

        const prestoResult = await runPrestoQueryInternal(sql)
        const executionTimeMs = Date.now() - startTime

        const rows = prestoResult.rows.map((r: any[]) => ({
          agency_tier: r[0],
          character_count: Number(r[1]),
          avg_depth_score: Number(r[2]),
          avg_prior_years: Number(r[3]),
          avg_pre_credits: Number(r[4]),
          avg_post_credits: Number(r[5]),
          avg_active_years: Number(r[6]),
          avg_post_rating: Number(r[7]),
          top_examples: String(r[8]),
        }))

        const hi = rows.find((r) => String(r.agency_tier).startsWith('High'))
        const lo = rows.find((r) => String(r.agency_tier).startsWith('Low'))
        const topHigh = hi ? Array.from(new Set(hi.top_examples.split(', '))).slice(0, 5).join(', ') : 'n/a'

        const result: BondQueryResult = {
          act: 4,
          title: 'Act 4 — The Character Depth & Agency Correlation',
          subtitle: 'Is career trajectory linked to "being in Bond", or to the SUBSTANCE of the role?',
          sql,
          catalogsQueried: [
            { name: 'bond_career_analysis', engine: CAREER_ENGINE, role: 'Cast credits, trajectories & 10-pt character depth scores' }
          ],
          executionTimeMs,
          columns: [
            { key: 'agency_tier', header: 'Agency Tier' },
            { key: 'character_count', header: 'Count', format: 'number' },
            { key: 'avg_depth_score', header: 'Avg Depth Score', format: 'score' },
            { key: 'avg_prior_years', header: 'Avg Prior Career (Yrs)', format: 'number' },
            { key: 'avg_post_credits', header: 'Avg Lifetime Post-Credits', format: 'number' },
            { key: 'avg_active_years', header: 'Avg Post-Bond Career (Yrs)', format: 'number' },
            { key: 'avg_post_rating', header: 'Post-Bond Rating', format: 'score' },
          ],
          rows,
          summaryStats: {
            'Presto Query Latency': `${executionTimeMs} ms`,
            'High Agency Roles': `${hi ? hi.character_count : 0} cast, e.g. ${topHigh}`,
            'Key Finding': hi && lo
              ? `Post-Bond career: ${hi.avg_active_years} yrs (high agency) vs ${lo.avg_active_years} yrs (low agency); post-Bond rating ${hi.avg_post_rating} vs ${lo.avg_post_rating}`
              : 'n/a',
            'Confounder Check': hi && lo
              ? `Career before Bond: ${hi.avg_prior_years} yrs (high agency) vs ${lo.avg_prior_years} yrs (low agency)`
              : 'n/a'
          },
          businessInsight: {
            bondTakeaway: hi && lo
              ? `In this sample, high-agency roles do not show longer post-Bond careers (${hi.avg_active_years} vs ${lo.avg_active_years} yrs); prior career length differs between tiers (${hi.avg_prior_years} vs ${lo.avg_prior_years} yrs). Agency scores are editorial judgments.`
              : 'n/a',
            enterpriseTranslation: 'Segmenting customers by a structured attribute (here, role depth) and comparing outcomes per segment tests an assumption instead of taking it for granted, even when the result is not what you expected.'
          }
        }
        return res.status(200).json(result)
      }

      case 5: {
        // Real embeddings (sentence-transformers/all-MiniLM-L6-v2), computed OFFLINE on a laptop by
        // setup/_embed_bond_corpus.py and stored as static JSON arrays. Presto computes the cosine similarity
        // (vectors are L2-normalised, so cosine = dot product). Brute force over 20 rows: no vector index,
        // no vector database, no model running on Power, and only the one pre-embedded query (Q1).
        const sql = `WITH q AS (
  SELECT query_text,
         CAST(json_parse(CAST(embedding AS VARCHAR)) AS ARRAY(DOUBLE)) AS qv
  FROM pg_olist.public.bond_semantic_queries
  WHERE query_id = 'Q1'
)
SELECT
    r.doc_id, r.actress_name, r.character_name, r.film_title, r.film_year,
    r.source_type, r.publication,
    reduce(zip_with(CAST(json_parse(CAST(r.embedding AS VARCHAR)) AS ARRAY(DOUBLE)), q.qv, (a, b) -> a * b),
           CAST(0 AS DOUBLE), (s, x) -> s + x, s -> s) AS cosine_similarity,
    r.text,
    q.query_text
FROM pg_olist.public.bond_semantic_reviews r
CROSS JOIN q
ORDER BY cosine_similarity DESC
LIMIT 8`

        const prestoResult = await runPrestoQueryInternal(sql)
        const executionTimeMs = Date.now() - startTime

        const rows = prestoResult.rows.map((r: any[]) => ({
          doc_id: r[0],
          actress_name: r[1],
          character_name: r[2],
          film_title: r[3],
          film_year: Number(r[4]),
          source_type: r[5],
          publication: r[6],
          cosine_similarity: Number(r[7]),
          text: r[8],
        }))
        const queryText = prestoResult.rows[0] ? String(prestoResult.rows[0][9]) : 'n/a'

        const result: BondQueryResult = {
          act: 5,
          title: 'Act 5 — Questions Outgrow SQL Columns (Similarity Ranking on Real Embeddings)',
          subtitle: 'Ranking 20 illustrative excerpts by cosine similarity to one pre-embedded question. A static demo, not RAG.',
          sql,
          catalogsQueried: [
            { name: 'bond_semantic_reviews', engine: 'Text + embedding table', role: '20 illustrative excerpts with stored 384-dim embeddings' },
            { name: 'bond_semantic_queries', engine: 'Text + embedding table', role: 'One pre-embedded question (Q1)' }
          ],
          executionTimeMs,
          columns: [
            { key: 'actress_name', header: 'Actress' },
            { key: 'character_name', header: 'Character' },
            { key: 'film_title', header: 'Film' },
            { key: 'film_year', header: 'Year', format: 'number' },
            { key: 'source_type', header: 'Source Type', format: 'tag' },
            { key: 'publication', header: 'Publication (label)' },
            { key: 'cosine_similarity', header: 'Cosine Similarity', format: 'score' },
            { key: 'text', header: 'Corpus Excerpt (illustrative)' },
          ],
          rows,
          summaryStats: {
            'Presto Query Latency': `${executionTimeMs} ms`,
            'Question (pre-embedded)': `"${queryText}"`,
            'Embeddings': 'all-MiniLM-L6-v2 (Hugging Face), 384-dim, computed offline on a laptop and stored as static values. No model runs on Power.',
            'What Presto Did': 'Parsed the stored vectors and computed cosine similarity in SQL (brute force over 20 rows; no vector index or vector database).',
            'Corpus': '20 short illustrative excerpts. Publication names are labels, not verified quotes.',
            'What We Could Add': 'Embed new questions live (e.g. watsonx.ai), a vector store, and RAG over real, licensed review text.'
          },
          businessInsight: {
            bondTakeaway: 'Rows are ranked by meaning, not keywords, using real embedding vectors. It only works for the one question embedded in advance, and the text is an illustrative sample, so treat it as a demonstration of the mechanism, not as evidence.',
            enterpriseTranslation: 'Customer sentiment, warranty claims and account manager notes often hold context that structured invoices miss. We could embed them and use RAG to answer questions over them; this act shows only the similarity-ranking step.'
          }
        }
        return res.status(200).json(result)
      }

      case 6:
      default: {
        const sql = `SELECT
    b.actress_name,
    b.character_name,
    b.film_title,
    b.release_year,
    b.bond_era,
    b.character_depth_score,
    b.post_bond_credits_lifetime AS post_bond_credits,
    b.post_bond_active_years AS post_active_years,
    b.career_trajectory,
    MAX(v.cosine_similarity) AS agency_similarity
FROM ${CAREER_TABLE} b
JOIN pg_olist.public.industry_decade_benchmarks ind
  ON ind.decade = CONCAT(CAST((b.release_year / 10) * 10 AS VARCHAR), 's')
LEFT JOIN (
  SELECT r.actress_name, r.film_title,
         reduce(zip_with(CAST(json_parse(CAST(r.embedding AS VARCHAR)) AS ARRAY(DOUBLE)),
                         CAST(json_parse(CAST(q.embedding AS VARCHAR)) AS ARRAY(DOUBLE)), (a, b) -> a * b),
                CAST(0 AS DOUBLE), (s, x) -> s + x, s -> s) AS cosine_similarity
  FROM pg_olist.public.bond_semantic_reviews r
  CROSS JOIN pg_olist.public.bond_semantic_queries q
  WHERE q.query_id = 'Q1'
) v ON v.actress_name = b.actress_name AND v.film_title = b.film_title
GROUP BY 1,2,3,4,5,6,7,8,9
ORDER BY b.release_year ASC, b.character_depth_score DESC`

        const prestoResult = await runPrestoQueryInternal(sql)
        const executionTimeMs = Date.now() - startTime

        const rows = prestoResult.rows.map((r: any[]) => ({
          actress_name: r[0],
          character_name: r[1],
          film_title: r[2],
          release_year: Number(r[3]),
          bond_era: r[4],
          character_depth_score: Number(r[5]),
          post_bond_credits: Number(r[6]),
          post_active_years: Number(r[7]),
          career_trajectory: r[8],
          agency_similarity: r[9] !== null ? Number(r[9]) : '—',
        }))
        const withText = rows.filter((r) => typeof r.agency_similarity === 'number').length
        const thriving = rows.filter((r) => String(r.career_trajectory).startsWith('Thriving')).length

        const result: BondQueryResult = {
          act: 6,
          title: 'Act 6 — The Lakehouse Unified Synthesis ("The Smartphone Operating Model")',
          subtitle: 'Joining Relational Credits + Industry Baselines + Embedding Similarity (Illustrative Text) in One Presto Query',
          sql,
          catalogsQueried: [
            { name: 'bond_career_analysis', engine: CAREER_ENGINE, role: 'Performer bio & lifetime credits' },
            { name: 'industry_decade_benchmarks', engine: 'Benchmark table', role: 'Industry decade vote benchmarks' },
            { name: 'bond_semantic_reviews', engine: 'Text + embedding table', role: '20 illustrative excerpts with stored embeddings' },
            { name: 'bond_semantic_queries', engine: 'Text + embedding table', role: 'One pre-embedded question (Q1)' }
          ],
          executionTimeMs,
          columns: [
            { key: 'actress_name', header: 'Actress' },
            { key: 'character_name', header: 'Character' },
            { key: 'film_title', header: 'Film' },
            { key: 'release_year', header: 'Year', format: 'number' },
            { key: 'bond_era', header: 'Era', format: 'tag' },
            { key: 'character_depth_score', header: 'Agency Score', format: 'score' },
            { key: 'post_bond_credits', header: 'Lifetime Credits', format: 'number' },
            { key: 'post_active_years', header: 'Active Yrs', format: 'number' },
            { key: 'career_trajectory', header: 'Outcome', format: 'tag' },
            { key: 'agency_similarity', header: 'Agency Similarity (Q1)', format: 'score' },
          ],
          rows,
          summaryStats: {
            'Presto Query Latency': `${executionTimeMs} ms`,
            'Tables Joined': `Career, decade benchmark and embedding tables in one query${PRIMARY_IS_IBMI ? '; career table on Db2 for i, others on PostgreSQL' : ''}`,
            'Embedding Evidence': `${withText} of ${rows.length} actresses have an excerpt scored against Q1 (illustrative sample, static embeddings)`,
            'What The Data Shows': `${thriving} of ${rows.length} have a "Thriving Long-Term Career" by acting credits; no overall curse is visible here, but individual careers differ (descriptive only, not causal).`,
            'What We Could Add': 'Live embedding of new questions (e.g. watsonx.ai), a vector store, and RAG over real review text.'
          },
          businessInsight: {
            bondTakeaway: 'One query can join career history, decade benchmarks and embedding similarity. The text is a small illustrative sample, so the similarity column adds colour rather than evidence.',
            enterpriseTranslation: 'Enterprises can join transactional data (e.g. Db2 for i) with lakehouse tables and stored embedding similarity in one query. Live embedding and RAG over real documents are what we could add.'
          }
        }
        return res.status(200).json(result)
      }
    }
  } catch (err: any) {
    console.error(`[bond-query] Error in Act ${act}:`, err)
    return res.status(500).json({ error: err.message || String(err) })
  }
}

// Made with Bob

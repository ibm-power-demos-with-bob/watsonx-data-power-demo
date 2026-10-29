#!/usr/bin/env python3
"""
Load Bond Investigation & IMDb 3-Clock Tables into PostgreSQL on RHEL.
These tables will be queryable by watsonx.data Presto via the `pg_olist` catalog.
"""

import json
import os
import sys
from pathlib import Path
import paramiko

sys.path.insert(0, os.path.dirname(__file__))
from reservation import (
    RHEL_HOST as HOST,
    SSH_USER as USER,
    SSH_KEY as KEY,
    WXD_HOST,
    WXD_PRESTO_PORT,
    WXD_API_USER,
    WXD_API_PASS,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "demo-ui" / "src" / "data" / "bond"

# Load JSON datasets
with open(DATA_DIR / "bond_actress_career_analysis.json", "r", encoding="utf-8") as f:
    career_data = json.load(f)

with open(DATA_DIR / "industry_decade_benchmarks.json", "r", encoding="utf-8") as f:
    decade_data = json.load(f)

with open(DATA_DIR / "bond_semantic_corpus.json", "r", encoding="utf-8") as f:
    corpus_data = json.load(f)

# Static embeddings produced offline by setup/_embed_bond_corpus.py (real Hugging Face model, not run on Power)
with open(DATA_DIR / "bond_semantic_embeddings.json", "r", encoding="utf-8") as f:
    emb_data = json.load(f)
EMB_BY_DOC = {d["doc_id"]: d["embedding"] for d in emb_data["documents"]}

# Connect to RHEL via SSH
try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)


def run_cmd(cmd, label=""):
    _, out, err = c.exec_command(cmd)
    rc = out.channel.recv_exit_status()
    stdout = out.read().decode("utf-8", errors="replace").strip()
    stderr = err.read().decode("utf-8", errors="replace").strip()
    if rc != 0:
        print(f"[{label}] ERR ({rc}): {stderr[:400]}")
    else:
        print(f"[{label}] OK: {stdout[:300]}")
    return rc, stdout


def main():
    print("=== Step 1: Creating Tables in PostgreSQL (database: olist) ===")

    ddl = """
    DROP TABLE IF EXISTS bond_career_analysis CASCADE;
    CREATE TABLE bond_career_analysis (
        actress_name VARCHAR(100),
        character_name VARCHAR(100),
        film_title VARCHAR(100),
        release_year INTEGER,
        bond_era VARCHAR(50),
        nconst VARCHAR(20),
        role_category VARCHAR(100),
        occupation VARCHAR(150),
        character_depth_score INTEGER,
        has_independent_objective BOOLEAN,
        professional_expertise BOOLEAN,
        participates_in_climax BOOLEAN,
        intelligence_or_combat_role BOOLEAN,
        survives_film BOOLEAN,
        age_at_bond INTEGER,
        age_group VARCHAR(50),
        prior_career_years INTEGER,
        pre_bond_credits INTEGER,
        pre_bond_avg_rating NUMERIC(4,2),
        pre_bond_avg_score NUMERIC(4,2),
        post_bond_credits_5y INTEGER,
        post_bond_avg_rating_5y NUMERIC(4,2),
        post_bond_credits_lifetime INTEGER,
        post_bond_avg_rating_lifetime NUMERIC(4,2),
        post_bond_avg_score_lifetime NUMERIC(4,2),
        post_bond_active_years INTEGER,
        rating_delta_naive NUMERIC(4,2),
        career_trajectory VARCHAR(100),
        character_description TEXT
    );

    DROP TABLE IF EXISTS industry_decade_benchmarks CASCADE;
    CREATE TABLE industry_decade_benchmarks (
        decade VARCHAR(20) PRIMARY KEY,
        total_movies_released INTEGER,
        rated_movies_count INTEGER,
        mean_imdb_rating NUMERIC(4,2),
        mean_votes_per_movie NUMERIC(10,1),
        median_votes_per_movie NUMERIC(10,1),
        p90_votes_per_movie NUMERIC(10,1)
    );

    DROP TABLE IF EXISTS bond_semantic_reviews CASCADE;
    CREATE TABLE bond_semantic_reviews (
        doc_id VARCHAR(50) PRIMARY KEY,
        actress_name VARCHAR(100),
        character_name VARCHAR(100),
        film_title VARCHAR(100),
        film_year INTEGER,
        source_year INTEGER,
        source_type VARCHAR(100),
        publication VARCHAR(150),
        source_url VARCHAR(400),
        licence VARCHAR(50),
        retrieved_at VARCHAR(20),
        text TEXT,
        embedding_model VARCHAR(100),
        embedding TEXT
    );

    DROP TABLE IF EXISTS bond_semantic_queries CASCADE;
    CREATE TABLE bond_semantic_queries (
        query_id VARCHAR(20) PRIMARY KEY,
        query_text TEXT,
        embedding_model VARCHAR(100),
        embedding TEXT
    );
    """

    # Execute DDL
    ddl_cmd = f"PGPASSWORD=edbadmin psql -h localhost -U edbadmin -d olist -c \"{ddl}\""
    run_cmd(ddl_cmd, label="psql-ddl")

    # Insert bond_career_analysis
    print("\n=== Step 2: Populating bond_career_analysis ===")
    insert_stmts = []
    for r in career_data:
        pre_r = r['pre_bond_avg_rating'] if r['pre_bond_avg_rating'] is not None else 'NULL'
        pre_s = r['pre_bond_avg_score'] if r['pre_bond_avg_score'] is not None else 'NULL'
        post_5_r = r['post_bond_avg_rating_5y'] if r['post_bond_avg_rating_5y'] is not None else 'NULL'
        post_l_r = r['post_bond_avg_rating_lifetime'] if r['post_bond_avg_rating_lifetime'] is not None else 'NULL'
        post_l_s = r['post_bond_avg_score_lifetime'] if r['post_bond_avg_score_lifetime'] is not None else 'NULL'
        delta = r['rating_delta_naive'] if r['rating_delta_naive'] is not None else 'NULL'
        age = r['age_at_bond'] if r['age_at_bond'] is not None else 'NULL'
        desc = r['character_description'].replace("'", "''")
        occ = r['occupation'].replace("'", "''")
        cname = r['character_name'].replace("'", "''")
        aname = r['actress_name'].replace("'", "''")
        ftitle = r['film_title'].replace("'", "''")

        stmt = f"""INSERT INTO bond_career_analysis VALUES (
            '{aname}', '{cname}', '{ftitle}', {r['release_year']}, '{r['bond_era']}', '{r['nconst']}',
            '{r['role_category']}', '{occ}', {r['character_depth_score']},
            {r['has_independent_objective']}, {r['professional_expertise']}, {r['participates_in_climax']},
            {r['intelligence_or_combat_role']}, {r['survives_film']}, {age}, '{r['age_group']}',
            {r['prior_career_years']}, {r['pre_bond_credits']}, {pre_r}, {pre_s},
            {r['post_bond_credits_5y']}, {post_5_r}, {r['post_bond_credits_lifetime']}, {post_l_r}, {post_l_s},
            {r['post_bond_active_years']}, {delta}, '{r['career_trajectory']}', '{desc}'
        );"""
        insert_stmts.append(stmt)

    all_inserts = "\n".join(insert_stmts)
    run_cmd(f"PGPASSWORD=edbadmin psql -h localhost -U edbadmin -d olist -c \"{all_inserts}\"", label="insert-career")

    # Insert industry_decade_benchmarks
    print("\n=== Step 3: Populating industry_decade_benchmarks ===")
    dec_inserts = []
    for d in decade_data:
        dec_inserts.append(f"""INSERT INTO industry_decade_benchmarks VALUES (
            '{d['decade']}', {d['total_movies_released']}, {d['rated_movies_count']},
            {d['mean_imdb_rating']}, {d['mean_votes_per_movie']}, {d['median_votes_per_movie']}, {d['p90_votes_per_movie']}
        );""")
    run_cmd(f"PGPASSWORD=edbadmin psql -h localhost -U edbadmin -d olist -c \"{chr(10).join(dec_inserts)}\"", label="insert-decade")

    # Insert bond_semantic_reviews
    print("\n=== Step 4: Populating bond_semantic_reviews ===")
    rev_inserts = []
    model = emb_data["model"]

    def q(s):
        return str(s).replace("'", "''")

    for doc in corpus_data:
        emb = json.dumps(EMB_BY_DOC[doc['doc_id']], separators=(",", ":"))
        rev_inserts.append(f"""INSERT INTO bond_semantic_reviews VALUES (
            '{q(doc['doc_id'])}', '{q(doc['actress_name'])}', '{q(doc['character_name'])}', '{q(doc['film_title'])}',
            {doc['film_year']}, {doc['source_year']}, '{q(doc['source_type'])}', '{q(doc['publication'])}',
            '{q(doc['source_url'])}', '{q(doc['licence'])}', '{q(doc['retrieved_at'])}',
            '{q(doc['text'])}', '{q(model)}', '{emb}'
        );""")
    # Wikipedia text contains double quotes, so the SQL is sent on psql's stdin (no shell quoting, no arg-length limit)
    stdin, out, err = c.exec_command("PGPASSWORD=edbadmin psql -v ON_ERROR_STOP=1 -q -h localhost -U edbadmin -d olist -f -")
    stdin.write("\n".join(rev_inserts))
    stdin.channel.shutdown_write()
    rc = out.channel.recv_exit_status()
    if rc != 0:
        print(f"[insert-reviews] ERR ({rc}): {err.read().decode('utf-8', errors='replace')[:400]}")
    else:
        print(f"[insert-reviews] OK: {len(rev_inserts)} rows")

    # Insert the (single, fixed) query embedding
    q = emb_data["query"]
    qtxt = q["query_text"].replace("'", "''")
    qemb = json.dumps(q["embedding"], separators=(",", ":"))
    run_cmd(f"PGPASSWORD=edbadmin psql -h localhost -U edbadmin -d olist -c \"INSERT INTO bond_semantic_queries VALUES ('{q['query_id']}', '{qtxt}', '{model}', '{qemb}');\"", label="insert-query")

    # Verify rows in PostgreSQL
    print("\n=== Step 5: Verification in PostgreSQL ===")
    run_cmd("PGPASSWORD=edbadmin psql -h localhost -U edbadmin -d olist -c \"SELECT COUNT(*) FROM bond_career_analysis; SELECT COUNT(*) FROM industry_decade_benchmarks; SELECT COUNT(*) FROM bond_semantic_reviews;\"", label="row-counts")

    c.close()
    print("\nAll Bond tables loaded into PostgreSQL on RHEL successfully!")


if __name__ == "__main__":
    main()

# Made with Bob

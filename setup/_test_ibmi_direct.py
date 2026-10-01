#!/usr/bin/env python3
"""Test various IBM i query patterns to isolate SQL0206."""
import prestodb, urllib3
urllib3.disable_warnings()

conn = prestodb.dbapi.connect(
    host="eu-de.services.cloud.techzone.ibm.com", port=48872,
    user="ibmlhadmin", catalog="ibmi_olist", schema="olist",
    http_scheme="https",
    auth=prestodb.auth.BasicAuthentication("ibmlhadmin", "password")
)
conn._http_session.verify = False
cur = conn.cursor()

tests = [
    ('SELECT 1 FROM ibmi_olist.olist.v_customers LIMIT 1', 'bare SELECT 1'),
    ('SELECT "customer id" FROM ibmi_olist.olist.v_customers LIMIT 1', 'select customer id'),
    ('SELECT "customer id", "state" FROM ibmi_olist.olist.v_customers LIMIT 3', 'select 2 cols'),
    ('SELECT count("customer id") FROM ibmi_olist.olist.v_customers', 'count(customer id)'),
    ('SELECT count(*) FROM ibmi_olist.olist.v_customers', 'count(*)'),
]

for sql, label in tests:
    try:
        cur.execute(sql)
        result = cur.fetchall()
        print(f"  OK [{label}]: {result[:3]}")
    except Exception as e:
        msg = str(e)[:120]
        print(f"  FAIL [{label}]: {msg}")

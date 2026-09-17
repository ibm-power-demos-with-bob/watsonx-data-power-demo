#!/bin/sh
system "RUNSQLSTM SRCSTMF('/tmp/olist/olist_drop.sql') COMMIT(*NONE) NAMING(*SQL) DFTRDBCOL(OLIST) ERRLVL(40)"
sleep 3
system "RUNSQLSTM SRCSTMF('/tmp/olist/olist_ddl.sql') COMMIT(*NONE) NAMING(*SQL) DFTRDBCOL(OLIST) ERRLVL(20)"
echo RC=$?

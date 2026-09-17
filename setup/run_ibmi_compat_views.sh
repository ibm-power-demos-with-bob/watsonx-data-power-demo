#!/bin/sh
system "RUNSQLSTM SRCSTMF('/tmp/10-ibmi-compat-views-drop.sql') COMMIT(*NONE) NAMING(*SQL)"
sleep 3
system "RUNSQLSTM SRCSTMF('/tmp/10-ibmi-compat-views.sql') COMMIT(*NONE) NAMING(*SQL)"

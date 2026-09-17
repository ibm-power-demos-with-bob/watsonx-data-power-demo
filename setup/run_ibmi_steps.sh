#!/bin/sh
system "RUNSQLSTM SRCSTMF('/tmp/10-ibmi-compat-views-drop.sql') COMMIT(*NONE) NAMING(*SQL)"
sleep 3
system "RUNSQLSTM SRCSTMF('/tmp/10-ibmi-compat-views.sql') COMMIT(*NONE) NAMING(*SQL)"
system "RUNSQLSTM SRCSTMF('/tmp/9-ibmi-add-sector.sql') COMMIT(*NONE) NAMING(*SQL)"

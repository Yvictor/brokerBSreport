SENTRY_DNS := https://6db9585c13094fe0a6daf59ba35bf0f1:398fc0f8893c41f2829102661ddc00f6@sentry.io/123315
Cus_Path := ''
WORKDIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

get-bsreport:
    get-twse-bsreport


# to do -> need to build cron.env
get-twse-bsreport:
    #${WORKDIR}/cron/cron.env; python -m twse
    python -m twse

# to do -> get tpex
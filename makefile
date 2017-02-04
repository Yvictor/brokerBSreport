SENTRY_DNS := 'https://6db9585c13094fe0a6daf59ba35bf0f1:398fc0f8893c41f2829102661ddc00f6@sentry.io/123315'
# Cus_Path := ''
WORKDIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

get-bsreport: get-tpex-bsreport get-twse-bsreport

# to do -> need to build cron.env
# ${WORKDIR}/cron/cron.env; python -m twse
get-twse-bsreport:
	SENTRY_DNS=${SENTRY_DNS} WORKER_NAME=twse SLP=5.7 TWSE_ORIGIN_FOLDER=0Bxlih4lHCRlmeTRCUkFpd2hkcm8  python -m twse

get-tpex-bsreport:
	SENTRY_DNS=${SENTRY_DNS} WORKER_NAME=tpex SLP=5.5 TPEX_ORIGIN_FOLDER=0Bxlih4lHCRlmd0hFVktsY0lrRzg  python -m tpex &

test-captcha-rec:
	python test_captcha_rec.py

single-test:
	python single_test.py

# brokerBSreport
TWSE and TPEX broker daily report crawler

### twseBSreport
```
SENTRY_DNS='' WORKER_NAME = '' CusPath = '' TWSE_ORIGIN_FOLDER = '' python -m twse
```

### tpexBSreport
```
SENTRY_DNS='' WORKER_NAME = '' CusPath = '' TPEX_ORIGIN_FOLDER = '' python -m tpex
```

> `make get-bsreport` will generate 2 file sort.h5 and origin_{date}.h5 the origin one will backup to cloud, sort file will append each date
> , now sort.h5 need to fix some problem
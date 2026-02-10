# Performance Notes

## Latency Headers
IronShield attaches `Server-Timing` headers to each response:
- `waf`: WAF rule evaluation time
- `ratelimit`: token bucket check
- `geo`: geo policy lookup
- `proxy`: upstream proxy duration

## Benchmarking
You can benchmark locally with:

```
hey -n 500 -c 25 http://localhost:8080/api/products
```

Compare response headers to understand pipeline overhead.

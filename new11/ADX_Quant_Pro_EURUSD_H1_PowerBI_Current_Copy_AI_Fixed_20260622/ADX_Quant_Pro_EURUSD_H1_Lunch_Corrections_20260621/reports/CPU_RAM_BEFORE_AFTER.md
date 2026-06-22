# CPU and RAM Before/After

## Prior available measurement

The package’s 2026-06-20 isolated benchmark reported:

- baseline median 0.1262 s;
- existing advanced layer median 4.0320 s;
- existing advanced layer maximum `tracemalloc` peak 3.445 MB.

## 2026-06-21 isolated fast-profile measurement

`reports/RESEARCH_VALIDATION_BENCHMARK_20260621.json` records three runs on Python 3.13.5 using 720 completed H1 rows, 3,000 canonical settled rows and 12,000 method rows:

- median elapsed: 2.7506 s;
- minimum: 2.7208 s;
- maximum: 2.9167 s;
- maximum `tracemalloc` peak: 2,417,000 bytes approximately;
- maximum observed RSS delta: 692 KB;
- output: 144 CPA rows and 6 SPA rows.

## Correct interpretation

This is an isolated component benchmark under the fast profile, not a matched whole-app before/after experiment. It demonstrates bounded execution and memory for the new layer. It does not prove the total app is faster than the uploaded package.

The new modules are absent from renderer/tab/expander call paths, so tab switching adds no new research calculation. Runtime UI/browser memory and live Streamlit Cloud cold-start measurements remain environment-dependent.

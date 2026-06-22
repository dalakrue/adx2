# Modified Files Manifest — 2026-06-20

Base ZIP: `b56f7c58-5b12-487c-89c2-e7439413c78c.zip`
Base ZIP SHA-256: `3873d325b7db90df60c98c487368a4cc94d1211b7622632dea102c857072a287`

Original files: **726** · Modified: **15** · New: **27** · Deleted: **0**

All original paths preserved: **YES**. Manifest files exclude themselves from hash inventory.

## Modified files

- `ROLLBACK_INSTRUCTIONS_20260620.md` — current history-first rollback instructions
  - before `687f11808d0d0cfb597ec9b80f431dca6d8c3cbbe8cf612d5ad3d3ff7ad9940e`
  - after  `833b4479bbe29f9ef0dd5fe840310aa4545d5e31c8565608b1fe79515a9a0390`
- `core/canonical_runtime_20260617.py` — accepts the additive history bundle during canonical atomic publication
  - before `bf3d716f947a3f64e6d380946184451c76c1cd376bd8fda0d6baf5ab333025c2`
  - after  `12e2dcc2ca12aa9b22af7758502174700bc1fcca3aefe93101c7aa8cf9b485b6`
- `core/models/quant_models.py` — Streamlit Cloud single-worker n_jobs=1 safety
  - before `ad5e88626701e5ca632a8556b4ae9c2eafa46edfa0263c978d868cfe38645908`
  - after  `e05656595928cd9b4954dc7b6d2d4c1c7e057c5e7e4ac845b4e9044c3de9be5d`
- `core/settings_run_orchestrator_20260617.py` — builds history/research evidence once inside the existing Settings transaction
  - before `9b4c0d2db28ecfc17f79035dc3fd4aad9a75c50be9ed05d5a700b06e106052fd`
  - after  `ee641e00831c583ab36b1d41d89756823e1749fce6266abd781188a1636739c1`
- `data/canonical_runtime.sqlite3` — original canonical data plus additive empty history catalog/watermarks/35 tables
  - before `bbf0c0288ccce3026b60d3b4185b8e9ad167edfee9deaf2b7b1846f94f04b7f7`
  - after  `0668c1a81fb077d8b0af105010f867d2bd89ceea69398d14355d7de39ffff2e5`
- `services/canonical_snapshot_store.py` — commits canonical snapshot and affected history rows in one SQLite transaction
  - before `f85f56e422690b3f027d0932f9f199888a48ba3ac2028ec90e0345aa3c85e527`
  - after  `72f9b026f7259c761e298f3f4d6dfc72473e36d2d4407af892d3b68ccdcc79ab`
- `tabs/ai_assistant_compact_20260619.py` — redacted grounded question/answer/evidence history persistence
  - before `55959d7712c006f4f3bb0cf871e684ed3d4d6935ea261db69826846a012461e4`
  - after  `b93c863558afba26a908152b4a5790111291fe8fe1bd3bb657b964106d156e2d`
- `tabs/antd_page_router_20260615.py` — true Morning and Research load gates
  - before `cc4ac4294b7a1d9a7803b95a03ce8e73c4930b6762677c97c928864a876496a8`
  - after  `6c47cb38f7ba393a5cae56172bfff530c4d889e2b78d3fa925ee268fc705f491`
- `tabs/engine_split/legacy_impl/original_backtest_inner_impl_parts/part_001.py` — bounded performance/lazy-render compatibility update
  - before `a1b90e4699ed6e7be5223858eeb5fc1d3160d6ff3af013cb16db356736849f8f`
  - after  `f98033e93e12f4c99bfb4e628540bccc07e1a18d18e97fd4f6b34446e3a8f911`
- `tabs/research.py` — lazy network/NLP imports and selected-workspace execution
  - before `0d4d916133a33e5464b9ab342f6ffa51298ca239272702fb9f3fe42cf77f8ccd`
  - after  `cd63b2bf85fcc1379e61875feb65fd53f3ca15f729018f7fc7bd2227fa287f4d`
- `tabs/train/legacy_impl/train_data_legacy_impl_parts/part_000.py` — bounded performance/lazy-render compatibility update
  - before `98ce961a57bae6985c1d4a7baeccdc360d2f410fad261c6c48f3ce6c11c1ca4f`
  - after  `32db2a79670a5c4bb07ffd686f5f8a79f076cc01ebe9dd17bbfd5df138c99b86`
- `tests/test_lunch_four_core_fields_20260619.py` — updated regression contract for true load gates
  - before `1831ac1690eb6dbf4270e09815e4b21d8924f0e25954a629393fd0db26c27b07`
  - after  `d0ed6830b53168fff2dd320587e14f294e3e1c2eb1f9a090103a329c3407d2d1`
- `tests/test_similar_day_intelligence_20260619.py` — updated regression contract for exclusive 4A
  - before `caaa3f214a837a007d0cf3955d9fb07e0f7047141b74d25b4d83016634c8ff0d`
  - after  `f8081646f22092121745b9cf78ed34c08d889bb3a4ce76dd47ca56ecbb782155`
- `ui/lunch_four_core_fields_20260619.py` — true six-field gates and exclusive 4A/4B placement without duplicate current renderer
  - before `c1edb8b56e493cf0cec804092c3d96f8db0329d2666ca79b7973fc0030ba5b4d`
  - after  `0e6a65548007f032036cac57bfa20606cf120219c1b1f638c6afc209b13b6b5c`
- `ui/powerbi_cached_renderer_20260619.py` — M4 display-only history aggregation
  - before `54f0ffde80cb8df16df1fc3827d6b08ee375367de485fc8605bcdd8b10f3d2ca`
  - after  `22d5f0a3427bae5892fb1d022f97fabaa22c9049b1f5b0b22cde891e2204b041`

## New files

- `ARCHITECTURE_CALL_GRAPH_20260620.md` — audit/report/inventory deliverable — 3,645 bytes — `bfceb17fa006a3feaa0067bfa13e80c1480fc9c4e0a25b0cf11f099370edaef9`
- `AUDIT_BASELINE_REPORT_20260620_HISTORY_FIRST.md` — audit/report/inventory deliverable — 3,799 bytes — `d87b76720fb94418bc6a6ec1da8ca766b852ad62651d7ea579e5fea8e4e10020`
- `AUDIT_INVENTORY_20260620.json` — audit/report/inventory deliverable — 983,422 bytes — `efd6b7441fa27ec3e396303d05cd591d222911fadc5eb997d1f11e9751ac15b6`
- `CACHE_INVENTORY_20260620.json` — audit/report/inventory deliverable — 2,827 bytes — `a77a9d76e4f886f38207f7bbd91b5b6e3293e20c1219c1efe02a6a8410bd0297`
- `COLUMNAR_ARCHIVE_DECISION_20260620.json` — audit/report/inventory deliverable — 12,021 bytes — `dd1585e03b1c559c1ede9d1c9758cc0528d091a92ad1fdc4c0395d71858b9e4d`
- `DATABASE_MIGRATION_REPORT_20260620_HISTORY_EVIDENCE.md` — audit/report/inventory deliverable — 7,437 bytes — `fbaf8f6a29e481bc360dcacf69be9397697359a7eb386cc7b5e86cbeb5c89dc5`
- `DATABASE_SCHEMA_INVENTORY_20260620.json` — audit/report/inventory deliverable — 326,173 bytes — `b4a3c71c80f65b83da1415909692ef4b3e97c2ff1809741d5f969591b5940a5d`
- `IMPLEMENTATION_REPORT_20260620_HISTORY_FIRST.md` — audit/report/inventory deliverable — 2,888 bytes — `023d59e48a7059bfb08c33ca53bb5ffffe82b5851031177940d1f4fa127e4a79`
- `LIMITATIONS_EVIDENCE_20260620.md` — audit/report/inventory deliverable — 2,218 bytes — `ab5afc649408f2f38d02825ee841a22a138272a77ba6fb4a9d1b5307a6eceea9`
- `PERFORMANCE_MEASUREMENTS_20260620_HISTORY_FIRST.json` — audit/report/inventory deliverable — 3,964 bytes — `489fc018648c20df7554c40f899d3d1766cd7a63007cc92a42775843757c42d4`
- `PERFORMANCE_REPORT_20260620_BEFORE_AFTER.md` — audit/report/inventory deliverable — 3,289 bytes — `246cae7df74b3cf19f5726f7231e916d3c23d8371d7dfb34ada6b6cbb03a5482`
- `README.md` — audit/report/inventory deliverable — 1,774 bytes — `4b73aa3f12127856d4cede523c87cd138789c6278de389a85e1b1b3622982f79`
- `TEN_PAPER_RESEARCH_MAPPING_20260620.md` — audit/report/inventory deliverable — 2,993 bytes — `83a62743850654e3223858d83f83f624b19a02e9c75f269db35004edf3ee8348`
- `TEST_REPORT_20260620_HISTORY_FIRST.md` — audit/report/inventory deliverable — 1,607 bytes — `059bad316ddc339069aeddd25b5675aa1311ad4f4a1aa7401ee593a15507512b`
- `WINDOWS_AND_STREAMLIT_CLOUD_COMMANDS_20260620.md` — audit/report/inventory deliverable — 2,058 bytes — `83e57e2768e06647dd3fd6c426d985a54887748f2472612153e7907b0b85a69a`
- `core/history_columnar_archive_20260620.py` — threshold-gated reversible Parquet/DuckDB archive path — 5,265 bytes — `83f7c47b8a7f0ae8cdb03a739605fb2fa125021a3e7595e085f457f025f969f3`
- `core/history_evidence_store_20260620.py` — 35-table atomic projected history store — 17,346 bytes — `82e93b4b6cb362e117457abe35dc4e3805f100f7cbe909aeb393c24e1265e6fe`
- `core/history_identity_20260620.py` — common history identity and event-time validation — 4,608 bytes — `412952ad6471066063b04d0e1c902efdb55767db3f677d42d8eaa6b8fe5646ee`
- `core/history_research_pipeline_20260620.py` — completed-H1 evidence transaction preserving protected outputs — 27,508 bytes — `5366f026bcded2fee3492e5851ed38d3324e58c819a813cc041510495503e6d1`
- `core/research_evidence_algorithms_20260620.py` — TinyLFU, M4, Matrix Profile, PELT, CQR, MinT and DM implementations — 18,276 bytes — `e50a84349d5908059dd0c0704f5c32fc76ad88f15913e8fc6a712952b962cca2`
- `core/tinylfu_runtime_cache_20260620.py` — bounded reusable display cache — 1,259 bytes — `d7ef76f9e0356e3a5da4536ff98e06ebcb2649c67c2b41b7e48654a0a7d6088b`
- `data/canonical_runtime.sqlite3.before_history_20260620.bak` — byte-exact original canonical database rollback copy — 81,920 bytes — `bbf0c0288ccce3026b60d3b4185b8e9ad167edfee9deaf2b7b1846f94f04b7f7`
- `tests/test_history_performance_research_20260620.py` — new acceptance and protection suite — 10,313 bytes — `a4a81bee00441f050052fe4e213587bfc2b440c46fe77bcf524db47de5641e54`
- `tools/benchmark_history_performance_20260620.py` — controlled workload benchmark — 12,012 bytes — `53746951c75f02268f8907c5d1a00ed216b323f6a4f100430e9003be21298010`
- `tools/migrate_history_evidence_20260620.py` — idempotent additive schema migration — 1,293 bytes — `bff22d2b1fa71ca27b221371e94f9a244bc7fb952324575f11ecb5909cbf2d58`
- `tools/rollback_history_evidence_20260620.py` — audit/report/inventory deliverable — 2,077 bytes — `78b26b00261ef6d0f90470923eafcacb9942d048855a0ba22ee7f9f8cfa3801e`
- `ui/history_evidence_browser_20260620.py` — bounded phone/desktop projected evidence browser and explicit export — 3,441 bytes — `e9bf07a1019246da8858346a593c9605f505a769bfee397eb9cf05f716cc073a`

## Deleted files

None.

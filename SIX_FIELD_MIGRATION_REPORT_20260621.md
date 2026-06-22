# Six-Field Lunch Migration Report

## Before

The authoritative renderer exposed four principal fields. Dinner/Combined content, Similar-Day content, the assistant, and export/readiness behavior were nested under Field 4, while `render_lunch_six_core_fields()` redirected to the four-field implementation.

## After

`render_lunch_six_core_fields()` owns exactly six top-level Lunch toggles in the required order and with the exact requested labels. The compatibility function `render_lunch_four_core_fields()` points to the six-field implementation so older callers do not fail.

### Field 1

Reads the current canonical cards, current Full Metric tables, protected ten decision tables, Decision 11, current priority/ranking, position sizing, 25-day histories, evidence browser, and unified copy controls.

### Field 2

Reads the published cached Power BI renderer and evidence only. Opening the field does not recalculate the projection.

### Field 3

Reads bounded 25-day regime history, lower/medium/higher standard tables, lifecycle, alpha/delta, reliability, conflict/transition trust, and evidence. Query projection is pushed into the history query.

### Field 4

Is now a genuine principal Dinner Full Combined Intelligence workspace. It lazily selects one existing read-only view at a time: combined regime logic, Power BI regime projection, original/advanced data, priority/reliability, KNN/Greedy, Similar-Day/pattern intelligence, or all current data. No calculation is duplicated.

### Field 5

Is now a genuine principal Grounded AI Assistant field. It is imported only when open and runs retrieval/planning only after submit.

### Field 6

Is a new display-only readiness workspace. It aggregates existing published data into Data, Calculation, Decision, Risk, Evidence/Limitations, and Final Checklist sections. It cannot create or overwrite BUY/SELL/WAIT.

## Lazy execution evidence

Acceptance tests assert exactly six labels, no Field 5/6 nesting under Field 4, no cross-field calculation, no heavy module import for closed gates, no Settings-orchestrator call from toggles, phone-safe state persistence, and bounded history ordering.

## Compatibility boundary

Deprecated `_render_workspace_4a` and `_render_workspace_4b` aliases remain solely for older import/static contracts. Both point only to Field 4 combined content and contain no AI or readiness nesting.

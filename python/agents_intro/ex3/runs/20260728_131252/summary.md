# Ex3 Aggregate Review Report

Generated: `2026-07-28 13:22:20 UTC`

## Headline metrics

- Trials: **5**
- Bugs per trial (x): **12**
- Generator model: `llama3`
- Reviewer model: `llama3.1`
- Precision: **0.9333 ± 0.0913**
- Recall: **0.4167 ± 0.2826**
- F1: **0.5219 ± 0.2595**
- Totals: TP=25, FP=3, FN=35, planted=60, findings=28

## Per-trial table

| Trial | Topic | TP | FP | FN | Precision | Recall | F1 | Latency (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| trial_01 | Order Processing | 5 | 1 | 7 | 0.83 | 0.42 | 0.56 | 108.1 |
| trial_02 | Order Processing and Inventory Managemen | 1 | 0 | 11 | 1.00 | 0.08 | 0.15 | 56.9 |
| trial_03 | Inventory Manager | 3 | 0 | 9 | 1.00 | 0.25 | 0.40 | 60.7 |
| trial_04 | Order Processing Utility | 10 | 2 | 2 | 0.83 | 0.83 | 0.83 | 144.1 |
| trial_05 | Order Processing | 6 | 0 | 6 | 1.00 | 0.50 | 0.67 | 198.5 |

## Category recall (aggregate)

| Category | Planted | TP | Recall |
|---|---:|---:|---:|
| api_design | 5 | 3 | 0.60 |
| edge_case | 11 | 4 | 0.36 |
| logic | 21 | 11 | 0.52 |
| maintainability | 3 | 1 | 0.33 |
| performance | 9 | 3 | 0.33 |
| security | 11 | 3 | 0.27 |

## Top misses (FN)

- `trial_01` / `B1` [logic]: Incorrect quantity update
- `trial_01` / `B3` [security]: Missing input validation
- `trial_01` / `B5` [logic]: Incorrect total calculation
- `trial_01` / `B6` [edge_case]: Incorrect order status for delayed orders
- `trial_01` / `B8` [performance]: Inefficient iteration in update_order_status
- `trial_01` / `B10` [edge_case]: Incorrect order status for backordered orders
- `trial_01` / `B11` [security]: Missing input validation in update_inventory
- `trial_02` / `B1` [logic]: Invalid order format not handled
- `trial_02` / `B3` [logic]: Invalid quantity not handled
- `trial_02` / `B4` [logic]: Not enough stock for product
- `trial_02` / `B5` [edge_case]: Order with no products
- `trial_02` / `B6` [edge_case]: Order with unknown product

## Top false alarms (FP)

- `trial_01` / `F6` [maintainability]: Hardcoded index access in `OrderAPI` class
- `trial_04` / `F7` [logic]: Incorrect details message
- `trial_04` / `F8` [logic]: Incorrect price calculation

## Config

- prompt_version: `v1`
- match_threshold: `0.55`
- output_dir: `runs/`

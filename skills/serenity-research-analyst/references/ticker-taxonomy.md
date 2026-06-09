# Ticker Taxonomy

Use this reference to keep symbol interpretation disciplined.

## Proxy Symbols

- `SIVE` is priced with `SIVEF` in the free-data workflow.
- `SOI` may use a US/OTC proxy such as `SLOIF` depending on data availability.
- Proxy symbols are useful for public/free research, but they are not perfect primary-listing backtests.

## Target Roles

Only focal beneficiaries should be considered possible direct signals. Downgrade these roles:

- customer;
- peer;
- comparison context;
- supply-chain context;
- broad index-like exposure.

A customer ticker can validate demand without being the best beneficiary.

## Industry Nodes

Common AI/semi nodes include:

- AI networking and optics;
- AI compute;
- memory / HBM / storage;
- semiconductor manufacturing;
- internet platforms;
- power / thermal / infrastructure.

Do not infer too much from broad nodes. A weak parent theme can contain a strong bottleneck, and `industry_node=unclear` may mean the taxonomy needs improvement.

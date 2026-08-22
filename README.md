# FedCampaign-EMHI

FedCampaign-EMHI implements Exclusion-Matched Hierarchical Innovation for Operational Distributed Insufficiency. The scientific and execution contract is the repository copy of the roadmap at `docs/Roadmap.md`.

## Environment

Python 3.13+ and `uv` are required.

```bash
uv sync --extra dev
uv run fedcampaign doctor
```

The production scientific configuration is `configs/fedcampaign-emhi.yaml`. `configs/tests.yml` and `configs/smoke.yml` are reduced non-production configurations and cannot replace the claim-bearing production configuration.

Raw datasets are immutable and must appear under the configured `data/raw` symlink.

## Public CLI

The only public executable is `fedcampaign`:

```bash
fedcampaign doctor
fedcampaign preprocess
fedcampaign preprocess <dataset-name>
fedcampaign preprocess --overwrite
fedcampaign preprocess <dataset-name> --overwrite
fedcampaign plan
fedcampaign smoke
fedcampaign smoke --overwrite
fedcampaign run <experiment-name>
fedcampaign run <experiment-name> --overwrite
fedcampaign status
fedcampaign status <experiment-name>
fedcampaign report
fedcampaign report <experiment-name>
fedcampaign report <experiment-name> --overwrite
```

The CLI exposes execution controls only. It does not accept seed, method, coalition-order, basis, context, threshold, PFA, statistical, sensitivity, run-id, or lifecycle-step overrides.

## Development

```bash
make format
make lint
make typecheck
make test
make quality
```

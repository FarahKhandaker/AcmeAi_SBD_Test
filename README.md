## Usage

Ensure a valid `config.yaml` exists (copy from `config.example.yaml` and edit),
then run:

```bash
python run.py
```

For local development, generate a synthetic video feed first:

```bash
python run.py --generate-video
```

Point at a different config file:

```bash
python run.py --config path/to/other.yaml ##Add the actual yaml file here
```

Exit codes:
- `0` — success
- `2` — configuration error
- `3` — pipeline or detector failure
- `4` — reporter failure (reserved for a later commit)
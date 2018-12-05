# ReadMe

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

```bash
cp config_example.ini config.ini
```

## Usage

### Crawler

1. PTT Article

```bash
python -m crawler article (--start-date | --index START_INDEX END_INDEX) [--config-path CONFIG_PATH]
```

2. PTT User last login record

```bash
python -m crawler user (--database | --ip IP) [--config-path CONFIG_PATH]
```

3. PTT Ip autonomous system number

```bash
python -m crawler asn (--database | --id ID) [--config-path CONFIG_PATH]
```

### Export

```bash
python export.py --format {ods, csv} --output-folder OUTPUT_FOLDER [--output-prefix OUTPUT_PREFIX]
```

### Schedule

1. Update

```bash
python schedule.py update {article, asn, user} -c CYCLE_TIME [-s START_DATETIME]
```

2. Remove

```bash
python schedule.py remove {article, asn, user}
```
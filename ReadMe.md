ReadMe
====

## Introduction

---

## Usage


```bash
python main.py crawler article (--start-date | --index START_INDEX END_INDEX) [--config-path CONFIG_PATH]

python main.py crawler asn (--database | --id ID) [--config-path CONFIG_PATH]

python main.py crawler user (--database | --ip IP) [--config-path CONFIG_PATH]

python main.py export --format {ods, csv} --output-folder OUTPUT_FOLDER [--output-prefix OUTPUT_PREFIX]
```

### PttArticleCrawler

```bash
user.py [-h] (--start-date | --index START_INDEX END_INDEX) [--config-path CONFIG_PATH]
```

### PttUserCrawler

```bash
user.py [-h] (--database | --id-list ID_LIST) [--config-path CONFIG_PATH]
```

### PttIpAsnCrawler

```bash
asn.py [-h] (--database | --ip-list IP_LIST) [--config-path CONFIG_PATH]
```

---

## 檔案結構

```
PttCrawler/
|- utils.py
|- main.py
|- config_example.ini
|- models/
|   |- __init__.py
|   |- base.py
|   |- article.py
|   |- asn.py
|   `- user.py
|- crawler/
|   |- __init__.py
|   |- article.py
|   |- asn.py
|   |- user.py
|- webdriver/
|   |- windows/
|   |   `- chromedriver.exe
|   |- linux/
|   |   `- chromedriver
|   `- mac/
|       `- chromedriver
|- requirements.txt
`- ReadMe.md
```

---

## Dependency

```bash
pip install -r requirements.txt
```

## Todo

1. 文章爬蟲被PTT擋連線
    * 可能是`requests`套件不含一般瀏覽器的cookie
    考慮用selenuim解決，實際效果待測試
2. 執行速度緩慢
    * 要找適合的delaytime
3. 匯出
    - [ ] csv
    - [ ] ods
4. 排程
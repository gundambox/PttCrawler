ReadMe
====

## 檔案結構

```
PttCrawler/
|- crawler/
|   |- article.py
|   |- user.py
|   |- models.py
|   |- utils.py
|   |- config_example.ini
|   `- webdriver/
|       |- windows/
|       |   `- chromedriver.exe
|       |- linux/
|       |   `- chromedriver
|       `- mac/
|           `- chromedriver
|- requirements.txt
`- ReadMe.md
```

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
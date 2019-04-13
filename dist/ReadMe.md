# ReadMe

## 操作步驟

### Windows

1. 修改 config.ini (可跳過)

可修改設定參數，第一次不設定可直接跳過

2. 初始化 DB

    ```bash
    init_db.exe
    ```

3. Crawler

    1. PTT 文章索引爬蟲

        從WebPtt爬取文章索引

        * --board-name
            - 看板名稱
        * --before, --after
            - 預設為before
            - before是往舊索引爬取
            - after是往新索引爬取
        * --index 
            - 若前面設定為before, 預設為DB中最舊的索引
            - 若前面設定為after, 預設為DB中最新的索引
            - 若DB無資料, 預設到該看板抓取最新的索引

        ```bash
        crawler.exe article_index --board-name BOARD_NAME \
            [--before | --after] [--index INDEX]                 
        ```

    2. PTT 文章爬蟲

        從WebPtt爬取文章

        * --board-name
            - 看板名稱
        * --start-date, --index, --database
            - --start-date: 從最新文章往前爬取到特定時間的文章
            - --index: 爬取從START_INDEX到END_INDEX之間的文章
            - --database: 爬取DB中有紀錄索引的文章
        * --add, --upgrade
            - --add 會跳過存在的舊文章, 不新增文章歷史紀錄
            - --upgrade 每個文章都會新增一個歷史紀錄

        ```bash
        crawler.exe article --board-name BOARD_NAME \
            (--start-date | --index START_INDEX END_INDEX | --database) \
            (--add | --upgrade) \
            [--config-path CONFIG_PATH]
        ```

    3. PTT 鄉民上站紀錄爬蟲

        利用term.ptt.cc爬取上站紀錄、登入次數、有效文章

        ```bash
        crawler.exe user (--database | --id ID) [--config-path CONFIG_PATH]
        ```

    4. PTT 查Ip Autonomous System Number

        查Ip的ASN(主要查Country code)

        ```bash
        crawler.exe asn (--database | --ip IP) [--config-path CONFIG_PATH]
        ```

4. Export

    匯出成ods, csv或json

    ```bash
    export.exe --format {ods, csv json} --output-folder OUTPUT_FOLDER [--output-prefix OUTPUT_PREFIX]
    ```

5. Schedule

目前這功能在windows上找不到適合的套件，只能手動設定工作排程器

### Linux

1. 修改 config.ini (可跳過)

可修改設定參數，第一次不設定可直接跳過

2. 初始化 DB

    ```bash
    ./init_db
    ```

3. Crawler

    1. PTT 文章索引爬蟲

        從WebPtt爬取文章索引

        * --board-name
            - 看板名稱
        * --before, --after
            - 預設為before
            - before是往舊索引爬取
            - after是往新索引爬取
        * --index 
            - 若前面設定為before, 預設為DB中最舊的索引
            - 若前面設定為after, 預設為DB中最新的索引
            - 若DB無資料, 預設到該看板抓取最新的索引

        ```bash
        ./crawler article_index --board-name BOARD_NAME \
            [--before | --after] [--index INDEX]                 
        ```

    2. PTT 文章爬蟲

        從WebPtt爬取文章

        * --board-name
            - 看板名稱
        * --start-date, --index, --database
            - --start-date: 從最新文章往前爬取到特定時間的文章
            - --index: 爬取從START_INDEX到END_INDEX之間的文章
            - --database: 爬取DB中有紀錄索引的文章
        * --add, --upgrade
            - --add 會跳過存在的舊文章, 不新增文章歷史紀錄
            - --upgrade 每個文章都會新增一個歷史紀錄

        ```bash
        ./crawler article --board-name BOARD_NAME \
            (--start-date | --index START_INDEX END_INDEX | --database) \
            (--add | --upgrade) \
            [--config-path CONFIG_PATH]
        ```

    3. PTT 鄉民上站紀錄爬蟲

        利用term.ptt.cc爬取上站紀錄、登入次數、有效文章

        ```bash
        ./crawler user (--database | --id ID) [--config-path CONFIG_PATH]
        ```

    4. PTT 查Ip Autonomous System Number

        查Ip的ASN(主要查Country code)

        ```bash
        ./crawler asn (--database | --ip IP) [--config-path CONFIG_PATH]
        ```

4. Export

    匯出成ods, csv或json

    ```bash
    ./export --format {ods, csv json} --output-folder OUTPUT_FOLDER [--output-prefix OUTPUT_PREFIX]
    ```

5. Schedule

    1. Update

        * --args
            - crawler的參數
            - 例如: `python schedule.py update article_index --args "--board-name Gossiping" -c 1`
        * -c
            * 循環天數間隔

        ```bash
        ./schedule update {article_index, article, asn, user} \
            --args ARGS
            -c CYCLE_TIME [-s START_DATETIME] [--virtualenv VIRTUALENV_PATH]
        ```

    2. Remove

        * --args
            - crawler的參數
            - 例如: `python schedule.py remove article_index --args "--board-name GUNDAM"`

        ```bash
        ./schedule remove {article_index, article, asn, user} --args ARGS
        ```
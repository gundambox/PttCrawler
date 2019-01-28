# ChangeLog

## [Unrelease]

## [1.0.2] 2019-01-28
### Added
- start to use database migration
- use article_index crawler to fetch the ptt article index and article web_id
- add new argument in article crawler to fetch ptt article
- article_history rotation
- add pyinstaller to bundle script into executable
### Fixed
- schedule.py bug
- crawler.py bug

## [1.0.1] 2018-12-24
### Chanaged
- 讓排程支援virtualenv
- adjust doc and README
- Bypass Cloudflare

## [1.0.0] 2018-12-07
### Added
- 爬蟲
    * 文章
    * 使用者上站紀錄
- Ip_Asn查詢
- 匯出(ods, csv)
- 排程
- 查詢看板IP來源
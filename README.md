# smart-scraper
google drive scraper to download data from smart project:
https://www.smartmagnet.net/data

## Prerequisties
- Poetry: this project uses Poetry for dependency management
- client_secret.json: with your Google API key

## Run
1. Clone the project:
   
    `git clone https://github.com/jiashuwu89/smart-scraper.git`

    `cd smart-scraper`

2. Install Dependencies with Poetry:
   
    `poetry install`

3. How to run:

    Choose a station, option: 'CCNV', 'PTRS', 'RMUS', 'HRIS', 'SWNO', 'PLMR' and then provide a date range. 
   

    `poetry run python SmartScraper.py CCNV between 2023-02-01 2023-02-05`

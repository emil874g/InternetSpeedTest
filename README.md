# Office Internet Speed Tracker

Automated internet speed logging and analysis tool using Docker.

## Setup
1. Ensure **Docker Desktop** is installed and running.
2. Open a terminal in this folder and run:
   `docker-compose up -d --build`

The logger will now run 24/7 in the background. It tests 4 times at the start of every hour.

## Generating Charts
To generate the latest boxplot charts (saved to the `/charts` folder), run:
`docker-compose exec speedtest python clean_data.py`
`docker-compose exec speedtest python analyze_data.py`

## Viewing Logs
To see what the logger is doing right now, run:
`docker logs -f speedtest_office`

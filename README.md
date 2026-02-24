# Office Internet Speed Tracker

Automated internet speed logging and analysis tool using Docker. This is designed to test internet connections 24/7, but specifically for offices during the timeframe of 8-16.
This only logs data locally on your machine. However the code can be modified to log it directly to any cloud solution, you may want.

## Setup
1. Ensure **Docker Desktop** is installed and running.
2. Open a terminal in this folder and run:
   `docker-compose up -d --build`

The logger will now run 24/7 in the background. It tests 4 times at the start of every hour.

## Generating Charts
To generate the latest boxplot charts (saved to the `/charts` folder), run:
docker-compose exec speedtest python scripts/clean_data.py
docker-compose exec speedtest python scripts/analyze_speeds.py

## Viewing Logs
To see what the logger is doing right now, run:
`docker logs -f speedtest_office`


## Native Windows
Native Windows (Currently Active on Lenovo desktop in the office)
Because the office Lenovo desktop does not support hardware virtualization (BIOS locked), the logger runs natively via a hidden Windows VBScript.

Install Prerequisites:

Install Python 3.10+ (Ensure "Add Python to PATH" is checked).

Download the Ookla Speedtest CLI for Windows. Extract speedtest.exe and place it directly into the src/scripts/ folder.

Install dependencies: pip install pandas plotly pyarrow

Start the Logger:

Double-click start_logger.vbs. The logger will start running invisibly in the background.

(Note: The path inside start_logger.vbs is hardcoded to C:\Users\arh\Code\InternetSpeedTest\InternetSpeedTest\src\scripts\logger.py for this specific machine. Update it if the project folder is moved!)

Auto-Start on Reboot:

Press Win + R, type shell:startup, and press Enter.

Place a shortcut to start_logger.vbs in this folder so it runs automatically when Windows starts.

In order to run the scripts on windows for creating charts and cleaning the data simply run:
python src\scripts\clean_data.py
python src\scripts\analyze_speeds.py


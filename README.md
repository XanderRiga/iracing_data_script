# Top Drivers By Region

## What is this?
This is a python script that will create a CSV of the top 10 race results for drivers
from the given Club ID.

The club being searched, season quarter, season week are all configurable as well 
as the amount of results(e.g. top 20 instead of top 10)

## How do I use it
- Clone the repo
- Make sure you have pipenv installed(pip install pipenv)
- From inside the repo, run `pipenv install` to install dependencies
- From inside the repo, clone pyracing: https://github.com/Esterni/pyracing
- Navigate into the `pyracing` directory and run `pip install .`
- Create a .env file, run `touch .env` from the root of the repo
- inside the new file called `.env` add `IRACING_USERNAME=MY USERNAME` and `IRACING_PASSWORD=MY PASSWORD` as lines
  * **NOTE** This will not work if your username and password are not correct
- Make sure your computer won't go to sleep if left alone for a while(because this takes a _while)_
- From the root of the repo, run `python main.py`
- Enjoy!

## Troubleshooting
- Make sure you are inside the pipenv shell when you run 
  anything related to this code, by running `pipenv shell` from inside the repo
- Make sure the shell is active when running the `pip install .` from inside the pyracing directory


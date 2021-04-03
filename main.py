from pyracing import client as pyracing
from pyracing import constants as ct
from pyracing.response_objects import session_data, career_stats, historical_data, iracing_data
import os
import asyncio
import dotenv
import csv
from datetime import datetime
from timeit import default_timer as timer

 # 45 is club ID for brazil
CLUB_ID = 45

# Quarter refers to the quarter of the season you want to search.
# If you want the season that starts in January, use 1
QUARTER = 2

# This is the race week inside the season you want to search for.
# This is 0 index, so the first race week is 0, 2nd race week is 1, etc
RACE_WEEK = 2

# Change this to change the amount of results that are output into the CSV
# By default this gives top 10 for road and oval
TOP_N_RESULTS = 10

dotenv.load_dotenv()


async def main():
  start = timer()
  client = await login()

  driver_ids = await drivers_from_club(client)

  road_results_list = await road_results(client, driver_ids)
  top_n_road = top_n_from_results(TOP_N_RESULTS, road_results_list)
  road_subsession_results = await event_results_to_subsession_results(client, top_n_road)
  road_complete_time = datetime.now()
  road_csv_name = f'top_road_{road_complete_time}.csv'
  build_csv(road_csv_name, road_subsession_results)
  print(f'Road CSV Built at: {road_csv_name}')

  oval_results_list = await oval_results(client, driver_ids)
  top_n_oval = top_n_from_results(TOP_N_RESULTS, oval_results_list)
  oval_subsession_results = await event_results_to_subsession_results(client, top_n_oval)
  oval_complete_time = datetime.now()
  oval_csv_name = f'top_oval_{oval_complete_time}.csv'
  build_csv(oval_csv_name, oval_subsession_results)
  print(f'Oval CSV Built at: {oval_csv_name}')

  end = timer()
  print(f'Finished! Script took {end - start} seconds to complete')


def build_csv(file_name, subsession_result_list):
  with open(file_name, mode='w') as file:
    writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Name', 'Start Date', 'Champ Points', 'Club Points',
                          'Start Position', 'Finish Position', 'SoF', 'Series', 'iRating Gain'])

    for subsession_result in subsession_result_list:
      writer.writerow([subsession_result.event_result.display_name,
                       subsession_result.event_result.date_start,
                       subsession_result.event_result.points_champ,
                       subsession_result.event_result.points_club,
                       subsession_result.event_result.pos_start,
                       subsession_result.event_result.pos_finish,
                       subsession_result.event_result.strength_of_field,
                       subsession_result.series_name,
                       subsession_result.irating_gain])


def top_n_from_results(n, results):
  results.sort(key=lambda result: result.points_champ, reverse=True)
  return results[0:n]


async def event_results_to_subsession_results(client, event_results):
  """This takes a list of event results, and returns a list of Results containing extra subsession data"""
  results = []
  for event_result in event_results:
    try:
      subsession_data = await client.subsession_data(event_result.subsession_id)

      driver = driver_from_subsession_by_cust_id(subsession_data, event_result.cust_id)
      if driver:
        irating = driver.irating_new - driver.irating_old
      else:
        irating = None

      results.append(SubsessionResult(event_result, subsession_data.series_name_short, irating))
    except:
      results.append(SubsessionResult(event_result, None, None))

  return results


async def road_results(client, cust_ids):
  return await weekly_results(client, cust_ids, ct.Category.road)


async def oval_results(client, cust_ids):
  return await weekly_results(client, cust_ids, ct.Category.oval)


async def weekly_results(client, cust_ids, category):
  """Returns dict of key: cust_id, value: list of event results objects.
  This data is for all of this cust_ids races in that race week unless it goes over the max limit"""
  all_results = []
  for cust_id in cust_ids:
    # All race results for given race week for this user
    race_results = await results_from_cust_id(client, cust_id, category.value)
    print(f'Got {category.name} results for {cust_id}')
    all_results.extend(race_results)

  print(f'Gathered all results for all drivers for category: {category.name}')
  return all_results


async def results_from_cust_id(client, cust_id, category):
  try:
    return await client.event_results(
      cust_id,
      QUARTER,
      result_num_high=100,
      race_week=RACE_WEEK,
      category=category,
      sort=ct.Sort.champ_points.value,
      order=ct.Sort.descending.value
    )
  except:
    return []


async def drivers_from_club(client):
  """Get as many unique driver ids as we can from a club.
  We will likely only see the top few since its sorted by most champ pts"""
  driver_ids = []
  for season in await all_seasons(client):
    try:
      standings = await client.season_standings(
          season.season_id,
          club_id=CLUB_ID,
          race_week=-1,
          result_num_high=100
      )
    except:
      print(f'No drivers found for series: {season.series_name_short}')
      continue

    print(f'Found {len(standings)} drivers from club in series: {season.series_name_short}')

    for standing in standings:
      driver_ids.append(standing.cust_id)

  print(f'Gathered {len(driver_ids)} total drivers from club')
  # Remove duplicates
  return list(set(driver_ids))


async def all_seasons(client):
  return await client.current_seasons()


def driver_from_subsession_by_cust_id(subsession_data, cust_id):
  for driver in subsession_data.drivers:
    if driver.cust_id == cust_id:
      return driver

  return None


async def login():
  client = pyracing.Client(
    os.getenv("IRACING_USERNAME"),
    os.getenv("IRACING_PASSWORD")
  )
  return client


class SubsessionResult:
  def __init__(self, event_result, series_name, irating_gain):
    self.event_result = event_result
    self.series_name = series_name
    self.irating_gain = irating_gain


asyncio.run(main())

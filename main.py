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
  top_10_road = top_n_from_results(TOP_N_RESULTS, road_results_list)
  road_complete_time = datetime.now()
  build_csv(f'top_road_{road_complete_time}.csv', top_10_road)

  oval_results_list = await oval_results(client, driver_ids)
  top_10_oval = top_n_from_results(TOP_N_RESULTS, oval_results_list)
  oval_complete_time = datetime.now()
  build_csv(f'top_oval_{oval_complete_time}.csv', top_10_oval)

  end = timer()
  print(f'Finished! Script took {end - start} seconds to complete')

def build_csv(file_name, event_result_list):
  with open(file_name, mode='w') as file:
    writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Name', 'Start Date', 'Champ Points', 'Club Points',
                          'Start Position', 'Finish Position', 'SoF'])

    for event_result in event_result_list:
      writer.writerow([event_result.display_name, event_result.date_start,
                            event_result.points_champ, event_result.points_club,
                            event_result.pos_start, event_result.pos_finish,
                            event_result.strength_of_field])


def top_n_from_results(n, results):
  results.sort(key=lambda result: result.points_champ, reverse=True)
  return results[0:n]


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
    # data = await client.subsession_data(race.subsession_id)

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


async def login():
  client = pyracing.Client(
    os.getenv("IRACING_USERNAME"),
    os.getenv("IRACING_PASSWORD")
  )
  return client


asyncio.run(main())

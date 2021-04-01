from pyracing import client as pyracing
from pyracing import constants as ct
from pyracing.response_objects import session_data, career_stats, historical_data, iracing_data
import os
import asyncio
import dotenv
import csv
from datetime import datetime
from timeit import default_timer as timer


CLUB_ID = 45
QUARTER = 2
RACE_WEEK = 2
dotenv.load_dotenv()


async def main():
  start = timer()
  client = await login()

  driver_ids = await drivers_from_club(client)
  road_results_list = await road_results(client, driver_ids)
  oval_results_list = await oval_results(client, driver_ids)

  top_10_road = top_n_from_results(10, road_results_list)
  top_10_oval = top_n_from_results(10, oval_results_list)

  now = datetime.now()
  build_csv(f'top_road_{now}.csv', top_10_road)
  build_csv(f'top_oval_{now}.csv', top_10_oval)
  end = timer()
  print(f'Finished! Script took {end - start} seconds to complete')

def build_csv(file_name: str, event_result_list: list[historical_data.EventResults]):
  with open(file_name, mode='w') as road_file:
    road_writer = csv.writer(road_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    road_writer.writerow(['Name', 'Start Date', 'Champ Points', 'Club Points',
                          'Start Position', 'Finish Position', 'SoF'])

    for event_result in event_result_list:
      road_writer.writerow([event_result.display_name, event_result.date_start,
                            event_result.points_champ, event_result.points_club,
                            event_result.pos_start, event_result.pos_finish,
                            event_result.strength_of_field])


def top_n_from_results(n: int, results: list[historical_data.EventResults]) -> list[historical_data.EventResults]:
  results.sort(key=lambda result: result.points_champ, reverse=True)
  return results[0:n]


async def road_results(client: pyracing, cust_ids: list[int]) -> list[historical_data.EventResults]:
  return await weekly_results(client, cust_ids, ct.Category.road)


async def oval_results(client: pyracing, cust_ids: list[int]) -> list[historical_data.EventResults]:
  return await weekly_results(client, cust_ids, ct.Category.oval)


async def weekly_results(client: pyracing, cust_ids: list[int], category: ct.Category) -> list[historical_data.EventResults]:
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


async def results_from_cust_id(client: pyracing, cust_id: int, category: ct.Category) -> list[historical_data.EventResults]:
  return await client.event_results(
    cust_id,
    QUARTER,
    result_num_high=100,
    race_week=RACE_WEEK,
    category=category,
    sort=ct.Sort.champ_points.value,
    order=ct.Sort.descending.value
  )


async def drivers_from_club(client: pyracing) -> list[int]:
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


async def all_seasons(client: pyracing) -> list[iracing_data.Season]:
  return await client.current_seasons()


async def login() -> pyracing:
  client = pyracing.Client(
    os.getenv("IRACING_USERNAME"),
    os.getenv("IRACING_PASSWORD")
  )
  return client


asyncio.run(main())

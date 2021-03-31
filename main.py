from pyracing import client as pyracing
from pyracing import constants as ct
from pyracing.response_objects import session_data, career_stats, historical_data, iracing_data
import os
import asyncio
import dotenv


CLUB_ID = 45
SEASON_IDS = [649, 228, 386, 447] # series for testing
QUARTER = 2
RACE_WEEK = 2

dotenv.load_dotenv()


async def main():
  client = await login()

  driver_ids = await drivers_from_club(client)
  road_results_list = await road_results(client, driver_ids)
  oval_results_list = await oval_results(client, driver_ids)

  # TODO use the results lists to find the top of the week


async def road_results(client: pyracing, cust_ids: list[int]) -> dict[int, list[session_data.SubSessionData]]:
  return await weekly_results(client, cust_ids, ct.Category.road)


async def oval_results(client: pyracing, cust_ids: list[int]) -> dict[int, list[session_data.SubSessionData]]:
  return await weekly_results(client, cust_ids, ct.Category.oval)


async def weekly_results(client: pyracing, cust_ids: list[int], category: ct.Category) -> dict[int, list[session_data.SubSessionData]]:
  """Returns dict of key: cust_id, value: list of subsession data objects.
  This data is for all of this cust_ids races in that race week unless it goes over the max limit"""
  subsession_results = {}
  for cust_id in cust_ids:
    # All race results for given race week for this user
    race_results = await results_from_cust_id(client, cust_id, category.value)
    for race in race_results:
      data = await client.subsession_data(race.subsession_id)
      add_or_append(subsession_results, cust_id, data)

  print(f'Gathered all results for all drivers for category: {category.name}')
  return subsession_results


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
  driver_ids = []
  for season_id in SEASON_IDS:
    standings = await client.season_standings(
        season_id,
        club_id=CLUB_ID,
        race_week=-1,
        result_num_high=-1
    )
    for standing in standings:
      driver_ids.append(standing.cust_id)

  print('Gathered all drivers from club')
  # Remove duplicates
  return list(set(driver_ids))


def add_or_append(dict: dict, key: any, item: any) -> None:
  """Add list to value of dict[key] or create it as list if it doesn't exist"""
  if key in dict:
    dict[key] = dict[key].append(item)
  else:
    dict[key] = [item]


async def login() -> pyracing:
  client = pyracing.Client(
    os.getenv("IRACING_USERNAME"),
    os.getenv("IRACING_PASSWORD")
  )
  return client


asyncio.run(main())

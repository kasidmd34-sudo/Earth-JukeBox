"""Download sample NASA POWER dataset locally."""
import asyncio
import json
import os
import sys

# Ensure repository root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.data.nasa_power import NASAPowerAdapter


async def main():
    print("Fetching NASA POWER sample data for Mumbai...")
    data = await NASAPowerAdapter.fetch_monthly_climatology(
        19.0760, 72.8777, 2018, 2023, ["T2M", "PRECTOTCORR", "WS10M"]
    )
    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/mumbai_sample.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Saved to data/raw/mumbai_sample.json")


if __name__ == "__main__":
    asyncio.run(main())

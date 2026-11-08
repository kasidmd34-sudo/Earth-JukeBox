"""CLI utility to query and verify NASA CMR datasets."""
import asyncio
import os
import sys

# Ensure repository root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.data.nasa_cmr import NASACMRClient


async def main():
    print("Searching NASA CMR for MOD13A2 (Vegetation)...")
    granules = await NASACMRClient.discover_granules("MOD13A2", "-10,10,10,20", "2023-01-01", "2023-02-01", 3)
    print(f"Found {len(granules)} granules.")
    for g in granules:
        print(f" - {g.get('title')}")


if __name__ == "__main__":
    asyncio.run(main())

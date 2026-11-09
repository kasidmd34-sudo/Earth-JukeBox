import asyncio

from app.reports.summary_generator import generate_ai_summary


async def main():
    sample_context = {
        "condition": "temperature",
        "location": {
            "latitude": 19.0760,
            "longitude": 72.8777,
        },
        "date_range": {
            "start": "2020-01-01",
            "end": "2025-12-31",
        },
        "unit": "degrees_Celsius",
        "sample_count": 6,
        "statistics": {
            "mean": 28.5,
            "min": 24.1,
            "max": 33.2,
            "std": 2.4,
        },
        "dataset": {
            "organization": "NASA",
            "dataset_name": (
                "NASA POWER Monthly Climate Surface Temperatures"
            ),
            "dataset_identifier": "POWER_MONTHLY_T2M",
        },
        "limitations": [
            "Gridded monthly data, not a local weather-station reading."
        ],
    }

    result = await generate_ai_summary(sample_context)

    print("\n--- GENERATED REPORT SUMMARY ---")
    print("Summary:", result["summary"])
    print("\nKey findings:")
    for finding in result["key_findings"]:
        print("-", finding)

    print("\nLimitations:")
    for limitation in result["limitations"]:
        print("-", limitation)

    print("\nGeneration method:", result["generation_method"])


if __name__ == "__main__":
    asyncio.run(main())
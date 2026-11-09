
import asyncio
import json

from app.reports.report_service import ReportService


async def main():
    report = await ReportService.generate_report(
        condition="temperature",
        latitude=19.0760,
        longitude=72.8777,
        start_date="2020-01-01",
        end_date="2025-12-31",
    )

    print("\n========== REPORT TEST ==========")

    print("\nCondition:", report["condition"])
    print("Unit:", report["unit"])

    print("\nStatistics:")
    print(json.dumps(report["statistics"], indent=4))

    print("\nNASA Data Source:")
    print(json.dumps(report["data_source"], indent=4))

    print("\nObservation Count:")
    print(report["report_metadata"]["observation_count"])

    print("\nSonification Parameters:")
    print(len(report["sonification"]["parameters"]))

    print("\nAI Summary:")
    print(json.dumps(report["ai_summary"], indent=4))

    print("\nReport service test completed.")


if __name__ == "__main__":
    asyncio.run(main())

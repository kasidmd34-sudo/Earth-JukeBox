
import asyncio
from pathlib import Path

from app.reports.report_service import ReportService
from app.reports.chart_generator import ChartGenerator


async def main():
    report = await ReportService.generate_report(
        condition="temperature",
        latitude=19.0760,
        longitude=72.8777,
        start_date="2020-01-01",
        end_date="2025-12-31",
    )

    charts = ChartGenerator.generate_charts(report)

    output_dir = Path("artifacts/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    for chart_name, chart_buffer in charts.items():
        output_path = output_dir / f"{chart_name}.png"

        with open(output_path, "wb") as file:
            file.write(chart_buffer.getvalue())

        print(f"Generated: {output_path}")

    print("\nChart generation completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())

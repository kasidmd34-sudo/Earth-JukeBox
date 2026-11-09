
import asyncio
from pathlib import Path

from app.reports.report_service import ReportService
from app.reports.chart_generator import ChartGenerator
from app.reports.pdf_generator import PDFGenerator


async def main():
    print("Retrieving NASA observations...")

    report = await ReportService.generate_report(
        condition="temperature",
        latitude=19.0760,
        longitude=72.8777,
        start_date="2020-01-01",
        end_date="2025-12-31",
    )

    print("Generating charts...")

    charts = ChartGenerator.generate_charts(report)

    print("Initializing PDF generator...")

    pdf_generator = PDFGenerator()

    output_dir = Path("artifacts/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    for report_format in ["compact", "detailed"]:
        print(f"\nGenerating {report_format} PDF...")

        pdf_buffer = pdf_generator.generate_pdf(
            report_data=report,
            charts=charts,
            report_format=report_format,
        )

        output_path = output_dir / f"earth_jukebox_{report_format}.pdf"

        with open(output_path, "wb") as file:
            file.write(pdf_buffer.getvalue())

        print(f"Created: {output_path}")
        print(f"File size: {output_path.stat().st_size / 1024:.2f} KB")

    print("\nBoth PDF reports generated successfully.")


if __name__ == "__main__":
    asyncio.run(main())

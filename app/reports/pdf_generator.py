
"""PDF generation engine for Earth Jukebox.

Creates compact and detailed environmental reports using ReportLab.

Features:
- Compact and detailed PDF formats
- NASA dataset provenance
- Descriptive statistics
- Gemini-generated summaries
- Matplotlib charts
- Scientific limitations
- Sonification parameters
- NASA observation records

All environmental data comes from the supplied NASA report context.
No environmental data is retrieved or invented in this module.
"""

from io import BytesIO
import re
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)


class PDFGenerator:
    """Generate compact and detailed Earth Jukebox PDF reports."""

    PAGE_WIDTH, PAGE_HEIGHT = A4

    NAVY = colors.HexColor("#14213D")
    BLUE = colors.HexColor("#2563EB")
    LIGHT_BLUE = colors.HexColor("#EAF2FF")
    LIGHT_GREY = colors.HexColor("#F3F4F6")
    MID_GREY = colors.HexColor("#6B7280")
    DARK_GREY = colors.HexColor("#374151")
    BORDER = colors.HexColor("#D1D5DB")
    WHITE = colors.white

    def __init__(self):
        self.styles = getSampleStyleSheet()

        self.styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=self.styles["Title"],
                fontName="Helvetica-Bold",
                fontSize=23,
                leading=28,
                textColor=self.NAVY,
                alignment=1,
                spaceAfter=8,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="ReportSubtitle",
                parent=self.styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=15,
                textColor=self.MID_GREY,
                alignment=1,
                spaceAfter=14,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SectionHeading",
                parent=self.styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=18,
                textColor=self.NAVY,
                spaceBefore=10,
                spaceAfter=7,
                keepWithNext=True,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SubHeading",
                parent=self.styles["Heading3"],
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=13,
                textColor=self.BLUE,
                spaceBefore=6,
                spaceAfter=4,
                keepWithNext=True,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="BodyCustom",
                parent=self.styles["BodyText"],
                fontName="Helvetica",
                fontSize=9,
                leading=13,
                textColor=self.DARK_GREY,
                spaceAfter=6,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SmallCustom",
                parent=self.styles["BodyText"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=10,
                textColor=self.DARK_GREY,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="TableHeaderCustom",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7.5,
                leading=9,
                textColor=self.WHITE,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="TableCellCustom",
                parent=self.styles["Normal"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=9,
                textColor=self.DARK_GREY,
            )
        )

        # Compact sample styles help keep the explanatory note with the table.
        self.styles.add(
            ParagraphStyle(
                name="SampleTableHeaderCustom",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7,
                leading=8,
                textColor=self.WHITE,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SampleTableCellCustom",
                parent=self.styles["Normal"],
                fontName="Helvetica",
                fontSize=7,
                leading=8,
                textColor=self.DARK_GREY,
            )
        )

    # ---------------------------------------------------------
    # TEXT FORMATTING HELPERS
    # ---------------------------------------------------------

    @staticmethod
    def _safe_text(
        value: Any,
        default: str = "Not available",
    ) -> str:
        if value is None or value == "":
            return default

        return str(value)

    @staticmethod
    def _format_display_text(value: Any) -> str:
        """Format known machine-readable units for human-readable PDF text.

        The underlying report/API data and NASA provenance are not modified.
        """
        text = str(value)
        replacements = {
            "degrees_Celsius": "°C",
            "degree_Celsius": "°C",
            "degrees_Fahrenheit": "°F",
            "degree_Fahrenheit": "°F",
        }
        for source, display in replacements.items():
            text = text.replace(source, display)
        return text

    @staticmethod
    def _escape(value: Any) -> str:
        """Escape data before inserting it into ReportLab markup."""
        text = str(value)
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _paragraph(
        self,
        text: Any,
        style: str = "BodyCustom",
    ) -> Paragraph:
        return Paragraph(
            self._escape(self._format_display_text(text)),
            self.styles[style],
        )

    def _rich_paragraph(
        self,
        text: str,
        style: str = "BodyCustom",
    ) -> Paragraph:
        """Render intentionally constructed, escaped ReportLab markup."""

        return Paragraph(
            self._format_display_text(text),
            self.styles[style],
        )

    def _section(self, title: str) -> Paragraph:
        return Paragraph(
            self._escape(title),
            self.styles["SectionHeading"],
        )

    def _subsection(self, title: str) -> Paragraph:
        return Paragraph(
            self._escape(title),
            self.styles["SubHeading"],
        )

    # ---------------------------------------------------------
    # REPORT HEADER
    # ---------------------------------------------------------

    def _build_header(
        self,
        report: Dict[str, Any],
    ) -> List[Any]:

        condition = report.get("condition", "environmental")
        location = report.get("location", {})
        time_window = report.get("time_window", {})

        story = [
            Spacer(1, 10 * mm),

            Paragraph(
                "EARTH JUKEBOX",
                ParagraphStyle(
                    name="Brand",
                    fontName="Helvetica-Bold",
                    fontSize=10,
                    leading=12,
                    textColor=self.BLUE,
                    alignment=1,
                ),
            ),

            Spacer(1, 4 * mm),

            self._paragraph(
                report.get(
                    "report_title",
                    f"{condition.capitalize()} Environmental Report",
                ),
                "ReportTitle",
            ),

            self._paragraph(
                "NASA Earth Observation Analysis and Scientific Sonification",
                "ReportSubtitle",
            ),
        ]

        summary_rows = [
            [
                self._paragraph("CONDITION", "TableHeaderCustom"),
                self._paragraph("LOCATION", "TableHeaderCustom"),
                self._paragraph("DATE RANGE", "TableHeaderCustom"),
            ],
            [
                self._paragraph(
                    condition.capitalize(),
                    "TableCellCustom",
                ),

                self._rich_paragraph(
                    f"Lat: {self._escape(location.get('latitude', 'N/A'))}<br/>"
                    f"Lon: {self._escape(location.get('longitude', 'N/A'))}",
                    "SmallCustom",
                ),

                self._rich_paragraph(
                    f"{self._escape(time_window.get('start_date', 'N/A'))}<br/>"
                    f"to {self._escape(time_window.get('end_date', 'N/A'))}",
                    "SmallCustom",
                ),
            ],
        ]

        table = Table(
            summary_rows,
            colWidths=[
                45 * mm,
                55 * mm,
                65 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
                    ("BACKGROUND", (0, 1), (-1, 1), self.LIGHT_BLUE),
                    ("BOX", (0, 0), (-1, -1), 0.6, self.BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, self.BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )

        story.extend(
            [
                table,
                Spacer(1, 6 * mm),
            ]
        )

        return story

    # ---------------------------------------------------------
    # STATISTICAL OVERVIEW
    # ---------------------------------------------------------

    def _build_statistics(
        self,
        report: Dict[str, Any],
    ) -> List[Any]:

        statistics = report.get("statistics", {})
        unit = self._safe_text(report.get("unit"), "")

        metrics = [
            ("Observation count", statistics.get("observation_count")),
            ("Mean", statistics.get("mean")),
            ("Median", statistics.get("median")),
            ("Minimum", statistics.get("minimum")),
            ("Maximum", statistics.get("maximum")),
            ("Range", statistics.get("range")),
            ("Standard deviation", statistics.get("standard_deviation")),
            ("First-to-last change", statistics.get("change")),
            (
                "First-to-last percentage change",
                statistics.get("change_percent"),
            ),
        ]

        rows = [
            [
                self._paragraph("Metric", "TableHeaderCustom"),
                self._paragraph("Value", "TableHeaderCustom"),
            ]
        ]

        for label, value in metrics:

            if value is None:
                display_value = "Not available"

            elif label == "Observation count":
                display_value = str(value)

            elif label == "First-to-last percentage change":
                display_value = f"{value}%"

            else:
                display_value = f"{value} {unit}"

            rows.append(
                [
                    self._paragraph(label, "TableCellCustom"),
                    self._paragraph(display_value, "TableCellCustom"),
                ]
            )

        table = Table(
            rows,
            colWidths=[
                75 * mm,
                90 * mm,
            ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [self.WHITE, self.LIGHT_GREY],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.4, self.BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        return [
            self._section("1. Statistical Overview"),
            table,
            Spacer(1, 4 * mm),
        ]

    # ---------------------------------------------------------
    # GEMINI SUMMARY
    # ---------------------------------------------------------

    def _build_ai_summary(
        self,
        report: Dict[str, Any],
    ) -> List[Any]:

        ai_summary = report.get("ai_summary", {}) or {}
        generation_method = str(
            ai_summary.get("generation_method", "unknown")
        ).strip().lower()

        if generation_method == "gemini":
            section_title = "2. AI-Assisted Environmental Interpretation"
        elif generation_method == "statistical_fallback":
            section_title = "2. Statistical Interpretation"
        else:
            section_title = "2. Environmental Interpretation"

        story = [
            self._section(section_title),
            self._paragraph(
                ai_summary.get(
                    "summary",
                    "No summary was generated.",
                )
            ),
        ]

        findings = ai_summary.get("key_findings", [])

        if findings:

            story.append(
                self._subsection("Key Findings")
            )

            for finding in findings:

                story.append(
                    self._paragraph(f"• {finding}")
                )

        story.append(
            self._paragraph(
                "Summary generation method: "
                + self._safe_text(
                    ai_summary.get("generation_method"),
                    "unknown",
                ),
                "SmallCustom",
            )
        )

        return story

    # ---------------------------------------------------------
    # CHARTS
    # ---------------------------------------------------------

    def _build_charts(
        self,
        charts: Optional[Dict[str, BytesIO]],
    ) -> List[Any]:

        story = [
            self._section("3. Environmental Visualizations")
        ]

        if not charts:

            story.append(
                self._paragraph("No charts were supplied.")
            )

            return story

        chart_items = [
            ("observation_chart", "Observation Pattern"),
            ("distribution_chart", "Value Distribution"),
        ]

        for chart_key, chart_title in chart_items:

            chart_buffer = charts.get(chart_key)

            if chart_buffer is None:
                continue

            chart_buffer.seek(0)

            story.append(
                self._subsection(chart_title)
            )

            story.append(
                Image(
                    chart_buffer,
                    width=165 * mm,
                    height=78 * mm,
                    kind="proportional",
                )
            )

            story.append(
                Spacer(1, 3 * mm)
            )

        return story

    # ---------------------------------------------------------
    # NASA DATA PROVENANCE
    # ---------------------------------------------------------

    def _build_provenance(
        self,
        report: Dict[str, Any],
    ) -> List[Any]:

        source = report.get("data_source", {})
        metadata = report.get("report_metadata", {})

        variables = source.get("variables", []) or []
        if isinstance(variables, str):
            variables_display = variables
        else:
            variables_display = ", ".join(str(item) for item in variables)

        fields = [
            ("Organization", source.get("organization")),
            ("Dataset", source.get("dataset_name")),
            ("Dataset identifier", source.get("dataset_identifier")),
            ("Provider DAAC", source.get("provider_daac")),
            ("API endpoint", source.get("api_endpoint")),
            ("Variables", variables_display),
            ("Spatial resolution", source.get("spatial_resolution")),
            ("Temporal resolution", source.get("temporal_resolution")),
            ("Retrieved at", source.get("retrieved_at")),
            ("Access / license", source.get("license_or_access")),
            ("Report generated at", metadata.get("generated_at")),
        ]

        rows = [
            [
                self._paragraph("Metadata", "TableHeaderCustom"),
                self._paragraph("Value", "TableHeaderCustom"),
            ]
        ]

        for label, value in fields:

            rows.append(
                [
                    self._paragraph(label, "TableCellCustom"),
                    self._paragraph(
                        self._safe_text(value),
                        "SmallCustom",
                    ),
                ]
            )

        table = Table(
            rows,
            colWidths=[
                48 * mm,
                117 * mm,
            ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [self.WHITE, self.LIGHT_GREY],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.4, self.BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        return [
            self._section("4. NASA Data Provenance"),
            table,
            Spacer(1, 4 * mm),
        ]

    # ---------------------------------------------------------
    # SCIENTIFIC LIMITATIONS
    # ---------------------------------------------------------

    def _build_limitations(
        self,
        report: Dict[str, Any],
        ) -> List[Any]:
        limitations = report.get("limitations", []) or []

        ai_summary = report.get("ai_summary", {}) or {}
        ai_limitations = ai_summary.get("limitations", []) or []

        combined = []

        def normalise(text: Any) -> str:
            text = str(text).lower()
            text = re.sub(r"[^a-z0-9\s]", " ", text)
            return " ".join(text.split())

        def is_duplicate(candidate: str, existing: str) -> bool:
            candidate_normalised = normalise(candidate)
            existing_normalised = normalise(existing)

            if candidate_normalised == existing_normalised:
                return True

            candidate_words = set(candidate_normalised.split())
            existing_words = set(existing_normalised.split())

            if not candidate_words or not existing_words:
                return False

            overlap = len(candidate_words & existing_words) / len(
                candidate_words | existing_words
            )

            if overlap >= 0.55:
                return True

            # Avoid repeating the same scientific caveat in different words.
            future_terms = {
                "future", "forecast", "predict", "prediction",
                "guarantee", "conditions",
            }

            if (
                "causation" in candidate_words
                and "causation" in existing_words
                and candidate_words.intersection(future_terms)
                and existing_words.intersection(future_terms)
            ):
                return True

            return False

        # Preserve the limitations supplied by the report service.
        for limitation in limitations:
            if not limitation:
                continue

            if not any(
                is_duplicate(str(limitation), existing)
                for existing in combined
            ):
                combined.append(str(limitation))

        # Add AI limitations only when they add new information.
        for limitation in ai_limitations:
            if not limitation:
                continue

            if not any(
                is_duplicate(str(limitation), existing)
                for existing in combined
            ):
                combined.append(str(limitation))

        story = [
            self._section("5. Scientific Limitations and Disclaimer"),
        ]

        if combined:
            for limitation in combined:
                story.append(
                    self._paragraph(f"• {limitation}")
                )
        else:
            story.append(
                self._paragraph(
                    "No additional limitations were provided."
                )
            )

        story.extend([
            Spacer(1, 3 * mm),
            self._paragraph(
                "This document is an analysis of retrieved NASA Earth "
                "observation data. It is not an official NASA forecast, "
                "emergency warning, or substitute for professional "
                "environmental assessment.",
                "SmallCustom",
            ),
        ])

        return story

    # ---------------------------------------------------------
    # SONIFICATION PARAMETERS
    # ---------------------------------------------------------

    def _build_sonification(
        self,
        report: Dict[str, Any],
        detailed: bool,
    ) -> List[Any]:
        sonification = report.get("sonification", {}) or {}
        parameters = sonification.get("parameters", []) or []

        heading = "6. Scientific Sonification Parameters"

        # In compact mode, include the count in the heading so it
        # cannot spill onto a separate page.
        if not detailed and parameters:
            heading += f" ({len(parameters)} mappings)"

        story = [
            self._section(heading),
        ]

        if not sonification:
            story.append(
                self._paragraph(
                    "Sonification parameters are unavailable."
                )
            )
            return story

        summary_items = [
            ("Sound profile", sonification.get("sound_profile")),
            (
                "Mapping description",
                sonification.get("mapping_description"),
            ),
            ("Musical key", sonification.get("musical_key")),
            ("Scale mode", sonification.get("scale_mode")),
            (
                "Dynamic range minimum",
                sonification.get("dynamic_range_min"),
            ),
            (
                "Dynamic range maximum",
                sonification.get("dynamic_range_max"),
            ),
        ]

        # Detailed reports retain the separate count.
        if detailed:
            summary_items.append(
                ("Parameter count", len(parameters))
            )

        for label, value in summary_items:
            display_value = self._safe_text(value)

            story.append(
                Paragraph(
                    f"<b>{self._escape(label)}:</b> "
                    f"{self._escape(display_value)}",
                    self.styles["BodyCustom"],
                )
            )

        if detailed and parameters:
            story.append(
                self._subsection("Sonification Parameter Samples")
            )

            rows = [
                [
                    self._paragraph("Timestamp", "SampleTableHeaderCustom"),
                    self._paragraph("Value", "SampleTableHeaderCustom"),
                    self._paragraph("MIDI", "SampleTableHeaderCustom"),
                    self._paragraph("Note", "SampleTableHeaderCustom"),
                    self._paragraph("Hz", "SampleTableHeaderCustom"),
                    self._paragraph("Tempo", "SampleTableHeaderCustom"),
                ]
            ]

            # Display up to 30 records to keep the PDF readable.
            for item in parameters[:30]:
                rows.append(
                    [
                        self._paragraph(
                            item.get("timestamp", ""),
                            "SampleTableCellCustom",
                        ),
                        self._paragraph(
                            item.get("original_value", ""),
                            "SampleTableCellCustom",
                        ),
                        self._paragraph(
                            item.get("midi_note", ""),
                            "SampleTableCellCustom",
                        ),
                        self._paragraph(
                            item.get("musical_note", ""),
                            "SampleTableCellCustom",
                        ),
                        self._paragraph(
                            item.get("pitch_hz", ""),
                            "SampleTableCellCustom",
                        ),
                        self._paragraph(
                            item.get("tempo_bpm", ""),
                            "SampleTableCellCustom",
                        ),
                    ]
                )

            table = Table(
                rows,
                colWidths=[
                    35 * mm,
                    25 * mm,
                    20 * mm,
                    20 * mm,
                    25 * mm,
                    25 * mm,
                ],
                repeatRows=1,
            )

            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [self.WHITE, self.LIGHT_GREY],
                        ),
                        ("GRID", (0, 0), (-1, -1), 0.35, self.BORDER),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )

            story.extend([
                table,
                Spacer(1, 1.5 * mm),
            ])

            if len(parameters) > 30:
                story.append(
                    self._paragraph(
                        f"Sample display: 30 of {len(parameters)} sonification "
                        "parameter records are shown. The complete parameter "
                        "set is available through the report data/API response.",
                        "SmallCustom",
                    )
                )

        return story
    
    # ---------------------------------------------------------
    # NASA OBSERVATION RECORDS
    # ---------------------------------------------------------

    def _build_observation_table(
        self,
        report: Dict[str, Any],
    ) -> List[Any]:

        observations = report.get("observations", [])

        story = [
            self._section("7. NASA Observation Records")
        ]

        if not observations:

            story.append(
                self._paragraph(
                    "No observation records were returned."
                )
            )

            return story

        rows = [
            [
                self._paragraph("Timestamp", "TableHeaderCustom"),
                self._paragraph("Value", "TableHeaderCustom"),
                self._paragraph("Unit", "TableHeaderCustom"),
            ]
        ]

        for item in observations:

            rows.append(
                [
                    self._paragraph(
                        item.get("timestamp", ""),
                        "TableCellCustom",
                    ),
                    self._paragraph(
                        item.get("value", ""),
                        "TableCellCustom",
                    ),
                    self._paragraph(
                        item.get("unit", ""),
                        "TableCellCustom",
                    ),
                ]
            )

        table = Table(
            rows,
            colWidths=[
                55 * mm,
                45 * mm,
                65 * mm,
            ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [self.WHITE, self.LIGHT_GREY],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.35, self.BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        story.extend(
            [
                table,
                Spacer(1, 4 * mm),
            ]
        )

        return story

    # ---------------------------------------------------------
    # PAGE FOOTER
    # ---------------------------------------------------------

    def _add_page_number(
        self,
        canvas,
        document,
    ):

        canvas.saveState()

        page_number = canvas.getPageNumber()

        canvas.setStrokeColor(self.BORDER)
        canvas.setLineWidth(0.5)

        canvas.line(
            20 * mm,
            15 * mm,
            self.PAGE_WIDTH - 20 * mm,
            15 * mm,
        )

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(self.MID_GREY)

        canvas.drawString(
            20 * mm,
            10 * mm,
            "Earth Jukebox | NASA Earth Observation Report",
        )

        canvas.drawRightString(
            self.PAGE_WIDTH - 20 * mm,
            10 * mm,
            f"Page {page_number}",
        )

        canvas.restoreState()

    # ---------------------------------------------------------
    # MAIN PDF GENERATOR
    # ---------------------------------------------------------

    def generate_pdf(
        self,
        report_data: Dict[str, Any],
        charts: Optional[Dict[str, BytesIO]] = None,
        report_format: str = "compact",
    ) -> BytesIO:
        """Generate a PDF and return it as an in-memory BytesIO object."""

        report_format = report_format.lower().strip()

        if report_format not in {"compact", "detailed"}:

            raise ValueError(
                "report_format must be either 'compact' or 'detailed'."
            )

        output = BytesIO()

        document = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=17 * mm,
            bottomMargin=22 * mm,
            title=report_data.get(
                "report_title",
                "Earth Jukebox Environmental Report",
            ),
            author="Earth Jukebox",
            subject="NASA Earth Observation Analysis",
        )

        story = []

        # Common sections
        story.extend(
            self._build_header(report_data)
        )

        story.extend(
            self._build_statistics(report_data)
        )

        story.extend(
            self._build_ai_summary(report_data)
        )

        if report_format == "compact":

            story.extend(
                self._build_charts(charts)
            )

            story.append(PageBreak())

            story.extend(
                self._build_provenance(report_data)
            )

            story.extend(
                self._build_limitations(report_data)
            )

            story.extend(
                self._build_sonification(
                    report_data,
                    detailed=False,
                )
            )

        else:

            story.extend(
                self._build_charts(charts)
            )

            story.append(PageBreak())

            story.extend(
                self._build_provenance(report_data)
            )

            story.extend(
                self._build_limitations(report_data)
            )

            story.append(PageBreak())

            story.extend(
                self._build_sonification(
                    report_data,
                    detailed=True,
                )
            )

            story.append(PageBreak())

            story.extend(
                self._build_observation_table(report_data)
            )

        document.build(
            story,
            onFirstPage=self._add_page_number,
            onLaterPages=self._add_page_number,
        )

        output.seek(0)

        return output

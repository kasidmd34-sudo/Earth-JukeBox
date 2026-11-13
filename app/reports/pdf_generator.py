"""PDF generation engine for Earth Jukebox.

Produces navigable ("interactive" PDF outline bookmarks + internal section links +
clickable NASA Worldview/portal links) compact and detailed reports.
"""

from io import BytesIO
import os
import re
from typing import Any, Dict, List, Optional

from reportlab.graphics.shapes import Circle, Drawing, Ellipse, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.sonification_service import SonificationService


class _Bookmark(Flowable):
    """Zero-height flowable adding a named PDF destination & outline bookmark."""

    def __init__(self, key: str, title: str, level: int = 0):
        super().__init__()
        self.key = key
        self.title = title
        self.level = level
        self.width = 0
        self.height = 0

    def draw(self):
        self.canv.bookmarkPage(self.key)
        self.canv.addOutlineEntry(self.title, self.key, level=self.level, closed=False)


class PDFGenerator:
    """Generate navigable Earth Jukebox PDF reports."""

    PAGE_WIDTH, PAGE_HEIGHT = A4

    NAVY = colors.HexColor("#14213D")
    BLUE = colors.HexColor("#2563EB")
    CYAN = colors.HexColor("#0891B2")
    LIGHT_BLUE = colors.HexColor("#EAF2FF")
    LIGHT_GREY = colors.HexColor("#F3F4F6")
    MID_GREY = colors.HexColor("#6B7280")
    DARK_GREY = colors.HexColor("#374151")
    BORDER = colors.HexColor("#D1D5DB")
    WHITE = colors.white

    def __init__(self):
        self.styles = getSampleStyleSheet()

        self.styles.add(ParagraphStyle(
            name="ReportTitle", parent=self.styles["Title"],
            fontName="Helvetica-Bold", fontSize=22, leading=26,
            textColor=self.NAVY, alignment=1, spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            name="ReportSubtitle", parent=self.styles["Normal"],
            fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=self.MID_GREY, alignment=1, spaceAfter=10,
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHeading", parent=self.styles["Heading2"],
            fontName="Helvetica-Bold", fontSize=13.5, leading=17,
            textColor=self.NAVY, spaceBefore=9, spaceAfter=6, keepWithNext=True,
        ))
        self.styles.add(ParagraphStyle(
            name="SubHeading", parent=self.styles["Heading3"],
            fontName="Helvetica-Bold", fontSize=10, leading=13,
            textColor=self.BLUE, spaceBefore=6, spaceAfter=4, keepWithNext=True,
        ))
        self.styles.add(ParagraphStyle(
            name="BodyCustom", parent=self.styles["BodyText"],
            fontName="Helvetica", fontSize=9, leading=13,
            textColor=self.DARK_GREY, spaceAfter=5,
        ))
        self.styles.add(ParagraphStyle(
            name="SmallCustom", parent=self.styles["BodyText"],
            fontName="Helvetica", fontSize=7.8, leading=10.5,
            textColor=self.DARK_GREY,
        ))
        self.styles.add(ParagraphStyle(
            name="TableHeaderCustom", parent=self.styles["Normal"],
            fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=self.WHITE,
        ))
        self.styles.add(ParagraphStyle(
            name="TableCellCustom", parent=self.styles["Normal"],
            fontName="Helvetica", fontSize=7.5, leading=9.5, textColor=self.DARK_GREY,
        ))
        self.styles.add(ParagraphStyle(
            name="SampleTableHeaderCustom", parent=self.styles["Normal"],
            fontName="Helvetica-Bold", fontSize=7, leading=8, textColor=self.WHITE,
        ))
        self.styles.add(ParagraphStyle(
            name="SampleTableCellCustom", parent=self.styles["Normal"],
            fontName="Helvetica", fontSize=7, leading=8.5, textColor=self.DARK_GREY,
        ))

    @staticmethod
    def _safe_text(value: Any, default: str = "Not available") -> str:
        return default if value is None or value == "" else str(value)

    @staticmethod
    def _format_display_text(value: Any) -> str:
        text = str(value)
        for source, display in {
            "degrees_Celsius": "°C",
            "degree_Celsius": "°C",
            "degrees_Fahrenheit": "°F",
            "degree_Fahrenheit": "°F",
        }.items():
            text = text.replace(source, display)
        return text

    @staticmethod
    def _escape(value: Any) -> str:
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _paragraph(self, text: Any, style: str = "BodyCustom") -> Paragraph:
        return Paragraph(self._escape(self._format_display_text(text)), self.styles[style])

    def _rich_paragraph(self, text: str, style: str = "BodyCustom") -> Paragraph:
        return Paragraph(self._format_display_text(text), self.styles[style])

    def _section(self, key: str, title: str) -> List[Any]:
        return [
            _Bookmark(key, title, level=0),
            Paragraph(f'<a name="{key}"/>{self._escape(title)}', self.styles["SectionHeading"]),
        ]

    def _subsection(self, title: str) -> Paragraph:
        return Paragraph(self._escape(title), self.styles["SubHeading"])

    def _build_logo_badge(self, is_media: bool = False) -> Any:
        """Render optional authorized NASA logo if present, else a clean vector Earth/NASA-data emblem."""
        custom_logo = os.path.join("assets", "nasa_logo.png")
        if os.path.exists(custom_logo):
            return Image(custom_logo, width=22 * mm, height=18 * mm, kind="proportional")

        d = Drawing(165 * mm, 20 * mm)
        # Left vector Earth Jukebox badge
        d.add(Circle(10 * mm, 10 * mm, 8.5 * mm, fillColor=self.NAVY, strokeColor=self.CYAN, strokeWidth=1.4))
        d.add(Ellipse(10 * mm, 10 * mm, 7 * mm, 3.2 * mm, fillColor=None, strokeColor=self.CYAN, strokeWidth=0.9))
        d.add(Circle(10 * mm, 10 * mm, 2.2 * mm, fillColor=self.CYAN, strokeColor=self.WHITE, strokeWidth=0.6))
        d.add(String(22 * mm, 12.2 * mm, "EARTH JUKEBOX", fontName="Helvetica-Bold", fontSize=11, fillColor=self.NAVY))
        d.add(String(
            22 * mm, 6.8 * mm,
            "Media Visual Analysis & Sonification" if is_media else "NASA Earth Observation Intelligence & Sonification",
            fontName="Helvetica", fontSize=8, fillColor=self.MID_GREY,
        ))
        # Right NASA-data attribution pill
        d.add(Rect(116 * mm, 4 * mm, 49 * mm, 12 * mm, rx=3 * mm, ry=3 * mm, fillColor=self.NAVY, strokeColor=self.BLUE, strokeWidth=0.8))
        d.add(Circle(123 * mm, 10 * mm, 4 * mm, fillColor=self.BLUE, strokeColor=self.WHITE, strokeWidth=0.8))
        d.add(String(120.5 * mm, 8.7 * mm, "NASA", fontName="Helvetica-Bold", fontSize=5.2, fillColor=self.WHITE))
        d.add(String(
            129 * mm, 10.6 * mm,
            "USER MEDIA" if is_media else "NASA DATA",
            fontName="Helvetica-Bold", fontSize=7, fillColor=self.WHITE,
        ))
        d.add(String(
            129 * mm, 6.5 * mm,
            "Visual Signal" if is_media else "Open Science",
            fontName="Helvetica", fontSize=6.5, fillColor=colors.HexColor("#93C5FD"),
        ))
        return d

    def _build_header(self, report: Dict[str, Any], detailed: bool) -> List[Any]:
        condition = report.get("condition", "environmental")
        location = report.get("location", {})
        time_window = report.get("time_window", {})
        is_media = report.get("observation_type") == "media_sequence"

        story: List[Any] = [
            self._build_logo_badge(is_media=is_media),
            Spacer(1, 3 * mm),
            self._paragraph(
                report.get("report_title", f"{condition.capitalize()} Environmental Report"),
                "ReportTitle",
            ),
            self._paragraph(
                "Interactive Summary, Annotated Graphs, Hierarchical Chords & Data Provenance",
                "ReportSubtitle",
            ),
        ]

        summary_rows = [
            [
                self._paragraph("CATEGORY", "TableHeaderCustom"),
                self._paragraph("LOCATION / SOURCE", "TableHeaderCustom"),
                self._paragraph("TIME WINDOW / SEQUENCE", "TableHeaderCustom"),
            ],
            [
                self._paragraph(condition.capitalize(), "TableCellCustom"),
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
        table = Table(summary_rows, colWidths=[45 * mm, 55 * mm, 65 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
            ("BACKGROUND", (0, 1), (-1, 1), self.LIGHT_BLUE),
            ("BOX", (0, 0), (-1, -1), 0.6, self.BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, self.BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.extend([table, Spacer(1, 3 * mm)])

        # Interactive quick-jump navigation bar (clickable internal PDF links)
        nav_items = [
            '<link href="#sec_summary" color="#2563EB"><u>1. Short Summary</u></link>',
            '<link href="#sec_charts" color="#2563EB"><u>2. Graphs &amp; Explanations</u></link>',
            '<link href="#sec_chords" color="#2563EB"><u>3. Hierarchical Chords</u></link>',
            '<link href="#sec_stats" color="#2563EB"><u>4. Statistics</u></link>',
            '<link href="#sec_provenance" color="#2563EB"><u>5. Provenance</u></link>',
            '<link href="#sec_limits" color="#2563EB"><u>6. Limitations</u></link>',
        ]
        if detailed:
            nav_items.append('<link href="#sec_records" color="#2563EB"><u>7. Records</u></link>')
        story.append(self._rich_paragraph(
            "<b>Quick Navigation (Click to Jump):</b> " + " &nbsp;|&nbsp; ".join(nav_items),
            "SmallCustom",
        ))
        story.append(Spacer(1, 4 * mm))
        return story

    def _build_ai_summary(self, report: Dict[str, Any]) -> List[Any]:
        ai_summary = report.get("ai_summary", {}) or {}
        story = self._section("sec_summary", "1. Short Executive Summary")
        story.append(self._paragraph(ai_summary.get("summary", "No summary was generated.")))

        findings = ai_summary.get("key_findings", []) or []
        if findings:
            story.append(self._subsection("Key Findings"))
            for finding in findings[:5]:
                story.append(self._paragraph(f"• {finding}"))

        story.append(self._paragraph(
            "Summary generation method: " + self._safe_text(ai_summary.get("generation_method"), "unknown"),
            "SmallCustom",
        ))
        story.append(Spacer(1, 3 * mm))
        return story

    def _build_charts(self, report: Dict[str, Any], charts: Optional[Dict[str, BytesIO]]) -> List[Any]:
        story = self._section("sec_charts", "2. Annotated Graphs & Explanations")
        stats = report.get("statistics", {}) or {}
        unit = self._format_display_text(self._safe_text(report.get("unit"), ""))
        condition = str(report.get("condition", "environmental")).capitalize()
        loc = report.get("location", {}) or {}

        if not charts:
            story.append(self._paragraph("No charts were supplied."))
            return story

        obs_buf = charts.get("observation_chart")
        if obs_buf is not None:
            obs_buf.seek(0)
            story.append(self._subsection("Observation Timeline with Alphabetical Chord Markers (A-L)"))
            story.append(Image(obs_buf, width=165 * mm, height=79 * mm, kind="proportional"))
            story.append(self._paragraph(
                f"<b>Graph Explanation:</b> This chart plots {stats.get('observation_count', 0)} {condition.lower()} "
                f"values ({unit}). The dashed horizontal line marks the mean ({stats.get('mean', 'N/A')} {unit}), "
                f"spanning from {stats.get('minimum', 'N/A')} to {stats.get('maximum', 'N/A')} {unit}. "
                "The alphabetical badges (A, B, C...) mark representative points in chronological order; "
                "green badges with ↑ indicate a higher musical pitch than the previous step, while coral badges "
                "with ↓ indicate a lower pitch. Cross-reference each letter in Section 3 below."
            ))

        lat, lon = loc.get("latitude"), loc.get("longitude")
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            wv_url = (
                f"https://worldview.earthdata.nasa.gov/?v="
                f"{max(-180, lon - 2):.2f},{max(-90, lat - 2):.2f},"
                f"{min(180, lon + 2):.2f},{min(90, lat + 2):.2f}"
            )
            story.append(self._rich_paragraph(
                f'<b>Interactive Satellite Layer:</b> <link href="{self._escape(wv_url)}" color="#2563EB">'
                "<u>Open this region in NASA Worldview Satellite Map</u></link>",
                "SmallCustom",
            ))

        dist_buf = charts.get("distribution_chart")
        if dist_buf is not None:
            dist_buf.seek(0)
            story.append(self._subsection("Value Distribution Histogram"))
            story.append(Image(dist_buf, width=165 * mm, height=74 * mm, kind="proportional"))
            story.append(self._paragraph(
                f"<b>Distribution Explanation:</b> Shows how frequently observations fell into each value band "
                f"({unit}). A tight cluster around the red dashed mean line indicates steady conditions, whereas "
                "a wide spread reflects stronger seasonal or event variability."
            ))

        story.append(Spacer(1, 3 * mm))
        return story

    def _build_sonification(self, report: Dict[str, Any], detailed: bool) -> List[Any]:
        sonification = report.get("sonification", {}) or {}
        parameters = sonification.get("parameters", []) or []
        hierarchy = sonification.get("chord_hierarchy", {}) or {}

        story = self._section("sec_chords", "3. Hierarchical Chords & Sonification Mapping")
        if not sonification:
            story.append(self._paragraph("Sonification parameters are unavailable."))
            return story

        # Level 1: Tonal Architecture
        story.append(self._subsection("Level 1 — Tonal Center & Acoustic Profile"))
        story.append(self._rich_paragraph(
            f"<b>Key &amp; Scale:</b> {self._escape(sonification.get('musical_key', 'A'))} "
            f"({self._escape(str(sonification.get('scale_mode', 'pentatonic_minor')).replace('_', ' ').title())}) "
            f"&nbsp;|&nbsp; <b>Profile:</b> {self._escape(sonification.get('sound_profile', 'Synth'))}<br/>"
            f"<b>Dynamic Span:</b> {self._escape(sonification.get('dynamic_range_min', 0))} to "
            f"{self._escape(sonification.get('dynamic_range_max', 1))} "
            f"&nbsp;|&nbsp; <b>Total Mapped Events:</b> {len(parameters)}"
        ))

        # Level 2: Hierarchical Register Tiers (Peak -> Mid -> Base)
        tiers = hierarchy.get("level_3_register_tiers", {}) or {}
        if tiers:
            story.append(self._subsection("Level 2 — Hierarchical Chord Register Tiers (High → Mid → Low)"))
            tier_rows = [[
                self._paragraph("Register Tier", "SampleTableHeaderCustom"),
                self._paragraph("Events", "SampleTableHeaderCustom"),
                self._paragraph("Value Span", "SampleTableHeaderCustom"),
                self._paragraph("Distinct Chords Used", "SampleTableHeaderCustom"),
            ]]
            for key in ("high", "mid", "low"):
                t = tiers.get(key)
                if not t:
                    continue
                span_txt = (
                    f"{t.get('value_min')} to {t.get('value_max')}"
                    if t.get("value_min") is not None else "—"
                )
                chords_txt = ", ".join(t.get("distinct_chords") or []) or "—"
                tier_rows.append([
                    self._paragraph(t.get("label", key.title()), "SampleTableCellCustom"),
                    self._paragraph(str(t.get("event_count", 0)), "SampleTableCellCustom"),
                    self._paragraph(span_txt, "SampleTableCellCustom"),
                    self._paragraph(chords_txt, "SampleTableCellCustom"),
                ])
            tier_table = Table(tier_rows, colWidths=[45 * mm, 16 * mm, 32 * mm, 72 * mm], repeatRows=1)
            tier_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.WHITE, self.LIGHT_GREY]),
                ("GRID", (0, 0), (-1, -1), 0.35, self.BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.extend([tier_table, Spacer(1, 3 * mm)])

        # Level 3: Exact Graph-Matched A-L Chord Sequence
        if parameters:
            story.append(self._subsection("Level 3 — Graph Marker Cross-Reference (Alphabetical A-L)"))
            story.append(self._paragraph(
                "Each row below corresponds directly to the alphabetical badge (A, B, C...) plotted on the Section 2 timeline."
            ))
            chosen_indices = SonificationService.sample_marker_indices(len(parameters), max_markers=12)
            chord_rows = [[
                self._paragraph("Graph", "SampleTableHeaderCustom"),
                self._paragraph("Timestamp", "SampleTableHeaderCustom"),
                self._paragraph("Value", "SampleTableHeaderCustom"),
                self._paragraph("Chord & Triad Notes", "SampleTableHeaderCustom"),
                self._paragraph("MIDI", "SampleTableHeaderCustom"),
                self._paragraph("Hz", "SampleTableHeaderCustom"),
                self._paragraph("Pitch Move", "SampleTableHeaderCustom"),
            ]]
            for marker_idx, pt_idx in enumerate(chosen_indices):
                item = parameters[pt_idx]
                letter = chr(65 + marker_idx)
                chord = item.get("chord_name") or item.get("musical_note") or "—"
                notes = ", ".join(item.get("chord_notes") or [])
                chord_text = f"{chord} ({notes})" if notes else chord
                p_dir = item.get("pitch_direction", "initial")
                dir_label = "Higher (↑)" if p_dir == "higher" else ("Lower (↓)" if p_dir == "lower" else p_dir.title())
                chord_rows.append([
                    self._paragraph(letter, "SampleTableCellCustom"),
                    self._paragraph(item.get("timestamp", ""), "SampleTableCellCustom"),
                    self._paragraph(item.get("original_value", ""), "SampleTableCellCustom"),
                    self._paragraph(chord_text, "SampleTableCellCustom"),
                    self._paragraph(", ".join(str(x) for x in (item.get("chord_midi") or [])), "SampleTableCellCustom"),
                    self._paragraph(", ".join(str(x) for x in (item.get("chord_frequencies_hz") or [])), "SampleTableCellCustom"),
                    self._paragraph(dir_label, "SampleTableCellCustom"),
                ])

            chord_table = Table(
                chord_rows,
                colWidths=[13 * mm, 24 * mm, 16 * mm, 44 * mm, 21 * mm, 26 * mm, 21 * mm],
                repeatRows=1,
            )
            chord_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.WHITE, self.LIGHT_GREY]),
                ("GRID", (0, 0), (-1, -1), 0.35, self.BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.extend([chord_table, Spacer(1, 3 * mm)])

        if detailed and parameters:
            story.append(self._subsection("Detailed Sonification Event Samples (First 30 Steps)"))
            rows = [[
                self._paragraph("Timestamp", "SampleTableHeaderCustom"),
                self._paragraph("Value", "SampleTableHeaderCustom"),
                self._paragraph("Chord", "SampleTableHeaderCustom"),
                self._paragraph("MIDI", "SampleTableHeaderCustom"),
                self._paragraph("Hz", "SampleTableHeaderCustom"),
                self._paragraph("Tempo", "SampleTableHeaderCustom"),
            ]]
            for item in parameters[:30]:
                rows.append([
                    self._paragraph(item.get("timestamp", ""), "SampleTableCellCustom"),
                    self._paragraph(item.get("original_value", ""), "SampleTableCellCustom"),
                    self._paragraph(item.get("chord_name", item.get("musical_note", "")), "SampleTableCellCustom"),
                    self._paragraph(item.get("midi_note", ""), "SampleTableCellCustom"),
                    self._paragraph(item.get("pitch_hz", ""), "SampleTableCellCustom"),
                    self._paragraph(item.get("tempo_bpm", ""), "SampleTableCellCustom"),
                ])
            table = Table(rows, colWidths=[30 * mm, 22 * mm, 33 * mm, 20 * mm, 30 * mm, 30 * mm], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.WHITE, self.LIGHT_GREY]),
                ("GRID", (0, 0), (-1, -1), 0.35, self.BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.extend([table, Spacer(1, 2 * mm)])

        return story

    def _build_statistics(self, report: Dict[str, Any]) -> List[Any]:
        statistics = report.get("statistics", {}) or {}
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
            ("First-to-last percentage change", statistics.get("change_percent")),
        ]
        rows = [[self._paragraph("Metric", "TableHeaderCustom"), self._paragraph("Value", "TableHeaderCustom")]]
        for label, value in metrics:
            if value is None:
                display = "Not available"
            elif label == "Observation count":
                display = str(value)
            elif label == "First-to-last percentage change":
                display = f"{value}%"
            else:
                display = f"{value} {unit}"
            rows.append([self._paragraph(label, "TableCellCustom"), self._paragraph(display, "TableCellCustom")])

        table = Table(rows, colWidths=[75 * mm, 90 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.WHITE, self.LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.4, self.BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return [*self._section("sec_stats", "4. Statistical Overview"), table, Spacer(1, 4 * mm)]

    def _build_provenance(self, report: Dict[str, Any]) -> List[Any]:
        source = report.get("data_source", {}) or {}
        metadata = report.get("report_metadata", {}) or {}
        variables = source.get("variables", []) or []
        variables_display = variables if isinstance(variables, str) else ", ".join(str(x) for x in variables)

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
        rows = [[self._paragraph("Metadata", "TableHeaderCustom"), self._paragraph("Value", "TableHeaderCustom")]]
        for label, value in fields:
            val_text = self._safe_text(value)
            if isinstance(value, str) and value.startswith("http"):
                cell = self._rich_paragraph(
                    f'<link href="{self._escape(value)}" color="#2563EB"><u>{self._escape(value)}</u></link>',
                    "SmallCustom",
                )
            else:
                cell = self._paragraph(val_text, "SmallCustom")
            rows.append([self._paragraph(label, "TableCellCustom"), cell])

        table = Table(rows, colWidths=[48 * mm, 117 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.WHITE, self.LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.4, self.BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return [*self._section("sec_provenance", "5. Data Provenance"), table, Spacer(1, 4 * mm)]

    def _build_limitations(self, report: Dict[str, Any]) -> List[Any]:
        limitations = report.get("limitations", []) or []
        ai_summary = report.get("ai_summary", {}) or {}
        ai_limitations = ai_summary.get("limitations", []) or []

        def normalise(t: Any) -> str:
            return " ".join(re.sub(r"[^a-z0-9\s]", " ", str(t).lower()).split())

        combined: List[str] = []
        for item in [*limitations, *ai_limitations]:
            if not item:
                continue
            cand = normalise(item)
            cand_words = set(cand.split())
            is_dup = False
            for existing in combined:
                ex_words = set(normalise(existing).split())
                if cand == normalise(existing):
                    is_dup = True
                    break
                if cand_words and ex_words and len(cand_words & ex_words) / len(cand_words | ex_words) >= 0.55:
                    is_dup = True
                    break
            if not is_dup:
                combined.append(str(item))

        story = self._section("sec_limits", "6. Scientific Limitations & Disclaimer")
        for item in combined:
            story.append(self._paragraph(f"• {item}"))
        story.append(Spacer(1, 2 * mm))
        story.append(self._paragraph(
            "This document is an analytical and sonification report. It is not an official NASA forecast or emergency warning.",
            "SmallCustom",
        ))
        return story

    def _build_observation_table(self, report: Dict[str, Any]) -> List[Any]:
        observations = report.get("observations", []) or []
        story = self._section("sec_records", "7. Observation Records")
        if not observations:
            story.append(self._paragraph("No observation records were returned."))
            return story

        rows = [[
            self._paragraph("Timestamp / Step", "TableHeaderCustom"),
            self._paragraph("Value", "TableHeaderCustom"),
            self._paragraph("Unit", "TableHeaderCustom"),
        ]]
        for item in observations:
            rows.append([
                self._paragraph(item.get("timestamp", ""), "TableCellCustom"),
                self._paragraph(item.get("value", ""), "TableCellCustom"),
                self._paragraph(item.get("unit", ""), "TableCellCustom"),
            ])
        table = Table(rows, colWidths=[55 * mm, 45 * mm, 65 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.NAVY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.WHITE, self.LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.35, self.BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ]))
        story.extend([table, Spacer(1, 4 * mm)])
        return story

    def _add_page_number(self, canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(self.BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, 15 * mm, self.PAGE_WIDTH - 20 * mm, 15 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(self.MID_GREY)
        canvas.drawString(20 * mm, 10 * mm, "Earth Jukebox | Interactive Environmental & Sonification Report")
        canvas.drawRightString(self.PAGE_WIDTH - 20 * mm, 10 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    def generate_pdf(
        self,
        report_data: Dict[str, Any],
        charts: Optional[Dict[str, BytesIO]] = None,
        report_format: str = "compact",
    ) -> BytesIO:
        report_format = report_format.lower().strip()
        if report_format not in {"compact", "detailed"}:
            raise ValueError("report_format must be either 'compact' or 'detailed'.")

        detailed = report_format == "detailed"
        output = BytesIO()
        document = SimpleDocTemplate(
            output, pagesize=A4,
            rightMargin=20 * mm, leftMargin=20 * mm, topMargin=16 * mm, bottomMargin=22 * mm,
            title=report_data.get("report_title", "Earth Jukebox Environmental Report"),
            author="Earth Jukebox",
            subject="Earth Observation Analysis & Sonification",
        )

        story: List[Any] = []
        story.extend(self._build_header(report_data, detailed=detailed))
        story.extend(self._build_ai_summary(report_data))
        story.extend(self._build_charts(report_data, charts))
        story.append(PageBreak())
        story.extend(self._build_sonification(report_data, detailed=detailed))
        story.extend(self._build_statistics(report_data))
        if detailed:
            story.append(PageBreak())
        story.extend(self._build_provenance(report_data))
        story.extend(self._build_limitations(report_data))
        if detailed:
            story.append(PageBreak())
            story.extend(self._build_observation_table(report_data))

        document.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        output.seek(0)
        return output
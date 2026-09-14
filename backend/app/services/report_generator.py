"""Generate project PDF reports from persisted BhoomiGuard records."""

from html import escape
from io import BytesIO
from typing import Iterable


def _value(value: object | None) -> str:
    """Format an optional persisted value without manufacturing a substitute."""

    return "Not available" if value is None or value == "" else str(value)


def _rate(value: object | None) -> str:
    if value is None or value == "":
        return "Not available"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return _value(value)


def _completion(value: object | None) -> str:
    if value is None or value == "":
        return "Not available"
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return _value(value)


def _bottleneck(project: object) -> str | None:
    """Summarize only explicit officer-maintained operational conditions."""

    checks = (
        ("pending_court_cases", "Pending court cases require legal follow-up."),
        ("legal_disputes", "Legal disputes require review."),
        ("ownership_conflicts", "Ownership conflicts require resolution."),
        ("pending_approvals", "Pending approvals require coordination."),
        ("missing_documents", "Missing documents require completion."),
    )
    for attribute, message in checks:
        if (getattr(project, attribute, 0) or 0) > 0:
            return message
    return None


def _section(title: str, rows: Iterable[tuple[str, object | None]], styles: object) -> list[object]:
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    data = [
        [
            Paragraph(f"<b>{escape(str(label))}</b>", styles["BodyText"]),
            Paragraph(escape(_value(value)), styles["BodyText"]),
        ]
        for label, value in rows
    ]
    table = Table(data, colWidths=[5.25 * cm, 11.25 * cm], repeatRows=0)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9e2ec")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f6f9fb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [Paragraph(title, styles["Heading2"]), table, Spacer(1, 0.4 * cm)]


def _page_chrome(canvas: object, document: object) -> None:
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d6e2eb"))
    canvas.line(1.6 * cm, 28.2 * cm, 19.4 * cm, 28.2 * cm)
    canvas.setFillColor(colors.HexColor("#264d6b"))
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(1.6 * cm, 28.55 * cm, "BHOOMIGUARD AI  |  OFFICER REPORT")
    canvas.setFillColor(colors.HexColor("#6a7f90"))
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(19.4 * cm, 1.25 * cm, f"Page {document.page}")
    canvas.restoreState()


def build_project_report(
    project: object,
    prediction: object | None,
    risk_factors: list[object],
    recommendations: list[object],
    alerts: list[object],
    interventions: list[object],
    acquisition_cases: list[object],
) -> bytes:
    """Return a branded PDF using only supplied persisted database records."""

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate
    except ImportError as error:
        raise RuntimeError("PDF report generation dependencies are not installed") from error

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=2.2 * cm,
        bottomMargin=1.9 * cm,
        title=f"BhoomiGuard AI — {_value(getattr(project, 'project_code', None))}",
    )
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#173b58")
    styles["Heading2"].textColor = colors.HexColor("#234e6f")
    styles["Heading2"].spaceBefore = 5
    styles["Heading2"].spaceAfter = 8
    styles.add(ParagraphStyle(
        name="ReportIntro",
        parent=styles["BodyText"],
        textColor=colors.HexColor("#5d7182"),
        leading=15,
        spaceAfter=12,
    ))

    story: list[object] = [
        Paragraph("BhoomiGuard AI", styles["Title"]),
        Paragraph("Land Acquisition Project Monitoring Report", styles["Heading2"]),
        Paragraph(
            f"Project record: <b>{escape(_value(getattr(project, 'name', None)))}</b> "
            f"({escape(_value(getattr(project, 'project_code', None)))})",
            styles["ReportIntro"],
        ),
    ]
    story += _section("Project overview", [
        ("State", getattr(project, "state", None)),
        ("District", getattr(project, "district", None)),
        ("Village", getattr(project, "village", None)),
        ("Project type", getattr(project, "project_type", None)),
        ("Current acquisition stage", getattr(project, "current_stage", None)),
        ("Project status", getattr(project, "status", None)),
        ("Land area (acres)", getattr(project, "land_area_acres", None)),
        ("Affected families", getattr(project, "affected_families", None)),
        ("Villages affected", getattr(project, "villages_affected", None)),
    ], styles)
    story += _section("Latest persisted prediction", [
        ("Risk score", getattr(prediction, "risk_score", None)),
        ("Risk category", getattr(prediction, "risk_category", None)),
        ("Delay probability", _rate(getattr(prediction, "delay_probability", None))),
        ("Predicted delay (days)", getattr(prediction, "predicted_delay_days", None)),
        ("Model version", getattr(prediction, "model_version", None)),
    ], styles)
    story += _section("Officer-facing explanation", [
        ("Why this project is at risk", "Not available from the persisted prediction. No explanation has been inferred."),
        ("Current bottleneck", _bottleneck(project)),
    ], styles)
    story += _section("Timeline and acquisition progress", [
        ("Documentation completion", _completion(getattr(project, "documentation_completion_pct", None))),
        ("Compensation completion", _completion(getattr(project, "compensation_completion_pct", None))),
        ("Rehabilitation completion", _completion(getattr(project, "rehabilitation_completion_pct", None))),
        ("Resettlement completion", _completion(getattr(project, "resettlement_completion_pct", None))),
        ("Possession completion", _completion(getattr(project, "possession_completion_pct", None))),
        ("Days in current stage", getattr(project, "days_in_current_stage", None)),
        ("Days remaining to target", getattr(project, "days_remaining_to_target", None)),
        ("Previous stage delay (days)", getattr(project, "previous_stage_delay_days", None)),
    ], styles)
    story += _section("Acquisition cases", [
        (
            _value(getattr(case, "case_number", None)),
            " · ".join([
                _value(getattr(case, "current_stage", None)),
                _value(getattr(case, "case_status", None)),
                f"Days pending: {_value(getattr(case, 'days_pending', None))}",
            ]),
        ) for case in acquisition_cases] or [("Acquisition cases", None)], styles)
    story += _section("Recommendations", [
        (getattr(item, "title", "Recommendation"), getattr(item, "description", None))
        for item in recommendations
    ] or [("Recommendations", None)], styles)
    story += _section("Alerts", [
        (getattr(item, "severity", None) or getattr(item, "alert_type", None) or "Alert", getattr(item, "message", None))
        for item in alerts
    ] or [("Alerts", None)], styles)
    story += _section("Interventions", [
        (getattr(item, "intervention_type", None) or "Intervention", " · ".join([
            _value(getattr(item, "action", None)),
            f"Owner: {_value(getattr(item, 'owner_role', None))}",
            f"Status: {_value(getattr(item, 'status', None))}",
        ]))
        for item in interventions
    ] or [("Interventions", None)], styles)
    story += _section("Technical audit factors", [
        (getattr(factor, "factor_name", "Factor"), " · ".join([
            f"Impact: {_value(getattr(factor, 'impact', None))}",
            f"Direction: {_value(getattr(factor, 'direction', None))}",
        ]))
        for factor in risk_factors
    ] or [("Technical audit factors", None)], styles)

    document.build(story, onFirstPage=_page_chrome, onLaterPages=_page_chrome)
    return buffer.getvalue()

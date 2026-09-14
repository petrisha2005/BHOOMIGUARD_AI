"""Central configuration for the BhoomiGuard prototype data foundation."""

from pathlib import Path

RANDOM_SEED = 42
ML_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = ML_DIR / "data" / "raw" / "land_acquisition_cases.csv"
MODELS_DIR = ML_DIR / "models"
CLASSIFIER_MODEL_PATH = MODELS_DIR / "delay_classifier.joblib"
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.json"
MODEL_VERSION = "0.1.0"
TEST_SIZE = 0.20
RISK_THRESHOLDS = ((25, "Low"), (50, "Moderate"), (75, "High"), (101, "Critical"))
REPORTS_DIR = ML_DIR / "reports"
SHAP_BACKGROUND_ROWS = 200
SHAP_GLOBAL_SAMPLE_ROWS = 1_000

STAGE_NAMES = (
    "Notification",
    "Survey",
    "Objections",
    "Award",
    "Compensation",
    "Rehabilitation & Resettlement",
    "Possession",
)
PROJECT_TYPES = ("Highway", "Railway", "Metro", "Industrial Corridor", "Power Transmission", "Irrigation")
STATE_DISTRICTS = {
    "Maharashtra": ("Pune", "Nashik", "Nagpur", "Thane"),
    "Karnataka": ("Bengaluru Urban", "Mysuru", "Belagavi", "Kalaburagi"),
    "Tamil Nadu": ("Chennai", "Coimbatore", "Madurai", "Salem"),
    "Uttar Pradesh": ("Lucknow", "Kanpur Nagar", "Varanasi", "Agra"),
    "Rajasthan": ("Jaipur", "Jodhpur", "Kota", "Udaipur"),
    "Gujarat": ("Ahmedabad", "Surat", "Vadodara", "Rajkot"),
    "Telangana": ("Hyderabad", "Warangal", "Nizamabad", "Karimnagar"),
    "Madhya Pradesh": ("Bhopal", "Indore", "Jabalpur", "Gwalior"),
}

TARGET_COLUMNS = ("delay_flag", "actual_delay_days")
CATEGORICAL_COLUMNS = ("project_type", "state", "district", "current_stage")
NUMERICAL_COLUMNS = (
    "land_area_acres", "affected_families", "villages_affected",
    "legal_disputes", "ownership_conflicts", "pending_court_cases",
    "documentation_completion_pct", "missing_documents",
    "compensation_completion_pct", "compensation_pending_cases", "average_compensation_delay_days",
    "rehabilitation_completion_pct", "resettlement_completion_pct", "affected_families_rehabilitated",
    "pending_approvals", "approval_delay_days", "stakeholder_response_delay_days",
    "days_in_current_stage", "possession_completion_pct", "historical_delay_rate",
    "days_remaining_to_target", "previous_stage_delay_days",
)
FEATURE_COLUMNS = CATEGORICAL_COLUMNS + NUMERICAL_COLUMNS

FEATURE_DISPLAY_NAMES = {
    "project_type": "Project Type", "state": "State", "district": "District", "current_stage": "Current Stage",
    "land_area_acres": "Land Area (Acres)", "affected_families": "Affected Families",
    "villages_affected": "Villages Affected", "legal_disputes": "Legal Disputes",
    "ownership_conflicts": "Ownership Conflicts", "pending_court_cases": "Pending Court Cases",
    "documentation_completion_pct": "Documentation Completion", "missing_documents": "Missing Documents",
    "compensation_completion_pct": "Compensation Completion", "compensation_pending_cases": "Compensation Pending Cases",
    "average_compensation_delay_days": "Average Compensation Delay (Days)",
    "rehabilitation_completion_pct": "Rehabilitation Completion", "resettlement_completion_pct": "Resettlement Completion",
    "affected_families_rehabilitated": "Affected Families Rehabilitated", "pending_approvals": "Pending Approvals",
    "approval_delay_days": "Approval Delay (Days)", "stakeholder_response_delay_days": "Stakeholder Response Delay (Days)",
    "days_in_current_stage": "Days in Current Stage", "possession_completion_pct": "Possession Completion",
    "historical_delay_rate": "Historical Delay Rate", "days_remaining_to_target": "Days Remaining to Target",
    "previous_stage_delay_days": "Previous Stage Delay (Days)",
}

# Step 4: deterministic mappings from model factors to officer interventions.
RECOMMENDATION_FEATURE_CATEGORIES = {
    "compensation_completion_pct": "Compensation", "compensation_pending_cases": "Compensation",
    "average_compensation_delay_days": "Compensation",
    "legal_disputes": "Legal / Ownership", "ownership_conflicts": "Legal / Ownership",
    "pending_court_cases": "Legal / Ownership", "documentation_completion_pct": "Documentation",
    "missing_documents": "Documentation", "pending_approvals": "Approvals",
    "approval_delay_days": "Approvals", "rehabilitation_completion_pct": "Rehabilitation & Resettlement",
    "resettlement_completion_pct": "Rehabilitation & Resettlement",
    "affected_families_rehabilitated": "Rehabilitation & Resettlement",
    "stakeholder_response_delay_days": "Inter-department Coordination",
    "days_in_current_stage": "Inter-department Coordination",
}
RECOMMENDATION_TEMPLATES = {
    "Compensation": {
        "action": "Verify pending compensation records, payment approvals, and beneficiary details; escalate unresolved cases.",
        "responsible_role": "Compensation/Finance Officer",
        "monitoring": "Track pending compensation cases and payment-approval ageing until closure.",
    },
    "Legal / Ownership": {
        "action": "Initiate ownership-document verification and refer unresolved disputes or court matters for legal review.",
        "responsible_role": "Legal Officer",
        "monitoring": "Track disputed parcels, legal-review status, and pending court-case milestones.",
    },
    "Documentation": {
        "action": "Identify incomplete records, assign document verification, and set a completion deadline.",
        "responsible_role": "Documentation/Records Officer",
        "monitoring": "Track missing-document count and documentation-completion percentage.",
    },
    "Approvals": {
        "action": "Identify the pending approval authority, follow up on overdue approvals, and record a decision deadline.",
        "responsible_role": "Land Acquisition Officer",
        "monitoring": "Track pending approvals and approval-delay ageing until resolution.",
    },
    "Rehabilitation & Resettlement": {
        "action": "Review pending rehabilitation and resettlement actions; verify affected-family rehabilitation status.",
        "responsible_role": "R&R Officer",
        "monitoring": "Track rehabilitation, resettlement, and affected-family completion progress.",
    },
    "Inter-department Coordination": {
        "action": "Assign a project coordinator, schedule an inter-department follow-up, and escalate unresolved blockers.",
        "responsible_role": "Project Coordinator",
        "monitoring": "Track stakeholder response delays and time spent in the current acquisition stage.",
    },
}
PRIORITY_DEADLINE_DAYS = {"CRITICAL": 2, "HIGH": 5, "MEDIUM": 10, "LOW": 21}
RISK_CATEGORY_PRIORITY = {"Critical": "HIGH", "High": "HIGH", "Moderate": "MEDIUM", "Low": "LOW"}
CRITICAL_CONTRIBUTION_THRESHOLD = 0.35

# Step 5: deterministic alert and escalation configuration.
ALERT_CATEGORY_BY_RECOMMENDATION_CATEGORY = {
    "Compensation": "COMPENSATION", "Legal / Ownership": "LEGAL_OWNERSHIP",
    "Documentation": "DOCUMENTATION", "Approvals": "APPROVAL",
    "Rehabilitation & Resettlement": "REHABILITATION_RESETTLEMENT",
    "Inter-department Coordination": "COORDINATION",
}
ALERT_SEVERITY_BY_RECOMMENDATION_PRIORITY = {
    "CRITICAL": "CRITICAL", "HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW",
}
ALERT_STATUSES = ("OPEN", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED", "ESCALATED")
ALERT_INITIAL_STATUS = "OPEN"
ALERT_CRITICAL_RISK_CATEGORY = "Critical"
ALERT_ESCALATION_SEVERITIES = ("CRITICAL",)
ALERT_ESCALATE_HIGH_WITH_RECOMMENDATION_FLAG = True

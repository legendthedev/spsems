"""
backend/pipeline/institutional_ml_pipeline.py
Institutional Live Data Extraction, Transformation, and Model Training Pipeline.
Extracts live student project telemetry, submissions, supervisor feedback response
times, and milestone progress from the institutional database, transforms them into
feature matrices, and dispatches them to retrain the XGBoost and Random Forest models.
Also supports external university database connectors (PostgreSQL / MySQL / SQLite / SIS API).
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import httpx
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session

from config import get_settings

logger = logging.getLogger("institutional_ml_pipeline")
settings = get_settings()

FEATURE_NAMES = [
    "submission_rate",
    "days_since_last_submission",
    "milestone_completion_rate",
    "overdue_milestones",
    "supervisor_feedback_response_days",
    "chapter_progress",
    "time_progress_ratio",
    "stagnation_z_score",
    "total_submissions",
    "chapters_remaining",
]

CHAPTER_WEIGHTS = {
    "proposal": 0.15,
    "chapter1": 0.30,
    "chapter2": 0.45,
    "chapter3": 0.60,
    "chapter4": 0.75,
    "chapter5": 0.90,
    "final": 1.00,
}


class InstitutionalDataExtractor:
    """Extracts student project telemetry from SPSEMS institutional database."""

    @staticmethod
    def extract_live_records(db: Session, institution_slug: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extracts live student projects, milestone histories, and submission logs
        from the database and calculates real-world behavioral features.
        """
        query = """
            SELECT
                p.project_id,
                p.title,
                p.status AS project_status,
                p.risk_label AS existing_risk_label,
                p.risk_score AS existing_risk_score,
                p.final_grade,
                p.submitted_at AS project_created_at,
                s.student_id,
                s.matric_number,
                s.department,
                s.level,
                s.research_domain,
                u.full_name AS student_name,
                sup.supervisor_id,
                sup_u.full_name AS supervisor_name,
                inst.code AS institution_code,
                inst.name AS institution_name
            FROM projects p
            JOIN students s ON p.student_id = s.student_id
            JOIN users u ON s.user_id = u.user_id
            LEFT JOIN supervisors sup ON p.supervisor_id = sup.supervisor_id
            LEFT JOIN users sup_u ON sup.user_id = sup_u.user_id
            LEFT JOIN institutions inst ON (u.email LIKE '%' || inst.official_domain OR inst.code = 'KWASU')
        """
        rows = db.execute(text(query)).fetchall()
        now = datetime.utcnow()
        extracted = []

        for r in rows:
            p_id = r.project_id
            s_id = r.student_id

            # 1. Submissions Telemetry
            subs = db.execute(
                text("""
                    SELECT submitted_at, reviewed_at, status, chapter
                    FROM submissions
                    WHERE project_id = :p_id
                    ORDER BY submitted_at ASC
                """),
                {"p_id": p_id},
            ).fetchall()

            total_submissions = len(subs)
            last_sub_date = None
            review_deltas = []
            highest_chapter_val = 0.0

            for sub in subs:
                sub_date = None
                if sub.submitted_at:
                    try:
                        sub_date = datetime.fromisoformat(str(sub.submitted_at).replace("Z", ""))
                    except Exception:
                        pass
                if sub_date:
                    if last_sub_date is None or sub_date > last_sub_date:
                        last_sub_date = sub_date

                if sub.status == "approved" and sub.chapter in CHAPTER_WEIGHTS:
                    highest_chapter_val = max(highest_chapter_val, CHAPTER_WEIGHTS[sub.chapter])

                if sub.submitted_at and sub.reviewed_at:
                    try:
                        sub_t = datetime.fromisoformat(str(sub.submitted_at).replace("Z", ""))
                        rev_t = datetime.fromisoformat(str(sub.reviewed_at).replace("Z", ""))
                        delta = max((rev_t - sub_t).total_seconds() / 86400.0, 0.5)
                        review_deltas.append(delta)
                    except Exception:
                        pass

            # Calculate days since last submission
            if last_sub_date:
                days_since = max((now - last_sub_date).days, 0)
            else:
                try:
                    p_start = datetime.fromisoformat(str(r.project_created_at).replace("Z", ""))
                    days_since = max((now - p_start).days, 7)
                except Exception:
                    days_since = 30

            avg_feedback_days = float(np.mean(review_deltas)) if review_deltas else 5.0

            # 2. Milestones Telemetry
            milestones = db.execute(
                text("""
                    SELECT due_date, completed_date, status
                    FROM milestones
                    WHERE project_id = :p_id
                """),
                {"p_id": p_id},
            ).fetchall()

            total_milestones = len(milestones)
            completed_milestones = sum(1 for m in milestones if m.status == "completed")
            overdue_milestones = 0

            for m in milestones:
                if m.status in ("overdue", "missed"):
                    overdue_milestones += 1
                elif m.status != "completed" and m.due_date:
                    try:
                        due_dt = datetime.fromisoformat(str(m.due_date).split()[0])
                        if due_dt < now:
                            overdue_milestones += 1
                    except Exception:
                        pass

            milestone_completion_rate = (
                completed_milestones / max(total_milestones, 1) if total_milestones > 0 else 0.25
            )

            # 3. Project Duration & Temporal Telemetry
            try:
                p_start = datetime.fromisoformat(str(r.project_created_at).replace("Z", ""))
                weeks_elapsed = max((now - p_start).days / 7.0, 1.0)
            except Exception:
                weeks_elapsed = 8.0

            total_weeks = 20.0
            progress_ratio = min(weeks_elapsed / total_weeks, 1.2)
            sub_rate = total_submissions / max(weeks_elapsed, 1.0)
            z_stagnation = (days_since - 14.0) / 7.0
            chapter_progress = highest_chapter_val
            chapters_remaining = max(1.0 - chapter_progress, 0.0)

            # 4. Ground-Truth Risk Outcome Calculation
            is_at_risk = 0
            category = 1  # 0: Critical, 1: On Track, 2: Exceeding

            if r.project_status == "completed" or (chapter_progress >= 0.75 and overdue_milestones == 0):
                is_at_risk = 0
                category = 2
            elif (
                overdue_milestones >= 2
                or days_since >= 28
                or r.existing_risk_label == "critical"
                or (r.final_grade is not None and r.final_grade < 50)
            ):
                is_at_risk = 1
                category = 0
            elif overdue_milestones == 1 or days_since >= 18 or r.existing_risk_label == "at_risk":
                is_at_risk = 1
                category = 1
            else:
                is_at_risk = 0
                category = 1

            feature_vector = [
                round(float(sub_rate), 4),
                round(float(days_since), 2),
                round(float(milestone_completion_rate), 4),
                int(overdue_milestones),
                round(float(avg_feedback_days), 2),
                round(float(chapter_progress), 4),
                round(float(progress_ratio), 4),
                round(float(z_stagnation), 4),
                int(total_submissions),
                round(float(chapters_remaining), 4),
            ]

            extracted.append({
                "project_id": p_id,
                "student_id": s_id,
                "matric_number": r.matric_number,
                "student_name": r.student_name,
                "title": r.title,
                "institution_code": r.institution_code or "KWASU",
                "features": feature_vector,
                "risk_label": int(is_at_risk),
                "category": int(category),
                "metrics_summary": {
                    "total_submissions": total_submissions,
                    "days_since_last_submission": days_since,
                    "milestone_completion_rate": round(milestone_completion_rate * 100, 1),
                    "overdue_milestones": overdue_milestones,
                    "chapter_progress_pct": round(chapter_progress * 100, 1),
                },
            })

        return extracted


class ExternalDatabaseConnector:
    """Connects to external institutional databases to ingest legacy or remote cohorts."""

    @staticmethod
    def test_connection(connection_url: str) -> Dict[str, Any]:
        """Tests connectivity to a remote institutional SQL database."""
        try:
            engine = create_engine(connection_url, connect_args={"connect_timeout": 5})
            with engine.connect() as conn:
                res = conn.execute(text("SELECT 1")).scalar()
            return {"connected": True, "message": "Successfully connected to external database."}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    @staticmethod
    def extract_from_external(
        connection_url: str,
        query_sql: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Pulls student records from an external institution database.
        If no custom query is specified, attempts heuristic extraction.
        """
        engine = create_engine(connection_url)
        default_query = query_sql or """
            SELECT
                id AS project_id,
                matric_no AS matric_number,
                submission_count AS total_submissions,
                days_inactive AS days_since_last_submission,
                milestones_done AS completed_milestones,
                milestones_total AS total_milestones,
                overdue_count AS overdue_milestones,
                feedback_delay_days AS supervisor_feedback_days,
                progress_fraction AS chapter_progress,
                is_delayed AS is_at_risk
            FROM student_project_records
            LIMIT 500
        """
        extracted = []
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(default_query)).mappings().all()
                for r in rows:
                    total_subs = float(r.get("total_submissions", 2))
                    days_since = float(r.get("days_since_last_submission", 14))
                    m_done = float(r.get("completed_milestones", 2))
                    m_tot = max(float(r.get("total_milestones", 4)), 1)
                    mcr = m_done / m_tot
                    overdue = int(r.get("overdue_milestones", 0))
                    fb_days = float(r.get("supervisor_feedback_days", 5.0))
                    chapter_p = float(r.get("chapter_progress", 0.5))
                    weeks_el = 10.0
                    sub_rate = total_subs / weeks_el
                    progress_ratio = weeks_el / 20.0
                    z_stag = (days_since - 14.0) / 7.0
                    is_risk = int(r.get("is_at_risk", 0))

                    features = [
                        sub_rate, days_since, mcr, overdue, fb_days,
                        chapter_p, progress_ratio, z_stag, total_subs, 1.0 - chapter_p
                    ]
                    extracted.append({
                        "project_id": r.get("project_id"),
                        "matric_number": r.get("matric_number", "EXT-STUDENT"),
                        "institution_code": "EXTERNAL",
                        "features": features,
                        "risk_label": is_risk,
                        "category": 0 if is_risk else 1,
                    })
        except Exception as e:
            logger.error(f"External database extraction failed: {e}")
            raise
        return extracted


class InstitutionalMLPipeline:
    """Orchestrates live data ingestion, feature formatting, model training, and database logging."""

    @classmethod
    def run_pipeline(
        cls,
        db: Session,
        institution_code: str = "KWASU",
        external_db_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end pipeline:
        1. Query operational DB for live project records.
        2. Query external DB (if configured).
        3. Merge and validate feature matrices.
        4. Send payload to ML service `/pipeline/train-with-live-data`.
        5. Log run history in `ml_pipeline_runs`.
        6. Return execution metrics and performance summary.
        """
        start_time = datetime.utcnow()

        # Step 1: Internal Live Data Extraction
        live_records = InstitutionalDataExtractor.extract_live_records(db)
        total_live = len(live_records)
        all_features = [r["features"] for r in live_records]
        all_labels = [r["risk_label"] for r in live_records]
        all_categories = [r["category"] for r in live_records]
        source_desc = f"Internal Database ({total_live} live project records)"

        # Step 2: Optional External Database Ingestion
        if external_db_url:
            try:
                ext_records = ExternalDatabaseConnector.extract_from_external(external_db_url)
                if ext_records:
                    for er in ext_records:
                        all_features.append(er["features"])
                        all_labels.append(er["risk_label"])
                        all_categories.append(er["category"])
                    source_desc += f" + External Database ({len(ext_records)} external cohort records)"
            except Exception as e:
                logger.warning(f"Could not ingest external database: {e}")

        if not all_features:
            raise ValueError("No student project records available in the database to train on.")

        # Step 3: Dispatch to ML Microservice
        ml_service_url = getattr(settings, "ml_service_url", "http://localhost:8001")
        payload = {
            "institution_code": institution_code,
            "source": source_desc,
            "features": all_features,
            "risk_labels": all_labels,
            "categories": all_categories,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(f"{ml_service_url}/pipeline/train-with-live-data", json=payload)
                res.raise_for_status()
                train_result = res.json()
        except httpx.ConnectError:
            raise RuntimeError(f"ML Microservice offline at {ml_service_url}. Please ensure port 8001 is active.")
        except Exception as e:
            raise RuntimeError(f"ML Microservice training error: {e}")

        # Step 4: Record Execution in Database Audit Table
        xgb_acc = train_result.get("xgboost_metrics", {}).get("accuracy", 0.0)
        xgb_f1 = train_result.get("xgboost_metrics", {}).get("f1", 0.0)
        rf_acc = train_result.get("random_forest_metrics", {}).get("accuracy", 0.0)
        rf_f1 = train_result.get("random_forest_metrics", {}).get("oob_score", 0.0)
        total_samples = train_result.get("total_samples_trained", len(all_features))

        summary_text = (
            f"Trained on {total_live} live institutional records ({total_samples} total). "
            f"XGBoost Acc: {xgb_acc:.1%}, F1: {xgb_f1:.1%}. Random Forest Acc: {rf_acc:.1%}."
        )

        try:
            db.execute(
                text("""
                    INSERT INTO ml_pipeline_runs (
                        institution_code, source_type, samples_extracted,
                        samples_trained, xgb_accuracy, xgb_f1, rf_accuracy,
                        rf_f1, status, summary, executed_at
                    ) VALUES (
                        :inst, :source, :extracted, :trained, :xgb_acc,
                        :xgb_f1, :rf_acc, :rf_f1, 'completed', :summary, :now
                    )
                """),
                {
                    "inst": institution_code,
                    "source": source_desc,
                    "extracted": total_live,
                    "trained": total_samples,
                    "xgb_acc": xgb_acc,
                    "xgb_f1": xgb_f1,
                    "rf_acc": rf_acc,
                    "rf_f1": rf_f1,
                    "summary": summary_text,
                    "now": datetime.utcnow().isoformat(),
                },
            )
            db.commit()
        except Exception as e:
            logger.warning(f"Could not persist pipeline run to DB: {e}")
            db.rollback()

        duration = round((datetime.utcnow() - start_time).total_seconds(), 2)

        return {
            "status": "success",
            "institution_code": institution_code,
            "source": source_desc,
            "samples_extracted": total_live,
            "total_samples_trained": total_samples,
            "execution_time_seconds": duration,
            "xgboost_metrics": train_result.get("xgboost_metrics"),
            "random_forest_metrics": train_result.get("random_forest_metrics"),
            "summary": summary_text,
            "trained_at": datetime.utcnow().isoformat(),
        }

    @classmethod
    def get_pipeline_history(cls, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns recent pipeline execution history from the database."""
        try:
            rows = db.execute(
                text("""
                    SELECT
                        run_id, institution_code, source_type, samples_extracted,
                        samples_trained, xgb_accuracy, xgb_f1, rf_accuracy, rf_f1,
                        status, summary, executed_at
                    FROM ml_pipeline_runs
                    ORDER BY run_id DESC
                    LIMIT :lim
                """),
                {"lim": limit},
            ).fetchall()

            history = []
            for r in rows:
                history.append({
                    "run_id": r.run_id,
                    "institution_code": r.institution_code,
                    "source_type": r.source_type,
                    "samples_extracted": r.samples_extracted,
                    "samples_trained": r.samples_trained,
                    "xgb_accuracy": r.xgb_accuracy,
                    "xgb_f1": r.xgb_f1,
                    "rf_accuracy": r.rf_accuracy,
                    "rf_f1": r.rf_f1,
                    "status": r.status,
                    "summary": r.summary,
                    "executed_at": str(r.executed_at),
                })
            return history
        except Exception as e:
            logger.warning(f"Could not fetch pipeline history: {e}")
            return []

"""
ml-service/main.py
FastAPI ML microservice — port 8001
Endpoints: /health, /predict/risk, /check/duplication,
           /match/supervisors, /evaluate/grade
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, AliasChoices
from typing import List, Dict, Any, Optional
import logging
import os
import time
import numpy as np

from ml_engine import get_xgb, get_rf, get_matcher, get_dup, compute_grade, generate_training_data, MODEL_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_start_time = time.time()

app = FastAPI(title="SPSEMS ML Microservice", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────

class RiskRequest(BaseModel):
    student_id:                          Optional[int] = None
    project_id:                          Optional[int] = None
    days_since_last_submission:          float = Field(default=30)
    total_submissions:                   int   = Field(default=0)
    milestone_completion_rate:           float = Field(default=0.0)
    supervisor_feedback_response_days:   float = Field(default=5.0)
    overdue_milestones:                  int   = Field(default=0)
    chapter_progress:                    float = Field(default=0.0)
    weeks_elapsed:                       float = Field(default=1.0)
    total_weeks:                         float = Field(default=20.0)


class DuplicationRequest(BaseModel):
    title:   str
    archive: List[Dict[str, Any]] = Field(default_factory=list)


class SupervisorEntry(BaseModel):
    id:              Optional[int]  = None
    supervisor_id:   Optional[int]  = None
    name:            Optional[str]  = None
    expertise_areas: Optional[str]  = None
    expertise_vector: Any           = None
    current_load:    int            = 0
    max_load:        int            = 5
    department:      Optional[str]  = None


class MatchRequest(BaseModel):
    student_keywords: List[str]
    supervisors:      List[Dict[str, Any]]


class GradeRequest(BaseModel):
    methodology_score:   float = Field(default=0, ge=0, le=20, validation_alias=AliasChoices("methodology_score", "rubric_methodology"))
    literature_score:    float = Field(default=0, ge=0, le=20, validation_alias=AliasChoices("literature_score", "rubric_literature"))
    analysis_score:      float = Field(default=0, ge=0, le=20, validation_alias=AliasChoices("analysis_score", "rubric_analysis"))
    presentation_score:  float = Field(default=0, ge=0, le=20, validation_alias=AliasChoices("presentation_score", "rubric_presentation"))
    originality_score:   float = Field(default=0, ge=0, le=20, validation_alias=AliasChoices("originality_score", "rubric_originality"))


class LiveDatasetTrainRequest(BaseModel):
    institution_code: Optional[str] = "GLOBAL"
    source:           Optional[str] = "live_database_etl"
    features:         List[List[float]]
    risk_labels:      List[int]
    categories:       Optional[List[int]] = None


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "SPSEMS ML Microservice", "version": "1.0.0"}


@app.get("/metrics")
def get_metrics():
    uptime_seconds = int(time.time() - _start_time)
    hours, rem     = divmod(uptime_seconds, 3600)
    minutes, secs  = divmod(rem, 60)

    xgb_info = get_xgb().get_info()
    rf_info   = get_rf().get_info()

    model_files = []
    if os.path.isdir(MODEL_DIR):
        for fname in os.listdir(MODEL_DIR):
            fpath = os.path.join(MODEL_DIR, fname)
            if os.path.isfile(fpath):
                model_files.append({
                    "file":       fname,
                    "size_kb":    round(os.path.getsize(fpath) / 1024, 1),
                    "modified":   __import__("datetime").datetime.utcfromtimestamp(
                                      os.path.getmtime(fpath)
                                  ).isoformat(),
                })

    return {
        "status":  "ok",
        "uptime":  f"{hours:02d}h {minutes:02d}m {secs:02d}s",
        "uptime_seconds": uptime_seconds,
        "models": {
            "xgboost_risk_predictor": xgb_info,
            "random_forest_classifier": rf_info,
        },
        "algorithms": {
            "supervisor_matching": {
                "name":        "TF-IDF Cosine Similarity + Workload Balancing",
                "description": "Student research keywords are vectorised with TF-IDF (1–2 grams, 500 features). Cosine similarity is computed against each supervisor's expertise vector. Final score = 0.70 × similarity + 0.30 × workload availability.",
                "vectorizer":  {"ngram_range": [1, 2], "max_features": 500, "stop_words": "english", "sublinear_tf": True},
                "weights":     {"cosine_similarity": 0.70, "workload_score": 0.30},
            },
            "duplication_checker": {
                "name":        "TF-IDF Cosine Similarity (Title Comparison)",
                "description": "Project titles are compared against the archive using TF-IDF vectors. A cosine similarity ≥ 0.75 flags a potential duplicate.",
                "threshold":   0.75,
                "vectorizer":  {"ngram_range": [1, 2], "stop_words": "english"},
            },
            "grading_engine": {
                "name":        "Weighted Rubric Grader",
                "description": "Five rubric components each scored out of 20. Grade boundaries: A ≥ 70, B ≥ 60, C ≥ 50, D ≥ 45, F < 45.",
                "rubrics":     ["Methodology", "Literature Review", "Analysis", "Presentation", "Originality"],
                "max_per_rubric": 20,
                "total_max":   100,
                "grade_boundaries": {"A": 70, "B": 60, "C": 50, "D": 45, "F": 0},
            },
        },
        "model_files": sorted(model_files, key=lambda x: x["file"]),
    }


@app.post("/predict/risk")
def predict_risk(body: RiskRequest):
    data = body.model_dump()
    try:
        xgb_result = get_xgb().predict(data)
        rf_result  = get_rf().classify(data)

        xgb_label = xgb_result["xgboost"]["risk_label"]
        label_map  = {"Critical Intervention": "critical", "On Track": "on_track", "Exceeding Expectations": "on_track"}
        rf_label   = label_map.get(rf_result.get("category", "On Track"), "on_track")

        label_priority = {"critical": 2, "at_risk": 1, "on_track": 0}
        final_label    = max([xgb_label, rf_label], key=lambda x: label_priority.get(x, 0))

        return {
            "final_label":               final_label,
            "ensemble_risk_probability": xgb_result["ensemble_risk_probability"],
            "xgboost":                   xgb_result["xgboost"],
            "random_forest":             rf_result,
        }
    except Exception as e:
        logger.error(f"Risk prediction error: {e}")
        return {
            "final_label":               "unknown",
            "ensemble_risk_probability": 0.5,
            "xgboost":                   {"risk_label": "unknown", "risk_probability": 0.5, "confidence": 0.0},
            "random_forest":             {"category": "On Track", "confidence": 0.0},
            "error":                     str(e),
        }


@app.post("/check/duplication")
def check_duplication(body: DuplicationRequest):
    try:
        result = get_dup().check(title=body.title, archive=body.archive)
        return result
    except Exception as e:
        logger.error(f"Duplication check error: {e}")
        return {"duplication_score": 0.0, "is_duplicate": False, "similar_titles": [], "error": str(e)}


@app.post("/match/supervisors")
def match_supervisors(body: MatchRequest):
    try:
        result = get_matcher().match(student_keywords=body.student_keywords, supervisors=body.supervisors)
        return result
    except Exception as e:
        logger.error(f"Supervisor matching error: {e}")
        return {"top_match": None, "matches": [], "error": str(e)}


@app.post("/retrain/{model_name}")
def retrain_model(model_name: str):
    allowed = {"xgboost", "random_forest"}
    if model_name not in allowed:
        raise HTTPException(status_code=400, detail=f"Unknown model. Valid: {', '.join(allowed)}")
    try:
        if model_name == "xgboost":
            metrics = get_xgb().train()
            return {"success": True, "model": "xgboost", "metrics": metrics}
        else:
            metrics = get_rf().train()
            return {"success": True, "model": "random_forest", "metrics": metrics}
    except Exception as e:
        logger.error(f"Retrain error ({model_name}): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/train-with-live-data")
def train_with_live_data(body: LiveDatasetTrainRequest):
    try:
        X = np.array(body.features, dtype=np.float32)
        y_risk = np.array(body.risk_labels, dtype=np.int32)

        if len(X) < 3:
            raise HTTPException(status_code=400, detail="At least 3 student project samples required from database.")

        # If live cohort is smaller than 40, augment with distribution-matched samples so cross-validation stratification holds
        if len(X) < 40:
            synth_needed = max(40 - len(X), 30)
            X_synth, y_synth = generate_training_data(synth_needed)
            X_train = np.vstack([X, X_synth])
            y_risk_train = np.concatenate([y_risk, y_synth])
        else:
            X_train = X
            y_risk_train = y_risk

        xgb_metrics = get_xgb().train(X=X_train, y=y_risk_train)

        # Train Random Forest (3-class)
        if body.categories and len(body.categories) == len(body.features):
            y_rf_live = np.array(body.categories, dtype=np.int32)
        else:
            y_rf_live = np.where(y_risk == 1, 0, 1)

        if len(X) < 40:
            X_rf_synth, y_rf_synth = get_rf()._gen_3class(max(40 - len(X), 30))
            X_rf_train = np.vstack([X, X_rf_synth])
            y_rf_train = np.concatenate([y_rf_live, y_rf_synth])
        else:
            X_rf_train = X
            y_rf_train = y_rf_live

        rf_metrics = get_rf().train(X=X_rf_train, y=y_rf_train)

        return {
            "status": "success",
            "institution_code": body.institution_code,
            "source": body.source,
            "live_samples_count": len(body.features),
            "total_samples_trained": len(X_train),
            "xgboost_metrics": xgb_metrics,
            "random_forest_metrics": rf_metrics,
            "trained_at": __import__("datetime").datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Live data training pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate/grade")
def evaluate_grade(body: GradeRequest):
    try:
        result = compute_grade(
            m=body.methodology_score,
            l=body.literature_score,
            a=body.analysis_score,
            p=body.presentation_score,
            o=body.originality_score,
        )
        return result
    except Exception as e:
        logger.error(f"Grade evaluation error: {e}")
        return {"total_score": 0.0, "grade_letter": "F", "error": str(e)}


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

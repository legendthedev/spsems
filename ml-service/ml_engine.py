"""
ml-service/ml_engine.py
ML models: XGBoost risk predictor, Random Forest classifier,
Cosine Similarity supervisor-student matching.
"""

import numpy as np
import json
import os
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import xgboost as xgb
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# FEATURE EXTRACTION
# Features sent by the backend (direct values)
# ─────────────────────────────────────────────

def features_from_request(data: dict) -> np.ndarray:
    """Convert backend risk-request dict into a feature vector."""
    days_since = float(data.get("days_since_last_submission", 30))
    total_subs = float(data.get("total_submissions", 0))
    mcr        = float(data.get("milestone_completion_rate", 0))
    fb_days    = float(data.get("supervisor_feedback_response_days", 5))
    overdue    = float(data.get("overdue_milestones", 0))
    chapter_p  = float(data.get("chapter_progress", 0))
    weeks_el   = float(data.get("weeks_elapsed", 1))
    total_wks  = float(data.get("total_weeks", 20))

    progress_ratio = weeks_el / max(total_wks, 1)
    sub_rate       = total_subs / max(weeks_el, 1)
    z_stagnation   = (days_since - 14) / 7

    return np.array([
        sub_rate,           # f1: submission rate
        days_since,         # f2: days since last submission
        mcr,                # f3: milestone completion rate
        overdue,            # f4: overdue milestone count
        fb_days,            # f5: feedback response days
        chapter_p,          # f6: chapter progress 0-1
        progress_ratio,     # f7: time elapsed / total time
        z_stagnation,       # f8: stagnation z-score
        total_subs,         # f9: total submissions
        1 - chapter_p,      # f10: chapters remaining
    ], dtype=np.float32)


# ─────────────────────────────────────────────
# SYNTHETIC TRAINING DATA
# ─────────────────────────────────────────────

def generate_training_data(n: int = 1000):
    np.random.seed(42)
    X, y = [], []
    for _ in range(n):
        at_risk = np.random.random() < 0.40
        if at_risk:
            sub_rate      = np.random.uniform(0, 0.5)
            days_since    = np.random.uniform(15, 60)
            mcr           = np.random.uniform(0, 0.4)
            overdue       = np.random.randint(1, 5)
            fb_days       = np.random.uniform(8, 20)
            chapter_p     = np.random.uniform(0, 0.4)
            progress_ratio= np.random.uniform(0.5, 1.0)
            z_stag        = np.random.uniform(0.5, 5.0)
            total_subs    = np.random.randint(0, 3)
        else:
            sub_rate      = np.random.uniform(0.5, 3.0)
            days_since    = np.random.uniform(0, 14)
            mcr           = np.random.uniform(0.4, 1.0)
            overdue       = np.random.randint(0, 2)
            fb_days       = np.random.uniform(1, 7)
            chapter_p     = np.random.uniform(0.4, 1.0)
            progress_ratio= np.random.uniform(0.1, 0.8)
            z_stag        = np.random.uniform(-2.0, 0.5)
            total_subs    = np.random.randint(2, 10)

        noise = np.random.normal(0, 0.03, 10)
        feat  = np.array([
            sub_rate, days_since, mcr, overdue, fb_days,
            chapter_p, progress_ratio, z_stag, total_subs, 1 - chapter_p,
        ]) + noise
        X.append(feat)
        y.append(1 if at_risk else 0)
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


# ─────────────────────────────────────────────
# XGBOOST RISK PREDICTOR
# ─────────────────────────────────────────────

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


class XGBoostRiskPredictor:
    def __init__(self):
        self.model        = None
        self.scaler       = StandardScaler()
        self.model_path   = os.path.join(MODEL_DIR, "xgboost_risk.json")
        self.scaler_path  = os.path.join(MODEL_DIR, "xgboost_scaler.pkl")
        self.metrics_path = os.path.join(MODEL_DIR, "xgboost_metrics.json")
        self.metrics      = {}

    def train(self, X=None, y=None):
        if X is None or y is None:
            X, y = generate_training_data(1200)
        X_sc = self.scaler.fit_transform(X)
        X_tr, X_te, y_tr, y_te = train_test_split(X_sc, y, test_size=0.2, random_state=42, stratify=y)

        self.model = xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0, min_child_weight=5, gamma=0.1,
            eval_metric="logloss", random_state=42, scale_pos_weight=1.5,
        )
        self.model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

        y_pred = self.model.predict(X_te)
        self.metrics = {
            "accuracy":        float(accuracy_score(y_te, y_pred)),
            "f1":              float(f1_score(y_te, y_pred)),
            "train_samples":   len(X_tr),
            "test_samples":    len(X_te),
            "n_features":      X.shape[1],
            "trained_at":      __import__("datetime").datetime.utcnow().isoformat(),
        }
        logger.info(f"XGBoost trained — Acc: {self.metrics['accuracy']:.3f}, F1: {self.metrics['f1']:.3f}")
        self.save()
        return self.metrics

    def predict(self, data: dict) -> dict:
        if self.model is None:
            self.load()
        features = features_from_request(data)
        fs       = self.scaler.transform(features.reshape(1, -1))
        prob     = float(self.model.predict_proba(fs)[0][1])
        if prob >= 0.65:   label = "critical"
        elif prob >= 0.35: label = "at_risk"
        else:              label = "on_track"
        return {
            "final_label":               label,
            "ensemble_risk_probability": round(prob, 4),
            "xgboost": {
                "risk_probability": round(prob, 4),
                "risk_label":       label,
                "confidence":       round(abs(prob - 0.5) * 2, 4),
            },
        }

    def save(self):
        if self.model:
            self.model.save_model(self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
        if self.metrics:
            with open(self.metrics_path, "w") as f:
                json.dump(self.metrics, f)

    def load(self):
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = xgb.XGBClassifier()
            self.model.load_model(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            if os.path.exists(self.metrics_path):
                with open(self.metrics_path) as f:
                    self.metrics = json.load(f)
        else:
            logger.info("No saved XGBoost model — training fresh")
            self.train()

    def get_info(self) -> dict:
        params = {}
        if self.model:
            p = self.model.get_params()
            params = {k: p.get(k) for k in ("n_estimators", "max_depth", "learning_rate", "subsample", "colsample_bytree", "reg_alpha", "reg_lambda", "min_child_weight", "gamma")}
        return {
            "name":          "XGBoost Risk Predictor",
            "type":          "Gradient Boosting (Binary Classification)",
            "task":          "Student risk prediction: on_track / at_risk / critical",
            "loaded":        self.model is not None,
            "model_file_kb": round(os.path.getsize(self.model_path) / 1024, 1) if os.path.exists(self.model_path) else None,
            "hyperparams":   params,
            "features":      FEATURE_NAMES,
            "thresholds":    {"critical": "prob >= 0.65", "at_risk": "prob >= 0.35", "on_track": "prob < 0.35"},
            "metrics":       self.metrics,
        }


# ─────────────────────────────────────────────
# RANDOM FOREST CLASSIFIER
# ─────────────────────────────────────────────

class RandomForestModel:
    LABELS = {0: "Critical Intervention", 1: "On Track", 2: "Exceeding Expectations"}

    def __init__(self):
        self.model        = None
        self.scaler       = StandardScaler()
        self.model_path   = os.path.join(MODEL_DIR, "rf_classifier.pkl")
        self.scaler_path  = os.path.join(MODEL_DIR, "rf_scaler.pkl")
        self.metrics_path = os.path.join(MODEL_DIR, "rf_metrics.json")
        self.metrics      = {}

    def _gen_3class(self, n=900):
        np.random.seed(123)
        X, y = [], []
        for _ in range(n):
            cls = np.random.choice([0, 1, 2], p=[0.25, 0.50, 0.25])
            if cls == 0:
                f = [np.random.uniform(0,.3), np.random.uniform(20,60), np.random.uniform(0,.4),
                     np.random.randint(2,5), np.random.uniform(8,20), np.random.uniform(0,.3),
                     np.random.uniform(0.5,1.0), np.random.uniform(1,5), np.random.randint(0,3), np.random.uniform(0.6,1.0)]
            elif cls == 1:
                f = [np.random.uniform(.5,2), np.random.uniform(3,14), np.random.uniform(.4,.7),
                     np.random.randint(0,2), np.random.uniform(2,7), np.random.uniform(.4,.7),
                     np.random.uniform(0.2,0.7), np.random.uniform(-1,.5), np.random.randint(2,7), np.random.uniform(0.3,0.6)]
            else:
                f = [np.random.uniform(2,4), np.random.uniform(0,7), np.random.uniform(.7,1),
                     0, np.random.uniform(1,3), np.random.uniform(.7,1),
                     np.random.uniform(0.1,0.5), np.random.uniform(-3,-1), np.random.randint(5,12), np.random.uniform(0.0,0.3)]
            X.append(np.array(f) + np.random.normal(0, 0.03, 10))
            y.append(cls)
        return np.array(X, dtype=np.float32), np.array(y)

    def train(self, X=None, y=None):
        if X is None or y is None:
            X, y = self._gen_3class()
        X_sc = self.scaler.fit_transform(X)
        X_tr, X_te, y_tr, y_te = train_test_split(X_sc, y, test_size=0.2, random_state=42, stratify=y)
        self.model = RandomForestClassifier(
            n_estimators=300, max_depth=8, max_features="sqrt",
            min_samples_leaf=4, min_samples_split=10,
            bootstrap=True, oob_score=True, class_weight="balanced",
            random_state=42, n_jobs=-1,
        )
        self.model.fit(X_tr, y_tr)
        y_pred = self.model.predict(X_te)
        self.metrics = {
            "accuracy":      float(accuracy_score(y_te, y_pred)),
            "oob_score":     float(self.model.oob_score_),
            "train_samples": len(X_tr),
            "test_samples":  len(X_te),
            "n_features":    X.shape[1],
            "trained_at":    __import__("datetime").datetime.utcnow().isoformat(),
        }
        logger.info(f"RF trained — Acc: {self.metrics['accuracy']:.3f}, OOB: {self.metrics['oob_score']:.3f}")
        self.save()
        return self.metrics

    def classify(self, data: dict) -> dict:
        if self.model is None:
            self.load()
        features = features_from_request(data)
        fs       = self.scaler.transform(features.reshape(1, -1))
        cls      = int(self.model.predict(fs)[0])
        proba    = self.model.predict_proba(fs)[0]
        return {
            "category":    self.LABELS[cls],
            "category_code": cls,
            "confidence":  round(float(proba[cls]), 4),
            "probabilities": {self.LABELS[i]: round(float(p), 4) for i, p in enumerate(proba)},
        }

    def save(self):
        if self.model:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
        if self.metrics:
            with open(self.metrics_path, "w") as f:
                json.dump(self.metrics, f)

    def load(self):
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model  = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            if os.path.exists(self.metrics_path):
                with open(self.metrics_path) as f:
                    self.metrics = json.load(f)
        else:
            self.train()

    def get_info(self) -> dict:
        params = {}
        if self.model:
            p = self.model.get_params()
            params = {k: p.get(k) for k in ("n_estimators", "max_depth", "max_features", "min_samples_leaf", "min_samples_split", "oob_score", "class_weight")}
        feat_imp = {}
        if self.model and hasattr(self.model, "feature_importances_"):
            feat_imp = {FEATURE_NAMES[i]: round(float(v), 4) for i, v in enumerate(self.model.feature_importances_)}
            feat_imp = dict(sorted(feat_imp.items(), key=lambda x: x[1], reverse=True))
        return {
            "name":              "Random Forest Classifier",
            "type":              "Random Forest (3-class Classification)",
            "task":              "Student performance classification",
            "loaded":            self.model is not None,
            "model_file_kb":     round(os.path.getsize(self.model_path) / 1024, 1) if os.path.exists(self.model_path) else None,
            "hyperparams":       params,
            "features":          FEATURE_NAMES,
            "classes":           list(self.LABELS.values()),
            "feature_importances": feat_imp,
            "metrics":           self.metrics,
        }


# ─────────────────────────────────────────────
# COSINE SIMILARITY MATCHING
# ─────────────────────────────────────────────

class SupervisorMatcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), max_features=500, stop_words="english", sublinear_tf=True
        )

    def match(self, student_keywords: list, supervisors: list) -> dict:
        if not supervisors:
            return {"top_match": None, "matches": []}

        student_text   = " ".join(student_keywords)
        supervisor_texts = []
        for sup in supervisors:
            ev = sup.get("expertise_vector") or sup.get("expertise_areas") or ""
            if isinstance(ev, list):
                ev = " ".join(ev)
            elif isinstance(ev, str):
                try:
                    import json as _json
                    parsed = _json.loads(ev)
                    ev = " ".join(parsed) if isinstance(parsed, list) else ev
                except Exception:
                    pass
            supervisor_texts.append(ev)

        all_texts = [student_text] + supervisor_texts
        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
        except Exception:
            # Vocabulary too small — fallback to keyword overlap
            results = []
            for sup in supervisors:
                ev     = set((sup.get("expertise_vector") or []))
                stu_kw = set(student_keywords)
                score  = len(ev & stu_kw) / max(len(ev | stu_kw), 1)
                results.append({**sup, "cosine_similarity": round(score, 4)})
            results.sort(key=lambda x: x["cosine_similarity"], reverse=True)
            return {"top_match": results[0] if results else None, "matches": results[:5]}

        student_vec    = tfidf_matrix[0]
        supervisor_vecs = tfidf_matrix[1:]
        similarities   = cosine_similarity(student_vec, supervisor_vecs)[0]

        results = []
        for i, sup in enumerate(supervisors):
            cl = sup.get("current_load", 0)
            ml = sup.get("max_load", 5)
            if cl >= ml:
                continue
            workload_score = 1 - (cl / ml)
            final_score    = 0.7 * float(similarities[i]) + 0.3 * workload_score
            results.append({
                **sup,
                "cosine_similarity": round(float(similarities[i]), 4),
                "workload_score":    round(workload_score, 4),
                "final_score":       round(final_score, 4),
            })

        results.sort(key=lambda x: x["final_score"], reverse=True)
        return {"top_match": results[0] if results else None, "matches": results[:5]}


# ─────────────────────────────────────────────
# DUPLICATION CHECKER
# ─────────────────────────────────────────────

class DuplicationChecker:
    THRESHOLD = 0.75

    def check(self, title: str, archive: list) -> dict:
        if not archive:
            return {"duplication_score": 0.0, "is_duplicate": False, "similar_titles": []}

        titles = [title] + [a.get("title", "") for a in archive]
        try:
            vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform(titles)
            sims = cosine_similarity(vec[0], vec[1:])[0]
        except Exception:
            sims = np.zeros(len(archive))

        max_score = float(np.max(sims)) if len(sims) > 0 else 0.0
        similar   = [
            {"id": archive[i].get("id"), "title": archive[i].get("title"), "score": round(float(sims[i]), 4)}
            for i in np.argsort(sims)[::-1][:3]
            if sims[i] > 0.3
        ]
        return {
            "duplication_score": round(max_score, 4),
            "is_duplicate":      max_score >= self.THRESHOLD,
            "similar_titles":    similar,
        }


# ─────────────────────────────────────────────
# GRADE CALCULATOR
# ─────────────────────────────────────────────

def compute_grade(m, l, a, p, o) -> dict:
    total = m + l + a + p + o
    if   total >= 70: letter = "A"
    elif total >= 60: letter = "B"
    elif total >= 50: letter = "C"
    elif total >= 45: letter = "D"
    else:             letter = "F"
    return {"total_score": round(total, 2), "grade_letter": letter}


# ─────────────────────────────────────────────
# SINGLETONS
# ─────────────────────────────────────────────

_xgb     = None
_rf      = None
_matcher = None
_dup     = None


def get_xgb():
    global _xgb
    if _xgb is None:
        _xgb = XGBoostRiskPredictor()
        _xgb.load()
    return _xgb

def get_rf():
    global _rf
    if _rf is None:
        _rf = RandomForestModel()
        _rf.load()
    return _rf

def get_matcher():
    global _matcher
    if _matcher is None:
        _matcher = SupervisorMatcher()
    return _matcher

def get_dup():
    global _dup
    if _dup is None:
        _dup = DuplicationChecker()
    return _dup

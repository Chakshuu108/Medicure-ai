"""
Health Intelligence Agent
─────────────────────────
Aggregates patient data, runs an ML-based risk-prediction pipeline
(XGBoost-style gradient boosting via scikit-learn, with LSTM-inspired
sequential feature engineering), and generates narrative clinical
insights via GROQ.

Architecture
  1. DataAggregator   – pulls & cleans all patient signals from the DB
  2. FeatureEngineer  – derives temporal & summary features from raw data
  3. RiskPredictor    – GradientBoostingClassifier (sklearn) trained on
                        in-memory synthetic priors + live patient features
  4. NarrativeEngine  – GROQ LLM narrative summary for the doctor
  5. HealthIntelligenceAgent (public API) – orchestrates 1-4
"""

import json
import math
import requests
import numpy as np
from datetime import date, datetime, timedelta
from collections import defaultdict

from data.database import (
    get_patient,
    get_patients_by_doctor,
    get_patient_prescriptions,
    get_all_medicines_for_patient,
    get_mcq_responses,
    get_chat_history,
    get_patient_alerts,
)
from core.config import GROQ_API_KEY, GROQ_MODEL


# ── Utility ───────────────────────────────────────────────────────────────────

def _safe_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ══════════════════════════════════════════════════════════════════════════════
# 1. Data Aggregator
# ══════════════════════════════════════════════════════════════════════════════

class DataAggregator:
    """Pulls and cleans all signals for a single patient."""

    def aggregate(self, patient_id: str) -> dict:
        patient     = get_patient(patient_id) or {}
        mcq_rows    = get_mcq_responses(patient_id, limit=30)
        medicines   = get_all_medicines_for_patient(patient_id)
        chat        = get_chat_history(patient_id, limit=20)
        alerts_raw  = get_patient_alerts(patient_id)
        alerts      = alerts_raw if alerts_raw else []

        # ── Parse MCQ responses ───────────────────────────────────────────
        parsed_mcq = []
        for row in mcq_rows:
            try:
                responses = json.loads(row.get("responses_json", "[]"))
            except Exception:
                responses = []
            parsed_mcq.append({
                "date":             row.get("date", ""),
                "total_score":      _safe_float(row.get("total_score", 0)),
                "status":           row.get("status", "Stable"),
                "adherence_status": row.get("adherence_status", ""),
                "side_effects":     json.loads(row.get("side_effects", "[]") or "[]"),
                "responses":        responses,
            })

        # ── Medication timeline ───────────────────────────────────────────
        today = date.today()
        active_meds, expired_meds = [], []
        for m in medicines:
            try:
                start = datetime.fromisoformat(m.get("start_date", today.isoformat())).date()
            except Exception:
                start = today
            elapsed = (today - start).days
            duration = int(m.get("duration_days", 7))
            if elapsed <= duration:
                active_meds.append(m)
            else:
                expired_meds.append(m)

        # ── Side-effect frequency ─────────────────────────────────────────
        all_effects: list = []
        for row in parsed_mcq:
            all_effects.extend(row["side_effects"])
        effect_freq: dict = defaultdict(int)
        for e in all_effects:
            effect_freq[str(e)] += 1

        # ── Chat sentiment signals ────────────────────────────────────────
        concern_kw     = ["worse","pain","fever","vomiting","dizzy","chest",
                          "breathing","severe","emergency","bleeding","swelling"]
        improvement_kw = ["better","improving","feeling good","recovered","well","normal","great"]
        user_msgs = [h["content"].lower() for h in chat if h.get("role") == "user"]
        concern_hits     = sum(1 for m in user_msgs for k in concern_kw     if k in m)
        improvement_hits = sum(1 for m in user_msgs for k in improvement_kw if k in m)

        return {
            "patient":          patient,
            "mcq_rows":         parsed_mcq,           # newest-first
            "active_meds":      active_meds,
            "expired_meds":     expired_meds,
            "effect_freq":      dict(effect_freq),
            "concern_hits":     concern_hits,
            "improvement_hits": improvement_hits,
            "alerts":           alerts,
            "raw_chat":         chat,
        }


# ══════════════════════════════════════════════════════════════════════════════
# 2. Feature Engineer
# ══════════════════════════════════════════════════════════════════════════════

class FeatureEngineer:
    """
    Derives a fixed-length feature vector from aggregated data.
    Also builds timeline arrays for graphing.
    """

    # status → numeric
    STATUS_MAP = {"Improving": 1, "Stable": 0, "Worsening": -1}

    def build_features(self, agg: dict) -> dict:
        patient  = agg["patient"]
        mcq_rows = agg["mcq_rows"]   # newest-first

        # ── Scalar demographics ───────────────────────────────────────────
        age          = _safe_float(patient.get("age", 35))
        age_norm     = _clamp(age / 80.0, 0, 1)
        gender_enc   = {"Male": 0.4, "Female": 0.5, "Other": 0.5}.get(
                            patient.get("gender", "Other"), 0.5)

        # ── MCQ-based sequential features ────────────────────────────────
        n_rows       = len(mcq_rows)
        scores       = [r["total_score"] for r in mcq_rows]          # newest-first
        statuses_enc = [self.STATUS_MAP.get(r["status"], 0) for r in mcq_rows]

        # recent window (last 7 entries)
        recent_scores  = scores[:7]
        recent_status  = statuses_enc[:7]

        avg_score_7    = np.mean(recent_scores)   if recent_scores else 0.0
        std_score_7    = np.std(recent_scores)    if len(recent_scores) > 1 else 0.0
        avg_status_7   = np.mean(recent_status)   if recent_status else 0.0

        # slope (linear trend over last 7 days) — negative = worsening
        slope_7 = 0.0
        if len(recent_scores) >= 3:
            x = np.arange(len(recent_scores), dtype=float)
            slope_7 = float(np.polyfit(x, recent_scores, 1)[0])

        # consecutive worsening count
        consec_worse = 0
        for s in statuses_enc:
            if s == -1:
                consec_worse += 1
            else:
                break

        # adherence hit rate
        adherence_scores = []
        for r in mcq_rows[:14]:
            adh = (r.get("adherence_status") or "").lower()
            if "full" in adh or "taken" in adh or "yes" in adh:
                adherence_scores.append(1)
            elif "partial" in adh or "some" in adh:
                adherence_scores.append(0.5)
            elif "miss" in adh or "no " in adh or adh == "no":
                adherence_scores.append(0)
        adherence_rate = np.mean(adherence_scores) if adherence_scores else 0.5

        # side-effect burden
        total_effects  = sum(agg["effect_freq"].values())
        effect_burden  = _clamp(total_effects / max(n_rows, 1) / 3.0, 0, 1)

        # chat sentiment ratio
        total_hits = agg["concern_hits"] + agg["improvement_hits"] + 1
        concern_ratio = _clamp(agg["concern_hits"] / total_hits, 0, 1)

        # medication load
        med_load = _clamp(len(agg["active_meds"]) / 10.0, 0, 1)

        # unresolved alert count
        unresolved_alerts = sum(1 for a in agg["alerts"] if not a.get("resolved"))
        alert_burden = _clamp(unresolved_alerts / 5.0, 0, 1)

        feature_vector = np.array([
            age_norm,           # 0
            gender_enc,         # 1
            _clamp((avg_score_7 + 20) / 40.0, 0, 1),  # 2  normalised score
            _clamp(std_score_7 / 10.0, 0, 1),           # 3
            _clamp((avg_status_7 + 1) / 2.0, 0, 1),     # 4
            _clamp((slope_7 + 5) / 10.0, 0, 1),         # 5  slope
            _clamp(consec_worse / 5.0, 0, 1),            # 6
            adherence_rate,     # 7
            effect_burden,      # 8
            concern_ratio,      # 9
            med_load,           # 10
            alert_burden,       # 11
            _clamp(n_rows / 30.0, 0, 1),  # 12  data richness
        ], dtype=np.float32)

        # ── Timeline arrays for graphing (oldest→newest) ──────────────────
        timeline_mcq = list(reversed(mcq_rows))
        dates_list   = [r["date"] for r in timeline_mcq]
        scores_list  = [r["total_score"] for r in timeline_mcq]
        status_list  = [r["status"] for r in timeline_mcq]
        adh_list     = []
        for r in timeline_mcq:
            adh = (r.get("adherence_status") or "").lower()
            if "full" in adh or "taken" in adh or "yes" in adh:
                adh_list.append(1.0)
            elif "partial" in adh or "some" in adh:
                adh_list.append(0.5)
            elif "miss" in adh or "no" in adh:
                adh_list.append(0.0)
            else:
                adh_list.append(0.7)  # unknown → assume partial

        return {
            "vector":          feature_vector,
            "dates":           dates_list,
            "scores":          scores_list,
            "status_list":     status_list,
            "adherence_list":  adh_list,
            "slope_7":         slope_7,
            "consec_worse":    consec_worse,
            "adherence_rate":  adherence_rate,
            "effect_burden":   effect_burden,
            "concern_ratio":   concern_ratio,
            "avg_score_7":     avg_score_7,
            "n_observations":  n_rows,
        }


# ══════════════════════════════════════════════════════════════════════════════
# 3. Risk Predictor  (Gradient Boosting via sklearn)
# ══════════════════════════════════════════════════════════════════════════════

class RiskPredictor:
    """
    Uses a GradientBoostingClassifier trained on synthetic priors that
    encode clinical domain knowledge.  At runtime, the live patient
    feature vector is predicted to Low / Medium / High with a probability
    distribution that drives the risk score (0-100).

    Synthetic training data: 300 samples generated from gaussian
    distributions around prototypical Low / Medium / High patients.
    This avoids any external dataset dependency.
    """

    LABELS = {0: "Low", 1: "Medium", 2: "High"}

    def __init__(self):
        self._model = None
        self._build_model()

    def _build_model(self):
        try:
            from sklearn.ensemble import GradientBoostingClassifier
        except ImportError:
            self._model = None
            return

        rng = np.random.default_rng(42)

        # Prototype centroids for 13 features
        # [age, gender, norm_score, std_score, avg_status, slope, consec_worse,
        #  adherence, effect_burden, concern_ratio, med_load, alert_burden, data_richness]
        low_center    = [0.35, 0.45, 0.75, 0.05, 0.80, 0.55, 0.0,  0.95, 0.05, 0.1,  0.2, 0.0,  0.8]
        medium_center = [0.50, 0.45, 0.50, 0.15, 0.50, 0.45, 0.2,  0.65, 0.25, 0.35, 0.4, 0.2,  0.5]
        high_center   = [0.70, 0.45, 0.20, 0.30, 0.10, 0.25, 0.6,  0.25, 0.60, 0.70, 0.7, 0.60, 0.3]

        X, y = [], []
        for label, center, n in [(0, low_center, 120), (1, medium_center, 100), (2, high_center, 80)]:
            noise = rng.normal(0, 0.08, (n, len(center)))
            samples = np.clip(np.array(center) + noise, 0, 1)
            X.append(samples)
            y.extend([label] * n)

        X_arr = np.vstack(X).astype(np.float32)
        y_arr = np.array(y, dtype=int)

        self._model = GradientBoostingClassifier(
            n_estimators=120, learning_rate=0.08,
            max_depth=4, subsample=0.85, random_state=42
        )
        self._model.fit(X_arr, y_arr)

    def predict(self, feature_vector: np.ndarray) -> dict:
        x = feature_vector.reshape(1, -1)

        if self._model is None:
            # Fallback: simple weighted sum heuristic
            weights = np.array([0.08, 0.00, -0.20, 0.08, -0.15, -0.12,
                                  0.18, -0.20, 0.12, 0.15, 0.06, 0.14, -0.05])
            raw = float(np.dot(weights, feature_vector.flatten())) + 0.5
            prob_high = _clamp(raw, 0, 1)
            prob_low  = _clamp(1 - raw - 0.1, 0, 1)
            prob_med  = _clamp(1 - prob_high - prob_low, 0, 1)
        else:
            probs = self._model.predict_proba(x)[0]
            prob_low, prob_med, prob_high = probs[0], probs[1], probs[2]

        score = int(round(prob_low * 20 + prob_med * 55 + prob_high * 90))
        score = _clamp(score, 0, 100)

        if score >= 65:
            level = "High"
        elif score >= 35:
            level = "Medium"
        else:
            level = "Low"

        return {
            "score":    score,
            "level":    level,
            "prob_low":  float(prob_low),
            "prob_med":  float(prob_med),
            "prob_high": float(prob_high),
        }

    def predict_trajectory(self, feature_vector: np.ndarray, horizon: int = 7) -> list:
        """
        Project risk score for the next `horizon` days using a simple
        exponential smoothing model on the current feature state.
        Returns list of (date_str, predicted_score).
        """
        base = self.predict(feature_vector)["score"]
        slope_feat = float(feature_vector[5])   # normalised slope
        consec_feat = float(feature_vector[6])  # normalised consecutive worse

        # direction: negative slope + high consec_worse → rising risk
        daily_delta = (0.5 - slope_feat) * 4.0 + consec_feat * 3.0

        trajectory = []
        for i in range(1, horizon + 1):
            day = date.today() + timedelta(days=i)
            projected = _clamp(base + daily_delta * i, 0, 100)
            trajectory.append((day.isoformat(), round(projected)))
        return trajectory


# ══════════════════════════════════════════════════════════════════════════════
# 4. Narrative Engine
# ══════════════════════════════════════════════════════════════════════════════

class NarrativeEngine:
    """Calls GROQ to produce a doctor-facing narrative clinical insight."""

    def __init__(self):
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

    def generate(self, patient: dict, features: dict, prediction: dict,
                 agg: dict) -> str:
        mcq_rows = agg["mcq_rows"]
        recent_statuses = [r["status"] for r in mcq_rows[:5]]
        recent_scores   = [r["total_score"] for r in mcq_rows[:5]]
        top_effects     = sorted(agg["effect_freq"].items(),
                                 key=lambda x: -x[1])[:3]

        prompt = f"""You are a senior clinical decision-support AI. Write a concise narrative for the treating physician.

PATIENT: {patient.get('name','N/A')}, Age {patient.get('age','N/A')}, Gender {patient.get('gender','N/A')}, Diagnosis: {patient.get('disease','N/A')}

PREDICTIVE RISK MODEL OUTPUT:
  • Risk Score: {prediction['score']}/100
  • Risk Category: {prediction['level']}
  • Probability breakdown → Low: {prediction['prob_low']:.0%}, Medium: {prediction['prob_med']:.0%}, High: {prediction['prob_high']:.0%}

RECENT MCQ DATA (last 5 check-ins):
  • Statuses: {', '.join(recent_statuses) if recent_statuses else 'No data'}
  • Scores:   {recent_scores}
  • Adherence rate (14-day): {features['adherence_rate']:.0%}
  • 7-day score trend slope: {'+' if features['slope_7'] >= 0 else ''}{features['slope_7']:.2f} (positive = improving)
  • Consecutive worsening days: {features['consec_worse']}

SIDE EFFECTS: {', '.join(f"{e}×{n}" for e,n in top_effects) if top_effects else 'None reported'}
CHAT CONCERN SIGNALS: {agg['concern_hits']} concern mentions, {agg['improvement_hits']} improvement mentions
ACTIVE MEDICATIONS: {len(agg['active_meds'])}

Write 3-4 sentences covering:
1. Current clinical picture
2. Key risk drivers
3. Recommended physician action (e.g., medication review, urgent follow-up, continue monitoring)
Be clinical, specific, and actionable. Do NOT repeat the numbers verbatim — synthesise them."""

        try:
            r = requests.post(
                self.url, headers=self.headers,
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a concise clinical decision-support AI. Respond in 3-4 sentences only."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 300,
                    "temperature": 0.25,
                },
                timeout=15,
            )
            data = r.json()
            choices = data.get("choices") or []
            if choices:
                return (choices[0].get("message") or {}).get("content", "").strip()
        except Exception:
            pass

        # Fallback narrative
        level = prediction["level"]
        adh   = f"{features['adherence_rate']:.0%}"
        trend_word = "improving" if features["slope_7"] > 0 else ("worsening" if features["slope_7"] < -1 else "stable")
        return (
            f"{patient.get('name','This patient')} presents with a {level.lower()} risk profile "
            f"(score {prediction['score']}/100) for their {patient.get('disease','condition')}. "
            f"Adherence over the past 14 days stands at {adh} with a {trend_word} score trajectory. "
            f"{'Consecutive worsening entries warrant prompt clinical review.' if features['consec_worse'] >= 2 else 'Continue current monitoring protocol.'}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 5. Public API — HealthIntelligenceAgent
# ══════════════════════════════════════════════════════════════════════════════

class HealthIntelligenceAgent:
    """
    Orchestrates the full pipeline for a single patient or a doctor's
    entire patient panel.
    """

    def __init__(self):
        self.aggregator  = DataAggregator()
        self.engineer    = FeatureEngineer()
        self.predictor   = RiskPredictor()
        self.narrator    = NarrativeEngine()

    # ── Single patient ────────────────────────────────────────────────────────
    def analyse_patient(self, patient_id: str, generate_narrative: bool = True) -> dict:
        """Full analysis for one patient. Returns a rich result dict."""
        agg      = self.aggregator.aggregate(patient_id)
        features = self.engineer.build_features(agg)
        pred     = self.predictor.predict(features["vector"])
        traj     = self.predictor.predict_trajectory(features["vector"])

        narrative = ""
        if generate_narrative and agg["mcq_rows"]:
            narrative = self.narrator.generate(
                agg["patient"], features, pred, agg
            )

        return {
            "patient":    agg["patient"],
            "prediction": pred,
            "features":   features,
            "trajectory": traj,
            "narrative":  narrative,
            "agg":        agg,
        }

    # ── Doctor panel overview ─────────────────────────────────────────────────
    def analyse_panel(self, doctor_id: str) -> list:
        """
        Lightweight analysis for all patients under a doctor.
        Skips full narrative to stay fast; returns list sorted by risk score desc.
        """
        patients = get_patients_by_doctor(doctor_id)
        results  = []
        for p in patients:
            pid = p.get("id") or p.get("patient_id", "")
            if not pid:
                continue
            try:
                agg      = self.aggregator.aggregate(pid)
                features = self.engineer.build_features(agg)
                pred     = self.predictor.predict(features["vector"])
                results.append({
                    "patient_id":   pid,
                    "name":         p.get("name", ""),
                    "disease":      p.get("disease", ""),
                    "age":          p.get("age", ""),
                    "risk_score":   pred["score"],
                    "risk_level":   pred["level"],
                    "adherence_rate": features["adherence_rate"],
                    "slope_7":      features["slope_7"],
                    "consec_worse": features["consec_worse"],
                    "n_checkins":   features["n_observations"],
                })
            except Exception:
                results.append({
                    "patient_id": pid,
                    "name":       p.get("name", ""),
                    "disease":    p.get("disease", ""),
                    "age":        p.get("age", ""),
                    "risk_score": int(p.get("risk_score") or 20),
                    "risk_level": p.get("risk_level") or "Low",
                    "adherence_rate": 0.5,
                    "slope_7":    0.0,
                    "consec_worse": 0,
                    "n_checkins": 0,
                })

        results.sort(key=lambda x: -x["risk_score"])
        return results

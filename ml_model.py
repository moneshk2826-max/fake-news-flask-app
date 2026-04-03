import csv
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
VECTORIZER_PATH = BASE_DIR / "vectorizer.pkl"
DATASET_PATH = BASE_DIR / "fake_news_dataset.csv"

SENSATIONAL_PHRASES = {
    "you won't believe": 0.35,
    "you wont believe": 0.35,
    "shocking": 0.22,
    "breaking": 0.16,
    "scientists discover": 0.18,
    "secret": 0.22,
    "secretly": 0.22,
    "miracle": 0.25,
    "conspiracy": 0.28,
    "exposed": 0.22,
    "bombshell": 0.22,
    "hoax": 0.20,
    "scam": 0.22,
    "banned": 0.14,
    "urgent": 0.14,
    "viral": 0.12,
    "must see": 0.12,
    "earth will go dark": 0.35,
    "go dark": 0.22,
    "cure": 0.18,
    "they don't want you to know": 0.35,
    "they dont want you to know": 0.35,
    "what they're not telling you": 0.30,
    "what theyre not telling you": 0.30,
    "big pharma": 0.28,
    "deep state": 0.30,
    "wake up": 0.18,
    "open your eyes": 0.22,
    "the truth about": 0.18,
    "exposed the truth": 0.25,
    "caught on camera": 0.18,
    "spread this before": 0.30,
    "share before deleted": 0.35,
    "media won't show": 0.30,
    "media wont show": 0.30,
    "100% proof": 0.30,
    "exposed by": 0.20,
    "illuminati": 0.30,
    "flat earth": 0.35,
    "chemtrails": 0.30,
    "5g causes": 0.30,
    "microchip": 0.22,
    "mark of the beast": 0.28,
    "depopulation": 0.28,
}

SUSPICIOUS_CLAIM_PATTERNS = {
    r"\bsecret documents?\b": "Secret-document framing detected",
    r"\bleaked documents?\b": "Leaked-document framing detected",
    r"\b(prove|proves|proved)\b": "Headline claims definitive proof without context",
    r"\b(faked|fabricated|staged|rigged)\b": "Manipulation allegation detected",
    r"\bcover[\s-]?up\b": "Cover-up allegation detected",
    r"\bhidden truth\b": "Hidden-truth framing detected",
    r"\bmainstream media\b": "Media conspiracy framing detected",
    r"\b(exposed|reveals?)\s+(the\s+)?truth\b": "Truth-revelation framing detected",
    r"\bwhat\s+(they|the\s+government|the\s+media)\s+(don'?t|won'?t|aren'?t)\b": "Suppression narrative detected",
    r"\b(exposed|caught)\s+(red[\s-]?handed|lying|cheating)\b": "Accusation-without-evidence framing detected",
    r"\b(exposed|unmasked|busted)\b": "Unmasking framing detected",
    r"\bdoctors?\s+(don'?t|won'?t|refuse)\b": "Anti-medical-authority framing detected",
    r"\b(exposed|leaked)\s+(emails?|footage|video|audio)\b": "Leaked-media framing detected",
}

model = None
vectorizer = None
dataset_title_lookup = None
_ml_modules = None
_ml_error = None
_ml_load_attempted = False


def _normalize_text(text):
    return re.sub(r"\s+", " ", str(text or "").strip()).strip("\"'")


def preprocess_text(text):
    """Lowercase and remove punctuation for cleaner TF-IDF input."""
    try:
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        return text
    except Exception:
        return text


def _normalize_lookup_text(text):
    return _normalize_text(text).strip("\"'").lower()


def _load_dataset_title_lookup():
    global dataset_title_lookup

    if dataset_title_lookup is not None:
        return dataset_title_lookup

    dataset_title_lookup = {}

    try:
        with DATASET_PATH.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                title = _normalize_lookup_text(row.get("title", ""))
                label = str(row.get("label", "")).strip().lower()
                if title and label in {"fake", "real"} and title not in dataset_title_lookup:
                    dataset_title_lookup[title] = label
    except Exception:
        dataset_title_lookup = {}

    return dataset_title_lookup


def _combine_fields(frame):
    frame = frame.copy()
    frame["title"] = frame["title"].fillna("")
    frame["text"] = frame["text"].fillna("")
    return frame["title"] + " " + frame["text"]


def _headline_heuristics(text):
    lowered = text.lower()
    tokens = re.findall(r"[a-z']+", lowered)
    risk_factors = []
    score = 0.0

    matched_phrases = [phrase for phrase in SENSATIONAL_PHRASES if phrase in lowered]
    if matched_phrases:
        score += min(0.70, sum(SENSATIONAL_PHRASES[phrase] for phrase in matched_phrases))
        risk_factors.append("Sensational or clickbait wording detected")
        if len(matched_phrases) >= 2:
            score += 0.15
            risk_factors.append("Multiple sensational trigger phrases stacked together")
        if len(matched_phrases) >= 3:
            score += 0.15
            risk_factors.append("Heavy concentration of fake-news trigger language")

    matched_claim_patterns = []
    for pattern, message in SUSPICIOUS_CLAIM_PATTERNS.items():
        if re.search(pattern, lowered):
            matched_claim_patterns.append(message)

    if matched_claim_patterns:
        score += min(0.32, 0.12 * len(matched_claim_patterns))
        risk_factors.extend(matched_claim_patterns)
        if len(matched_claim_patterns) >= 2:
            score += 0.15
            risk_factors.append("Several unverified allegation patterns detected together")

    if re.search(r"\b(secret|leaked) documents?\b", lowered) and re.search(
        r"\b(prove|proves|proved|faked|fabricated|staged|rigged|cover[\s-]?up)\b",
        lowered,
    ):
        score += 0.28
        risk_factors.append("Explosive allegation pattern detected")

    if re.search(r"\b(government|media|scientists|doctors|officials?)\b", lowered) and re.search(
        r"\b(faked|fabricated|lied|lying|cover[\s-]?up|hid|hidden)\b",
        lowered,
    ):
        score += 0.18
        risk_factors.append("Institution-targeted accusation without supporting context")

    if "!" in text or "?" in text:
        punctuation_hits = text.count("!") + text.count("?")
        if punctuation_hits >= 2:
            score += 0.08
            risk_factors.append("Heavy punctuation used to create urgency")

    uppercase_tokens = [word for word in re.findall(r"\b[A-Z]{3,}\b", text) if word.isalpha()]
    if len(uppercase_tokens) >= 2:
        score += 0.08
        risk_factors.append("Multiple all-caps words detected")

    if len(tokens) >= 18:
        unique_ratio = len(set(tokens)) / max(len(tokens), 1)
        if unique_ratio > 0.82 and not re.search(r"[,:;!?]", text):
            score += 0.20
            risk_factors.append("Headline looks unnatural or machine-generated")

    if re.search(r"\b(always|never|everyone|nobody|all|none)\b", lowered):
        score += 0.08
        risk_factors.append("Absolute claim language detected")

    if len(risk_factors) >= 3:
        score += 0.12

    return min(score, 1.0), risk_factors


def _get_ml_modules():
    global _ml_modules, _ml_error

    if _ml_modules is not None:
        return _ml_modules
    if _ml_error is not None:
        return None

    try:
        import joblib  # type: ignore
        import pandas as pd  # type: ignore
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
        from sklearn.linear_model import LogisticRegression  # type: ignore
        from sklearn.metrics import accuracy_score  # type: ignore
        from sklearn.model_selection import train_test_split  # type: ignore
    except Exception as exc:
        _ml_error = f"{exc.__class__.__name__}: {exc}"
        return None

    _ml_modules = {
        "joblib": joblib,
        "pd": pd,
        "TfidfVectorizer": TfidfVectorizer,
        "LogisticRegression": LogisticRegression,
        "accuracy_score": accuracy_score,
        "train_test_split": train_test_split,
    }
    return _ml_modules


def train_and_save_model():
    ml = _get_ml_modules()
    if ml is None:
        raise RuntimeError(f"ML dependencies are unavailable: {_ml_error}")

    df = ml["pd"].read_csv(DATASET_PATH)
    df = df[["title", "text", "label"]]

    X = _combine_fields(df)
    y = df["label"].astype(str).str.strip().str.lower()

    X_train, X_test, y_train, y_test = ml["train_test_split"](
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    trained_vectorizer = ml["TfidfVectorizer"](
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        max_features=30000,
    )

    X_train_vec = trained_vectorizer.fit_transform(X_train)
    X_test_vec = trained_vectorizer.transform(X_test)

    trained_model = ml["LogisticRegression"](max_iter=2000, class_weight="balanced")
    trained_model.fit(X_train_vec, y_train)

    y_pred = trained_model.predict(X_test_vec)
    accuracy = ml["accuracy_score"](y_test, y_pred)

    print("Model trained successfully")
    print("Accuracy:", accuracy)

    ml["joblib"].dump(trained_model, MODEL_PATH)
    ml["joblib"].dump(trained_vectorizer, VECTORIZER_PATH)

    print("Model and vectorizer saved")
    return trained_model, trained_vectorizer


def load_model_and_vectorizer():
    ml = _get_ml_modules()
    if ml is None:
        raise RuntimeError(f"ML dependencies are unavailable: {_ml_error}")

    if not MODEL_PATH.exists() or not VECTORIZER_PATH.exists():
        return train_and_save_model()

    try:
        loaded_model = ml["joblib"].load(MODEL_PATH)
        loaded_vectorizer = ml["joblib"].load(VECTORIZER_PATH)
        return loaded_model, loaded_vectorizer
    except Exception as exc:
        raise RuntimeError(f"Saved model could not be loaded: {exc}") from exc


def get_model_and_vectorizer():
    global model, vectorizer, _ml_error, _ml_load_attempted

    if model is not None and vectorizer is not None:
        return model, vectorizer
    if _ml_load_attempted and _ml_error is not None:
        return None, None

    _ml_load_attempted = True
    try:
        model, vectorizer = load_model_and_vectorizer()
    except Exception as exc:
        _ml_error = str(exc)
        model = None
        vectorizer = None

    return model, vectorizer


def _build_heuristic_response(score, risk_factors, normalized_text, ml_reason=None):
    if score >= 0.55:
        result = "Fake News"
        confidence = max(65.0, min(98.0, score * 100.0))
    elif score >= 0.28:
        result = "Suspicious"
        confidence = max(55.0, min(90.0, score * 100.0 + 10.0))
    else:
        result = "Real News"
        confidence = max(55.0, min(95.0, (1.0 - score) * 100.0))

    method = "Heuristic Analysis"
    details_parts = [f"Heuristic risk score: {score * 100.0:.2f}%."]

    if ml_reason:
        method = "Heuristic Analysis (ML Unavailable)"
        details_parts.append(f"ML model not used: {ml_reason}.")
    elif score <= 0.18 and normalized_text:
        details_parts.append("No strong fake-news markers were detected.")

    return {
        "result": result,
        "confidence": float(f"{confidence:.2f}"),
        "method": method,
        "details": " ".join(details_parts),
        "risk_factors": risk_factors or ["No strong fake-news markers detected"],
    }


def _build_dataset_match_response(label):
    if label == "fake":
        result = "Fake News"
        risk_factors = ["Exact headline match found in dataset with fake label"]
    else:
        result = "Real News"
        risk_factors = ["Exact headline match found in dataset with real label"]

    return {
        "result": result,
        "confidence": 100.0,
        "method": "Dataset Match",
        "details": f"Exact headline match found in dataset. Stored label: {label}.",
        "risk_factors": risk_factors,
    }


def _find_dataset_match_label(text):
    lookup_text = _normalize_lookup_text(text)
    dataset_lookup = _load_dataset_title_lookup()
    matched_label = dataset_lookup.get(lookup_text)

    if matched_label in {"fake", "real"}:
        return matched_label

    for title, label in dataset_lookup.items():
        if lookup_text.startswith(f"{title},"):
            return label

    return None


def detect(text):
    normalized_text = _normalize_text(text)
    if not normalized_text:
        return {
            "result": "Unknown",
            "confidence": 0,
            "method": "Heuristic Analysis",
            "details": "Empty input text provided.",
            "risk_factors": ["No text entered"],
        }

    matched_label = _find_dataset_match_label(normalized_text)
    if matched_label in {"fake", "real"}:
        return _build_dataset_match_response(matched_label)

    heuristic_score, risk_factors = _headline_heuristics(normalized_text)

    model_instance, vectorizer_instance = get_model_and_vectorizer()
    if model_instance is None or vectorizer_instance is None:
        return _build_heuristic_response(
            heuristic_score,
            risk_factors,
            normalized_text,
            ml_reason=_ml_error or "model unavailable",
        )

    try:
        clean_text = preprocess_text(normalized_text)
    except Exception:
        clean_text = normalized_text

    text_vector = vectorizer_instance.transform([clean_text])

    fake_probability = 0.5
    real_probability = 0.5
    try:
        probabilities = model_instance.predict_proba(text_vector)[0]
        class_names = [str(label).strip().lower() for label in model_instance.classes_]
        if "fake" in class_names:
            fake_probability = float(probabilities[class_names.index("fake")])
        if "real" in class_names:
            real_probability = float(probabilities[class_names.index("real")])
    except Exception as exc:
        return _build_heuristic_response(
            heuristic_score,
            risk_factors,
            normalized_text,
            ml_reason=f"prediction failed: {exc}",
        )

    combined_fake_score = (fake_probability * 0.5) + (heuristic_score * 0.5)

    if heuristic_score >= 0.55 or combined_fake_score >= 0.45:
        result = "Fake News"
        confidence = max(fake_probability, heuristic_score, combined_fake_score) * 100.0
        if heuristic_score > fake_probability:
            message = "Headline pattern risk outweighed the ML real score"
            if message not in risk_factors:
                risk_factors.append(message)
    elif combined_fake_score >= 0.30 or heuristic_score >= 0.28:
        result = "Suspicious"
        confidence = max(50.0, combined_fake_score * 100.0)
        message = "Mixed ML and headline pattern signals detected"
        if message not in risk_factors:
            risk_factors.append(message)
    else:
        result = "Real News"
        confidence = max(real_probability, (1.0 - combined_fake_score)) * 100.0

    details = (
        f"Combined fake score: {combined_fake_score * 100.0:.2f}%. "
        f"ML fake probability: {fake_probability * 100.0:.2f}%. "
        f"ML real probability: {real_probability * 100.0:.2f}%. "
        f"Heuristic risk score: {heuristic_score * 100.0:.2f}%."
    )

    return {
        "result": result,
        "confidence": float(f"{confidence:.2f}"),
        "method": "Hybrid ML + Heuristics",
        "details": details,
        "risk_factors": risk_factors or ["No strong fake-news markers detected"],
    }


if __name__ == "__main__":
    train_and_save_model()

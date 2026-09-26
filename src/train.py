import pandas as pd
import joblib
import mlflow
import mlflow.sklearn

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)


# 1. Load dataset
df = pd.read_csv("data/lifepass_documents.csv")

print("Dataset loaded successfully")
print("Total records:", len(df))
print("\nClass distribution:")
print(df["label"].value_counts())


# 2. Split data
X_train, X_test, y_train, y_test = train_test_split(
    df["text"],
    df["label"],
    test_size=0.25,
    random_state=42,
    stratify=df["label"]
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# 3. Create ML pipeline
model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2)
    )),
    ("classifier", LogisticRegression(
        max_iter=1000
    ))
])


# 4. Start MLflow experiment
mlflow.set_experiment("LifePass_Document_Classification")

with mlflow.start_run():

    # 5. Train
    model.fit(X_train, y_train)

    # 6. Predict
    y_pred = model.predict(X_test)

    # 7. Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(
        y_test, y_pred, average="weighted", zero_division=0
    )
    recall = recall_score(
        y_test, y_pred, average="weighted", zero_division=0
    )
    f1 = f1_score(
        y_test, y_pred, average="weighted", zero_division=0
    )

    print("\n===== MODEL RESULTS =====")
    print("Accuracy :", round(accuracy, 4))
    print("Precision:", round(precision, 4))
    print("Recall   :", round(recall, 4))
    print("F1 Score :", round(f1, 4))

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # 8. Log parameters
    mlflow.log_param("model", "Logistic Regression")
    mlflow.log_param("vectorizer", "TF-IDF")
    mlflow.log_param("ngram_range", "(1,2)")
    mlflow.log_param("test_size", 0.25)

    # 9. Log metrics
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("precision", precision)
    mlflow.log_metric("recall", recall)
    mlflow.log_metric("f1_score", f1)

    # 10. Save model
    joblib.dump(
        model,
        "models/lifepass_classifier.joblib"
    )

    # 11. Log model to MLflow
    mlflow.sklearn.log_model(
        model,
        "lifepass_classifier",
        registered_model_name="LifePass_Document_Classifier"
    )

print("\nModel saved successfully!")
print("Location: models/lifepass_classifier.joblib")
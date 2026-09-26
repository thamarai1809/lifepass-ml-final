import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# Load dataset
df = pd.read_csv("data/lifepass_documents.csv")

# Load trained model
model = joblib.load("models/lifepass_classifier.joblib")

# Same split used during training
X_train, X_test, y_train, y_test = train_test_split(
    df["text"],
    df["label"],
    test_size=0.25,
    random_state=42,
    stratify=df["label"]
)

# Predictions
y_pred = model.predict(X_test)

# Metrics
accuracy = accuracy_score(y_test, y_pred)

precision = precision_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

print("\n========== EVALUATION ==========")

print("Accuracy :", round(accuracy, 4))
print("Precision:", round(precision, 4))
print("Recall   :", round(recall, 4))
print("F1 Score :", round(f1, 4))

print("\n========== CLASSIFICATION REPORT ==========")

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)

# Confusion Matrix
labels = sorted(df["label"].unique())

cm = confusion_matrix(
    y_test,
    y_pred,
    labels=labels
)

print("\n========== CONFUSION MATRIX ==========")

print("Labels:", labels)
print(cm)

# Error analysis
print("\n========== ERROR ANALYSIS ==========")

errors = 0

for text, actual, predicted in zip(
    X_test,
    y_test,
    y_pred
):

    if actual != predicted:

        errors += 1

        print("\nText:", text)
        print("Actual    :", actual)
        print("Predicted :", predicted)

if errors == 0:
    print("No classification errors found on the test set.")

print("\nTotal errors:", errors)
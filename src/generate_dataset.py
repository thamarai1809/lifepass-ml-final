import pandas as pd
import random

random.seed(42)

templates = {
    "insurance": [
        "Vehicle insurance policy premium and coverage details",
        "Motor insurance policy document",
        "Car insurance policy issued by the insurer",
        "Insurance policy number and coverage information",
        "Vehicle insurance renewal document",
        "Motor vehicle insurance certificate",
        "Insurance premium payment details",
        "Comprehensive vehicle insurance policy",
        "Third party vehicle insurance document",
        "Insurance policy validity and expiry details",
        "Vehicle insurance coverage certificate",
        "Insurance claim and policy information",
        "Automobile insurance policy document",
        "Insurance provider policy certificate",
        "Vehicle policy renewal information",
    ],

    "driving_license": [
        "Driving licence issued by transport department",
        "Driving license document",
        "Motor vehicle driving licence",
        "Driving licence number and validity details",
        "Driving licence issued by regional transport office",
        "Learner driving licence document",
        "Permanent driving licence information",
        "Driving licence renewal document",
        "Transport department driving licence",
        "Driving licence validity and expiry date",
        "Motorist driving licence information",
        "Driving licence holder details",
        "Vehicle driver licence document",
        "Driving licence identification document",
        "Regional transport authority licence",
    ],

    "passport": [
        "Passport issued by the passport authority",
        "Indian passport document",
        "Passport identification information",
        "Passport number and validity details",
        "Passport renewal document",
        "International travel passport",
        "Passport holder information",
        "Passport expiry and issue date",
        "Government passport document",
        "Passport identification page",
        "Travel passport document",
        "Passport authority issued document",
        "Passport validity information",
        "Passport application document",
        "Passport personal identification details",
    ],

    "certificate": [
        "University degree certificate",
        "Educational certificate document",
        "Graduation certificate issued by university",
        "Course completion certificate",
        "Academic qualification certificate",
        "Higher secondary certificate",
        "Bachelor degree certificate",
        "Training completion certificate",
        "Professional certification document",
        "University academic certificate",
        "Education qualification document",
        "Certificate of course completion",
        "Academic achievement certificate",
        "College degree certificate",
        "Educational qualification document",
    ]
}


rows = []

for label, base_templates in templates.items():

    for i in range(50):

        text = random.choice(base_templates)

        # Add small variations
        variations = [
            "",
            " with validity information",
            " including important dates",
            " containing identification details",
            " with issue and expiry information",
            " for document verification",
            " with holder information",
            " containing document number",
        ]

        text += random.choice(variations)

        rows.append({
            "text": text,
            "label": label
        })


random.shuffle(rows)

df = pd.DataFrame(rows)

output_path = "data/lifepass_documents.csv"

df.to_csv(output_path, index=False)

print("Dataset generated successfully!")
print("Total records:", len(df))
print("\nClass distribution:")
print(df["label"].value_counts())

print("\nSaved to:")
print(output_path)
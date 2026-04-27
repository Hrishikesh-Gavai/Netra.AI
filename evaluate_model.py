import os
import numpy as np
import logging
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import load_model
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
DATASET_PATH = "dataset"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
CATEGORIES = ["cataract", "diabetic_retinopathy", "glaucoma", "normal"]

# Load your existing model (NO retraining!)
MODEL_PATH = "models/eye_disease_model.h5"
logging.info(f"Loading model from {MODEL_PATH}...")
model = load_model(MODEL_PATH)
logging.info("Model loaded successfully!")

# Load validation data
logging.info("Loading validation data...")
datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)

val_data = datagen.flow_from_directory(
    DATASET_PATH, 
    target_size=IMG_SIZE, 
    batch_size=BATCH_SIZE,
    class_mode='categorical', 
    subset="validation",
    shuffle=False  # Important for correct evaluation
)

# Make predictions
logging.info("Making predictions on validation data...")
predictions = model.predict(val_data)
y_pred = np.argmax(predictions, axis=1)
y_true = val_data.classes

# Calculate metrics
accuracy = accuracy_score(y_true, y_pred)
error_rate = 1 - accuracy

# Confusion Matrix
cm = confusion_matrix(y_true, y_pred)

# Calculate TP, FP, TN, FN for each class
print("\n" + "="*70)
print("DETAILED EVALUATION METRICS")
print("="*70)

for i, category in enumerate(CATEGORIES):
    TP = cm[i, i]
    FP = cm[:, i].sum() - TP
    FN = cm[i, :].sum() - TP
    TN = cm.sum() - (TP + FP + FN)
    
    print(f"\n📊 {category.upper()}:")
    print(f"   True Positives (TP): {TP}")
    print(f"   False Positives (FP): {FP}")
    print(f"   False Negatives (FN): {FN}")
    print(f"   True Negatives (TN): {TN}")

# Overall metrics
print("\n" + "="*70)
print("OVERALL METRICS")
print("="*70)
print(f"✅ Accuracy: {accuracy*100:.2f}%")
print(f"❌ Error Rate: {error_rate*100:.2f}%")

# Per class metrics
precision_per_class = precision_score(y_true, y_pred, average=None)
recall_per_class = recall_score(y_true, y_pred, average=None)
f1_per_class = f1_score(y_true, y_pred, average=None)

print("\n" + "="*70)
print("PER CLASS METRICS")
print("="*70)
for i, category in enumerate(CATEGORIES):
    print(f"\n{category.upper()}:")
    print(f"   Precision: {precision_per_class[i]*100:.2f}%")
    print(f"   Recall: {recall_per_class[i]*100:.2f}%")
    print(f"   F1-Score: {f1_per_class[i]*100:.2f}%")

# Weighted averages
print("\n" + "="*70)
print("WEIGHTED AVERAGES")
print("="*70)
print(f"📈 Weighted Precision: {precision_score(y_true, y_pred, average='weighted')*100:.2f}%")
print(f"📈 Weighted Recall: {recall_score(y_true, y_pred, average='weighted')*100:.2f}%")
print(f"📈 Weighted F1-Score: {f1_score(y_true, y_pred, average='weighted')*100:.2f}%")

# Macro averages
print(f"\n📊 Macro Precision: {precision_score(y_true, y_pred, average='macro')*100:.2f}%")
print(f"📊 Macro Recall: {recall_score(y_true, y_pred, average='macro')*100:.2f}%")
print(f"📊 Macro F1-Score: {f1_score(y_true, y_pred, average='macro')*100:.2f}%")

# Full classification report
print("\n" + "="*70)
print("CLASSIFICATION REPORT")
print("="*70)
print(classification_report(y_true, y_pred, target_names=CATEGORIES))

# Visualize Confusion Matrix
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=CATEGORIES, yticklabels=CATEGORIES)
plt.title('Confusion Matrix', fontsize=16, fontweight='bold')
plt.ylabel('True Label', fontsize=12)
plt.xlabel('Predicted Label', fontsize=12)
plt.tight_layout()
plt.show()

# Bar chart of metrics
fig, ax = plt.subplots(1, 2, figsize=(14, 5))

# Precision, Recall, F1-Score by class
x = np.arange(len(CATEGORIES))
width = 0.25

ax[0].bar(x - width, precision_per_class, width, label='Precision', color='skyblue')
ax[0].bar(x, recall_per_class, width, label='Recall', color='lightgreen')
ax[0].bar(x + width, f1_per_class, width, label='F1-Score', color='salmon')
ax[0].set_xlabel('Diseases')
ax[0].set_ylabel('Score')
ax[0].set_title('Per Class Metrics')
ax[0].set_xticks(x)
ax[0].set_xticklabels(CATEGORIES, rotation=45)
ax[0].legend()
ax[0].set_ylim(0, 1)

# Accuracy vs Error Rate
ax[1].bar(['Accuracy', 'Error Rate'], [accuracy, error_rate], 
          color=['green', 'red'], alpha=0.7)
ax[1].set_ylabel('Rate')
ax[1].set_title('Overall Performance')
ax[1].set_ylim(0, 1)
for i, v in enumerate([accuracy, error_rate]):
    ax[1].text(i, v + 0.02, f'{v*100:.1f}%', ha='center', fontweight='bold')

plt.tight_layout()
plt.show()

# Save metrics to CSV
metrics_data = {
    'Class': CATEGORIES,
    'Precision (%)': [p*100 for p in precision_per_class],
    'Recall (%)': [r*100 for r in recall_per_class],
    'F1-Score (%)': [f*100 for f in f1_per_class]
}
df = pd.DataFrame(metrics_data)
print("\n" + "="*70)
print("METRICS SUMMARY TABLE")
print("="*70)
print(df.to_string(index=False))

# Save to CSV file
df.to_csv('model_evaluation_metrics.csv', index=False)
print("\n✅ Metrics saved to 'model_evaluation_metrics.csv'")

logging.info("Evaluation complete!")
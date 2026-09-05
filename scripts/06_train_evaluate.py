"""
Step 6 â€” Fine-tune IndicBERT and Evaluate
==========================================
Loads data/final/train.csv, val.csv, and test.csv.
Fine-tunes ai4bharat/indic-bert with a 5-class classification head.
Tracks accuracy + macro-F1 per epoch on validation set.
Saves best checkpoint, tokenizer, and label_encoder.json to models/final/.
Runs full evaluation on test set and saves eval_report.json.

Usage:
    python scripts/06_train_evaluate.py [--epochs 5] [--batch-size 16]
                                        [--max-length 128] [--lr 2e-5]
                                        [--device auto|cpu|cuda]

    --device auto   : use CUDA if available, else CPU (default)
    --device cpu    : force CPU
    --device cuda   : force CUDA (will error if unavailable)

Output:
    models/checkpoints/   â† per-epoch checkpoints
    models/final/         â† best model + tokenizer + label_encoder.json + eval_report.json
"""

import os
import sys
import json
import math
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINAL_DIR = os.path.join(PROJECT_ROOT, "data", "final")
CKPT_DIR = os.path.join(PROJECT_ROOT, "models", "checkpoints")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models", "final")
MODEL_NAME = "ai4bharat/indic-bert"

LABEL_LIST = ["angry", "neutral", "happy", "sad", "fear"]
LABEL2ID = {l: i for i, l in enumerate(LABEL_LIST)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--epochs",      type=int,   default=5)
    p.add_argument("--batch-size",  type=int,   default=16)
    p.add_argument("--max-length",  type=int,   default=128)
    p.add_argument("--lr",          type=float, default=2e-5)
    p.add_argument("--device",      type=str,   default="auto",
                   choices=["auto", "cpu", "cuda"])
    return p.parse_args()


def resolve_device(pref: str):
    import torch
    if pref == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return pref


def load_split(name: str) -> pd.DataFrame:
    path = os.path.join(FINAL_DIR, f"{name}.csv")
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Run step 5 first.", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(path)
    df = df.dropna(subset=["text", "sentiment"])
    df = df[df["sentiment"].isin(LABEL_LIST)]
    return df


def encode_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["label"] = df["sentiment"].map(LABEL2ID)
    return df


def build_hf_dataset(df: pd.DataFrame, tokenizer, max_length: int):
    from datasets import Dataset as HFDataset

    dataset = HFDataset.from_pandas(df[["text", "label"]].reset_index(drop=True))

    def tokenize_fn(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            padding="max_length",
            max_length=max_length,
        )

    dataset = dataset.map(tokenize_fn, batched=True)
    dataset = dataset.rename_column("label", "labels")
    dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])
    return dataset


def compute_metrics_fn(eval_pred):
    from sklearn.metrics import accuracy_score, f1_score
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, preds)
    macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
    return {"accuracy": acc, "macro_f1": macro_f1}


def build_eval_report(trainer, test_df: pd.DataFrame,
                      test_dataset, tokenizer) -> dict:
    """Run inference on test set and build the full eval report."""
    from sklearn.metrics import (accuracy_score, f1_score,
                                 classification_report, confusion_matrix)

    preds_out = trainer.predict(test_dataset)
    preds = np.argmax(preds_out.predictions, axis=-1)
    labels = preds_out.label_ids

    overall_acc = float(accuracy_score(labels, preds))
    overall_f1 = float(f1_score(labels, preds, average="macro", zero_division=0))

    # Full sklearn classification report (per-class)
    cls_report = classification_report(
        labels, preds,
        target_names=LABEL_LIST,
        output_dict=True, zero_division=0
    )

    # Per-language breakdown
    test_df = test_df.reset_index(drop=True)
    test_df["pred_label"] = [ID2LABEL[p] for p in preds]
    per_lang = {}
    for lang in sorted(test_df["language"].unique()):
        sub = test_df[test_df["language"] == lang]
        sub_true = sub["sentiment"].map(LABEL2ID).values
        sub_pred = sub["pred_label"].map(LABEL2ID).values
        per_lang[lang] = {
            "n_samples": len(sub),
            "accuracy": float(accuracy_score(sub_true, sub_pred)),
            "macro_f1": float(f1_score(sub_true, sub_pred,
                                       average="macro", zero_division=0)),
            "classification_report": classification_report(
                sub_true, sub_pred,
                target_names=LABEL_LIST,
                output_dict=True, zero_division=0
            ),
        }

    # Confusion matrix
    cm = confusion_matrix(labels, preds).tolist()

    report = {
        "model": MODEL_NAME,
        "label_list": LABEL_LIST,
        "overall": {
            "accuracy": overall_acc,
            "macro_f1": overall_f1,
        },
        "per_class": cls_report,
        "per_language": per_lang,
        "confusion_matrix": {
            "labels": LABEL_LIST,
            "matrix": cm,
        },
    }
    return report


def main():
    args = parse_args()

    import torch
    from transformers import (
        AutoTokenizer, AutoModelForSequenceClassification,
        TrainingArguments, Trainer
    )

    device = resolve_device(args.device)
    print("=" * 60)
    print("Step 6 â€” Fine-tune IndicBERT")
    print("=" * 60)
    print(f"Model:      {MODEL_NAME}")
    print(f"Device:     {device}  (torch.cuda.is_available={torch.cuda.is_available()})")
    print(f"Epochs:     {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"Max length: {args.max_length}")
    print(f"LR:         {args.lr}")

    os.makedirs(CKPT_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)

    # -- Load data
    print("\nLoading splits...")
    train_df = encode_labels(load_split("train"))
    val_df   = encode_labels(load_split("val"))
    test_df  = encode_labels(load_split("test"))
    print(f"  Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    # -- Save label encoder
    label_encoder_path = os.path.join(MODEL_DIR, "label_encoder.json")
    with open(label_encoder_path, "w", encoding="utf-8") as f:
        json.dump({"label2id": LABEL2ID, "id2label": ID2LABEL}, f, indent=2)
    print(f"Saved label_encoder.json -> {label_encoder_path}")

    # -- Tokenizer
    print(f"\nLoading tokenizer: {MODEL_NAME} ...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # -- Tokenize datasets
    print("Tokenizing datasets...")
    train_ds = build_hf_dataset(train_df, tokenizer, args.max_length)
    val_ds   = build_hf_dataset(val_df,   tokenizer, args.max_length)
    test_ds  = build_hf_dataset(test_df,  tokenizer, args.max_length)

    # -- Model
    print(f"\nLoading model: {MODEL_NAME} ...")
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(LABEL_LIST),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    # Compute warmup_steps as ~10% of total training steps
    steps_per_epoch = math.ceil(len(train_df) / args.batch_size)
    total_steps = steps_per_epoch * args.epochs
    warmup_steps = max(1, total_steps // 10)
    print(f"  steps_per_epoch={steps_per_epoch}, total_steps={total_steps}, warmup_steps={warmup_steps}")

    # -- Training arguments (using only kwargs confirmed valid in transformers 5.x)
    training_args = TrainingArguments(
        output_dir=CKPT_DIR,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size * 2,
        learning_rate=args.lr,
        warmup_steps=warmup_steps,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_macro_f1",
        greater_is_better=True,
        logging_steps=50,
        save_total_limit=2,
        fp16=True,
        bf16=False,
        report_to="none",
        dataloader_num_workers=2,
        use_cpu=(device == "cpu"),
    )

    # -- Trainer (transformers 5.x: tokenizer → processing_class)
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        processing_class=tokenizer,
        compute_metrics=compute_metrics_fn,
    )

    # -- Train
    print("\nStarting training...")
    trainer.train()

    # -- Save best model + tokenizer
    print(f"\nSaving best model to {MODEL_DIR} ...")
    trainer.save_model(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    print("Model and tokenizer saved. âœ“")

    # -- Evaluate on test set
    print("\nRunning evaluation on test set...")
    report = build_eval_report(trainer, test_df, test_ds, tokenizer)

    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SET RESULTS")
    print(f"{'='*60}")
    print(f"  Overall Accuracy : {report['overall']['accuracy']:.4f}")
    print(f"  Overall Macro-F1 : {report['overall']['macro_f1']:.4f}")
    print(f"\nPer-language breakdown:")
    for lang, stats in report["per_language"].items():
        print(f"  [{lang}] acc={stats['accuracy']:.3f}  macro_f1={stats['macro_f1']:.3f}  n={stats['n_samples']}")

    # Save eval report
    eval_report_path = os.path.join(MODEL_DIR, "eval_report.json")
    with open(eval_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nEval report saved -> {eval_report_path}")
    print("\nTraining and evaluation complete. âœ“")


if __name__ == "__main__":
    main()


"""
Modelo preditivo de RISCO DE DEFASAGEM (early-warning) - Passos Magicos.

O enunciado pede identificar alunos em risco "ANTES de queda no desempenho ou
AUMENTO da defasagem" e estimar "a probabilidade do aluno ENTRAR em risco".
Trata-se, portanto, de uma tarefa PREDITIVA/LONGITUDINAL: usamos os indicadores
do ano atual (t) para prever a DETERIORACAO no ano seguinte (t+1).

Alvo (target): risco_piora = 1 se a defasagem PIORA no ano seguinte
    (defasagem_{t+1} < defasagem_t), 0 caso contrario.
    -> Como prevemos a MUDANCA (nao o nivel), idade/fase/IAN/INDE deixam de ser
       vazamento: sao o estado atual, legitimamente conhecido no momento da
       predicao, e ajudam a antecipar a piora.

Universo: registros aluno-ano que possuem observacao no ano seguinte (chave RA).

Etapas (exigidas pelo enunciado):
    1. Feature engineering (construcao do alvo longitudinal via RA)
    2. Separacao treino/teste (estratificada)
    3. Modelagem (Regressao Logistica x Random Forest x Gradient Boosting)
    4. Avaliacao (ROC-AUC, PR-AUC, matriz de confusao, importancias)
    5. Persistencia do melhor pipeline em models/modelo_risco.joblib

Uso:
    python src/modelo.py
"""
from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    roc_auc_score, average_precision_score, roc_curve,
    classification_report, confusion_matrix, ConfusionMatrixDisplay,
)

warnings.filterwarnings("ignore")
BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "processed" / "pede_unificado.csv"
MODELS = BASE / "models"; MODELS.mkdir(exist_ok=True)
FIG = BASE / "reports" / "figures"; FIG.mkdir(parents=True, exist_ok=True)

# Features: estado ATUAL do aluno (indicadores + demografia + defasagem atual).
# Como o alvo e a MUDANCA futura da defasagem, usar o nivel atual nao e vazamento.
NUM_FEATS = ["inde", "ida", "ieg", "iaa", "ips", "ipp", "ipv", "ian",
             "idade", "fase", "defasagem", "anos_na_pm"]
CAT_FEATS = ["genero"]
FEATURES = NUM_FEATS + CAT_FEATS
TARGET = "risco_piora"
RANDOM_STATE = 42


def carrega_dados():
    """Monta o alvo longitudinal: piora da defasagem no ano seguinte (via RA)."""
    df = pd.read_csv(DATA).sort_values(["RA", "ano"]).copy()
    df["defasagem_prox"] = df.groupby("RA")["defasagem"].shift(-1)
    # So consideramos registros com observacao no ano seguinte
    df = df[df["defasagem_prox"].notna()].copy()
    df[TARGET] = (df["defasagem_prox"] < df["defasagem"]).astype(int)
    X = df[FEATURES].copy()
    y = df[TARGET].copy()
    return df, X, y


def build_preprocessor():
    num = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())])
    cat = Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                    ("oh", OneHotEncoder(handle_unknown="ignore"))])
    return ColumnTransformer([("num", num, NUM_FEATS), ("cat", cat, CAT_FEATS)])


def candidatos():
    return {
        "Regressao Logistica": LogisticRegression(max_iter=1000, class_weight="balanced",
                                                  random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(n_estimators=400, max_depth=6,
                                                min_samples_leaf=8, class_weight="balanced",
                                                random_state=RANDOM_STATE, n_jobs=-1),
        "Gradient Boosting": HistGradientBoostingClassifier(
            max_depth=3, learning_rate=0.05, max_iter=300,
            class_weight="balanced", random_state=RANDOM_STATE),
    }


def melhor_limiar(y_true, proba):
    """Escolhe o limiar que maximiza o F1 (relevante sob desbalanceamento)."""
    from sklearn.metrics import f1_score
    grid = np.linspace(0.1, 0.9, 81)
    f1s = [f1_score(y_true, (proba >= t).astype(int), zero_division=0) for t in grid]
    return float(grid[int(np.argmax(f1s))])


def main():
    df, X, y = carrega_dados()
    print(f"Amostra: {len(X)} registros | positivos (risco): {y.sum()} ({y.mean()*100:.1f}%)")

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE)
    print(f"Treino: {len(X_tr)} | Teste: {len(X_te)}")

    pre = build_preprocessor()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    resultados = {}
    pipelines = {}
    for nome, clf in candidatos().items():
        pipe = Pipeline([("pre", pre), ("clf", clf)])
        auc_cv = cross_val_score(pipe, X_tr, y_tr, cv=cv, scoring="roc_auc").mean()
        pipe.fit(X_tr, y_tr)
        proba = pipe.predict_proba(X_te)[:, 1]
        auc = roc_auc_score(y_te, proba)
        ap = average_precision_score(y_te, proba)
        resultados[nome] = {"AUC (CV)": auc_cv, "AUC (teste)": auc, "PR-AUC (teste)": ap}
        pipelines[nome] = pipe
        print(f"  {nome:22} AUC(cv)={auc_cv:.3f}  AUC(teste)={auc:.3f}  PR-AUC={ap:.3f}")

    melhor_nome = max(resultados, key=lambda k: resultados[k]["AUC (teste)"])
    melhor = pipelines[melhor_nome]
    print(f"\nMelhor modelo: {melhor_nome}")

    # ---- Avaliacao detalhada do melhor modelo ----
    proba = melhor.predict_proba(X_te)[:, 1]
    limiar = melhor_limiar(y_te, proba)
    pred = (proba >= limiar).astype(int)
    print(f"\nLimiar otimo (max F1) = {limiar:.2f}")
    print("Relatorio de classificacao:")
    print(classification_report(y_te, pred, target_names=["Sem risco", "Em risco"]))

    # Matriz de confusao
    fig, ax = plt.subplots(figsize=(5, 4))
    ConfusionMatrixDisplay(confusion_matrix(y_te, pred),
                           display_labels=["Sem risco", "Em risco"]).plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(f"Matriz de confusao - {melhor_nome}")
    fig.tight_layout(); fig.savefig(FIG / "modelo_matriz_confusao.png"); plt.close(fig)

    # Curva ROC
    fpr, tpr, _ = roc_curve(y_te, proba)
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.plot(fpr, tpr, color="#2E5E8C", lw=2, label=f"AUC = {resultados[melhor_nome]['AUC (teste)']:.3f}")
    ax.plot([0, 1], [0, 1], "--", color="gray")
    ax.set_xlabel("Falso positivo"); ax.set_ylabel("Verdadeiro positivo")
    ax.set_title(f"Curva ROC - {melhor_nome}"); ax.legend()
    fig.tight_layout(); fig.savefig(FIG / "modelo_roc.png"); plt.close(fig)

    # Importancia por permutacao (robusta a qualquer modelo)
    perm = permutation_importance(melhor, X_te, y_te, scoring="roc_auc",
                                  n_repeats=10, random_state=RANDOM_STATE)
    imp = pd.Series(perm.importances_mean, index=FEATURES).sort_values()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    imp.plot(kind="barh", ax=ax, color="#8E44AD")
    ax.set_title(f"Importancia das variaveis (permutacao) - {melhor_nome}")
    ax.set_xlabel("Queda media no AUC ao embaralhar")
    fig.tight_layout(); fig.savefig(FIG / "modelo_importancias.png"); plt.close(fig)
    print("\nImportancia das variaveis (top):")
    print(imp.sort_values(ascending=False).round(4).to_string())

    # ---- Persistencia ----
    joblib.dump(melhor, MODELS / "modelo_risco.joblib")
    meta = {
        "melhor_modelo": melhor_nome,
        "features_numericas": NUM_FEATS,
        "features_categoricas": CAT_FEATS,
        "target": TARGET,
        "definicao_target": "piora da defasagem no ano seguinte (defasagem_{t+1} < defasagem_t)",
        "limiar_padrao": round(limiar, 2),
        "metricas": resultados,
        "n_treino": len(X_tr), "n_teste": len(X_te),
        "prevalencia_risco": float(y.mean()),
    }
    (MODELS / "modelo_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] Modelo salvo em {MODELS/'modelo_risco.joblib'}")
    print(f"[OK] Metadados em {MODELS/'modelo_meta.json'}")


if __name__ == "__main__":
    main()

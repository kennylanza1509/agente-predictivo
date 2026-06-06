"""
rag.py — Recuperación de información técnica (RAG) con TF-IDF.

Indexa los documentos de data/conocimiento/ (extractos de normas y criterios de
mantenimiento) y, dada una consulta, devuelve el fragmento más relevante.

"RAG" = Retrieval-Augmented Generation: primero se RECUPERA el texto técnico
pertinente y luego el agente lo usa para fundamentar (y citar) su diagnóstico.

Técnica: TF-IDF + similitud de coseno, solo con librería estándar.

Ejecuta:
    python tools/rag.py "vibracion alta en el motor"
"""

import os
import re
import math
import glob
from collections import Counter

# Carpeta con la base de conocimiento (un nivel arriba, dentro de data/).
CARPETA_CONOCIMIENTO = os.path.join(
    os.path.dirname(__file__), "..", "data", "conocimiento"
)

# Palabras muy comunes que no aportan al significado (stopwords en español).
STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "o",
    "a", "en", "que", "se", "su", "sus", "por", "con", "para", "es", "al", "lo",
    "como", "mas", "más", "puede", "ser", "este", "esta", "estos", "estas",
}


def tokenizar(texto):
    """Divide el texto en palabras minúsculas, sin signos ni stopwords."""
    palabras = re.findall(r"[a-záéíóúñ0-9]+", texto.lower())
    return [p for p in palabras if p not in STOPWORDS and len(p) > 1]


def cargar_documentos(carpeta):
    """Carga cada archivo .md/.txt como un documento {nombre, texto, tokens}."""
    documentos = []
    patrones = [os.path.join(carpeta, "*.md"), os.path.join(carpeta, "*.txt")]
    for patron in patrones:
        for ruta in sorted(glob.glob(patron)):
            with open(ruta, encoding="utf-8") as f:
                texto = f.read()
            documentos.append({
                "nombre": os.path.basename(ruta),
                "texto": texto,
                "tokens": tokenizar(texto),
            })
    return documentos


def calcular_idf(documentos):
    """IDF = qué tan 'rara' es cada palabra en el conjunto de documentos."""
    n_docs = len(documentos)
    apariciones = Counter()
    for doc in documentos:
        for palabra in set(doc["tokens"]):
            apariciones[palabra] += 1
    # +1 para evitar divisiones por cero (suavizado).
    return {p: math.log((n_docs + 1) / (c + 1)) + 1 for p, c in apariciones.items()}


def vector_tfidf(tokens, idf):
    """Convierte una lista de tokens en un vector TF-IDF {palabra: peso}."""
    tf = Counter(tokens)
    total = len(tokens) or 1
    return {p: (conteo / total) * idf.get(p, 0.0) for p, conteo in tf.items()}


def coseno(v1, v2):
    """Similitud de coseno entre dos vectores (diccionarios palabra->peso)."""
    comunes = set(v1) & set(v2)
    producto = sum(v1[p] * v2[p] for p in comunes)
    norma1 = math.sqrt(sum(v * v for v in v1.values()))
    norma2 = math.sqrt(sum(v * v for v in v2.values()))
    if norma1 == 0 or norma2 == 0:
        return 0.0
    return producto / (norma1 * norma2)


class MotorRAG:
    """Índice de búsqueda sobre la base de conocimiento."""

    def __init__(self, carpeta=CARPETA_CONOCIMIENTO):
        self.documentos = cargar_documentos(carpeta)
        self.idf = calcular_idf(self.documentos)
        # Precalcula el vector TF-IDF de cada documento.
        for doc in self.documentos:
            doc["vector"] = vector_tfidf(doc["tokens"], self.idf)

    def consultar(self, consulta, k=1):
        """Devuelve los k documentos más relevantes para la consulta."""
        v_consulta = vector_tfidf(tokenizar(consulta), self.idf)
        puntuados = [
            {"nombre": doc["nombre"], "texto": doc["texto"],
             "score": coseno(v_consulta, doc["vector"])}
            for doc in self.documentos
        ]
        puntuados.sort(key=lambda d: d["score"], reverse=True)
        return puntuados[:k]


def main():
    import sys
    consulta = " ".join(sys.argv[1:]) or "vibracion alta"

    motor = MotorRAG()
    resultados = motor.consultar(consulta, k=2)

    print(f'Consulta: "{consulta}"\n')
    for i, r in enumerate(resultados, 1):
        print(f"#{i}  {r['nombre']}  (score {r['score']:.3f})")
        print("-" * 50)
        print(r["texto"].strip())
        print()


if __name__ == "__main__":
    main()

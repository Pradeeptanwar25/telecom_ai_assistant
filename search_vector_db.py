import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# CHROMA DB
# ============================================================

CHROMA_PATH = "./vector_db"
COLLECTION_NAME = "dpr_records"


# ============================================================
# LOAD CHROMA
# ============================================================

chroma_client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# ============================================================
# SEMANTIC SEARCH FUNCTION
# ============================================================

def semantic_search(
    question,
    top_k=5
):
    """
    User ke natural-language question ko
    vector mein convert karke ChromaDB mein
    semantic similarity search karta hai.
    """

    # --------------------------------------------------------
    # Convert question into embedding
    # --------------------------------------------------------

    query_embedding = embedding_model.encode(
        question
    ).tolist()

    # --------------------------------------------------------
    # Search ChromaDB
    # --------------------------------------------------------

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # --------------------------------------------------------
    # Convert Chroma result into simple records
    # --------------------------------------------------------

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]

    search_results = []

    for i in range(len(documents)):

        search_results.append(
            {
                "document": documents[i],
                "metadata": metadatas[i],
                "distance": distances[i],
            }
        )

    return search_results


# ============================================================
# TEST MODE
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("VECTOR DATABASE SEMANTIC SEARCH")
    print("=" * 70)

    question = input(
        "\nEnter your question: "
    ).strip()

    if not question:

        print("Please enter a question.")

    else:

        results = semantic_search(
            question,
            top_k=5
        )

        print()
        print("=" * 70)
        print("SEARCH RESULTS")
        print("=" * 70)

        for index, result in enumerate(
            results,
            start=1
        ):

            print()
            print(f"Result {index}")
            print("-" * 70)

            metadata = result["metadata"]

            print(
                "Record Key :",
                metadata.get("record_key")
            )

            print(
                "Circle     :",
                metadata.get("circle")
            )

            print(
                "Old Site ID:",
                metadata.get("old_site_id")
            )

            print(
                "Distance   :",
                result["distance"]
            )

            print()

            print(
                result["document"]
            )
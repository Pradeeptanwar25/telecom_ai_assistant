import os
import django
import truststore

# ============================================================
# SSL setup
# ============================================================

truststore.inject_into_ssl()


# ============================================================
# Django setup
# ============================================================

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from dpr.models import DprRecord


# ============================================================
# ChromaDB
# ============================================================

import chromadb

from sentence_transformers import SentenceTransformer


# ============================================================
# ChromaDB configuration
# ============================================================

VECTOR_DB_PATH = "./vector_db"

COLLECTION_NAME = "dpr_records"


# ============================================================
# Connect to ChromaDB
# ============================================================

print("=" * 70)
print("CONNECTING TO CHROMADB")
print("=" * 70)

client = chromadb.PersistentClient(
    path=VECTOR_DB_PATH
)

print(
    f"Vector DB path: {VECTOR_DB_PATH}"
)


# ============================================================
# Delete old collection
# ============================================================

print()
print("Checking existing collection...")

try:

    client.delete_collection(
        name=COLLECTION_NAME
    )

    print(
        f"Old collection '{COLLECTION_NAME}' deleted."
    )

except Exception:

    print(
        f"No existing collection '{COLLECTION_NAME}' found."
    )


# ============================================================
# Create fresh collection
# ============================================================

collection = client.create_collection(
    name=COLLECTION_NAME
)

print(
    f"New collection '{COLLECTION_NAME}' created."
)


# ============================================================
# Load embedding model
# ============================================================

print()
print("=" * 70)
print("LOADING EMBEDDING MODEL")
print("=" * 70)

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print(
    "Embedding model loaded successfully."
)


# ============================================================
# Get records from PostgreSQL
# ============================================================

print()
print("=" * 70)
print("READING RECORDS FROM POSTGRESQL")
print("=" * 70)

records = DprRecord.objects.all()

total_records = records.count()

print(
    f"Records found in PostgreSQL: {total_records}"
)


# ============================================================
# Prepare data
# ============================================================

documents = []
ids = []
metadatas = []


print()
print("=" * 70)
print("PREPARING SEMANTIC SEARCH DOCUMENTS")
print("=" * 70)


for record in records:

    # ========================================================
    # IMPORTANT:
    # Only semantic/remarks-related fields are embedded.
    #
    # Exact dates/status values are intentionally not the
    # primary focus of the vector search because PostgreSQL
    # handles exact structured queries.
    # ========================================================

    text_parts = [

        f"Circle: {record.circle}",

        f"Old Site ID: {record.old_site_id}",

        f"Old Toco: {record.old_toco}",

        f"Circle Remarks: {record.circle_remarks}",

        f"Detailed Remarks: {record.detailed_remarks}",

        (
            "Circle Remarks as on 31-July: "
            f"{record.circle_remarks_as_on_31_july}"
        ),

        (
            "Short Remarks as on 31-July: "
            f"{record.short_remarks_as_on_31_july}"
        ),

        (
            "Submission Pending Remarks: "
            f"{record.submission_pending_remarks}"
        ),
    ]


    # --------------------------------------------------------
    # Convert everything to text
    # --------------------------------------------------------

    text = "\n".join(
        str(value)
        for value in text_parts
        if value is not None
    ).strip()


    # --------------------------------------------------------
    # Store document
    # --------------------------------------------------------

    documents.append(
        text
    )


    # --------------------------------------------------------
    # Use Django primary key as ChromaDB document ID
    # --------------------------------------------------------

    ids.append(
        str(record.id)
    )


    # --------------------------------------------------------
    # Store metadata
    # --------------------------------------------------------

    metadatas.append({

        "record_key": (
            record.record_key
            if record.record_key
            else ""
        ),

        "circle": (
            record.circle
            if record.circle
            else ""
        ),

        "old_site_id": (
            record.old_site_id
            if record.old_site_id
            else ""
        ),
    })


print(
    f"Documents prepared: {len(documents)}"
)


# ============================================================
# Create embeddings
# ============================================================

print()
print("=" * 70)
print("CREATING EMBEDDINGS")
print("=" * 70)

embeddings = model.encode(
    documents,
    show_progress_bar=True
)

print(
    "Embeddings created successfully."
)


# ============================================================
# Convert embeddings to list
# ============================================================

embeddings_list = embeddings.tolist()


# ============================================================
# Save to ChromaDB in batches
# ============================================================

print()
print("=" * 70)
print("SAVING RECORDS TO CHROMADB")
print("=" * 70)


BATCH_SIZE = 1000


for start in range(
    0,
    len(ids),
    BATCH_SIZE
):

    end = min(
        start + BATCH_SIZE,
        len(ids)
    )


    print(
        f"Saving records "
        f"{start + 1} to {end} "
        f"of {len(ids)}..."
    )


    collection.add(

        ids=ids[start:end],

        documents=documents[start:end],

        embeddings=embeddings_list[start:end],

        metadatas=metadatas[start:end],
    )


    print(
        f"Batch saved successfully: "
        f"{start + 1}-{end}"
    )


# ============================================================
# Final verification
# ============================================================

print()
print("=" * 70)
print("VECTOR DATABASE CREATED SUCCESSFULLY")
print("=" * 70)

print(
    f"PostgreSQL records : {total_records}"
)

print(
    f"ChromaDB documents  : {collection.count()}"
)

print(
    f"Vector DB location  : {VECTOR_DB_PATH}"
)

print(
    f"Collection name     : {COLLECTION_NAME}"
)

print()
print(
    "Semantic fields used:"
)

print(
    "- Circle"
)

print(
    "- Old Site ID"
)

print(
    "- Old Toco"
)

print(
    "- Circle Remarks"
)

print(
    "- Detailed Remarks"
)

print(
    "- Circle Remarks as on 31-July"
)

print(
    "- Short Remarks as on 31-July"
)

print(
    "- Submission Pending Remarks"
)

print()
print(
    "PostgreSQL data was not modified."
)

print(
    "Only the ChromaDB semantic index was rebuilt."
)

print("=" * 70)
import re
import chromadb
from sentence_transformers import SentenceTransformer

def load_and_chunk(filepath):
    """ Need to add docs here.."""
    with open(filepath,"r") as f:
        text=f.read()

    chunks = re.split(r"\n(?=RULE \d+)", text.strip())

    rules = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.split("\n", 1)
        header = lines[0]
        body = lines[1].strip() if len(lines) > 1 else ""
        rules.append({"header": header, "text": body})

    return rules

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("policy_manual")

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def ingest_manual(filepath="policy_manual.md"):
    """Need to add docs here"""

    rules=load_and_chunk(filepath=filepath)
    ids = [f"rule_{i+1}" for i in range(len(rules))]
    documents = [r["text"] for r in rules]
    metadatas = [{"header": r["header"]} for r in rules]
    embeddings = embed_model.encode(documents).tolist()

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    print(f"Ingested {len(rules)} rules into ChromaDB.")

def retrieve_rules(claim_text:str,k:int=5):
    """Need to add docs here"""

    query_embedding=embed_model.encode([claim_text]).tolist()
    results=collection.query(
        query_embeddings=query_embedding,
        n_results=k
    )

    retrieved = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        retrieved.append({"header": meta["header"], "text": doc})

    return retrieved

# Smoke test - need to clean this part up
if __name__=="__main__":
    ingest_manual("policy_manual.md")
    test_claim="my Car was rear-ended and my neck hurts lil bit"
    matches=retrieve_rules(claim_text=test_claim,k=5)
    print("="*30)
    for m in matches:
        print(m['header'])
        print(m['text'])
        print('-----')
import re
import chromadb
from sentence_transformers import SentenceTransformer

def load_and_chunk(filepath):
    """Parse a policy manual file into individual rule chunks.

    Splits a markdown/text file into separate rule entries, using a
    ``RULE <number>`` header line as the delimiter. Each resulting chunk is
    further split into a header (the ``RULE N — Title`` line) and a body
    (the rule's descriptive text), so that each rule can be embedded and
    stored independently for retrieval.

    Parameters
    ----------
    filepath : str
        Path to the policy manual file to parse. Expected to contain one
        or more rules, each beginning with a line matching ``RULE <number>``.

    Returns
    -------
    list of dict
        A list of parsed rules, each a dict with keys:

        - ``header`` : str, the rule's title line (e.g. ``"RULE 3 — Personal
          Injury (precedence rule)"``).
        - ``text`` : str, the rule's body text.

    Examples
    --------
    >>> rules = load_and_chunk("policy_manual.md")
    >>> rules[0]["header"]
    'RULE 1 — Property Damage (default)'
    """
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
    """Load, embed, and upsert all policy manual rules into ChromaDB.

    Parses the policy manual via :func:`load_and_chunk`, embeds each rule's
    body text using the module-level ``embed_model``, and upserts the
    resulting embeddings into the ``policy_manual`` ChromaDB collection.
    Uses ``upsert`` rather than ``add`` so that re-running this function
    after editing the manual cleanly overwrites existing rules by ID rather
    than creating duplicates.

    This should be re-run any time ``policy_manual.md`` is edited, since
    ChromaDB does not automatically detect changes to the source file.

    Parameters
    ----------
    filepath : str, optional
        Path to the policy manual file to ingest (default is
        ``"policy_manual.md"``).

    Returns
    -------
    None
        Prints a confirmation message with the number of rules ingested.

    Examples
    --------
    >>> ingest_manual("policy_manual.md")
    Ingested 15 rules into ChromaDB.
    """

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
    """Retrieve the most relevant policy rules for a given claim.

    Embeds the input claim text using the same embedding model used during
    ingestion, then performs a similarity search against the ``policy_manual``
    ChromaDB collection to find the ``k`` most relevant rule chunks. Used to
    build the retrieved-rules context injected into the LLM prompt in
    :func:`model.load_and_route`.

    Parameters
    ----------
    claim_text : str
        The claim description to retrieve relevant rules for.
    k : int, optional
        Number of top-matching rules to retrieve (default is 5). A higher
        ``k`` reduces the risk of a relevant rule being missed due to
        imperfect similarity ranking, at the cost of a longer prompt.

    Returns
    -------
    list of dict
        The top ``k`` matching rules, ordered by similarity, each a dict
        with keys:

        - ``header`` : str, the rule's title (e.g. ``"RULE 3 — Personal
          Injury (precedence rule)"``).
        - ``text`` : str, the rule's body text.

    Examples
    --------
    >>> matches = retrieve_rules("my neck hurts after the crash", k=3)
    >>> matches[0]["header"]
    'RULE 3 — Personal Injury (precedence rule)'
    """

    query_embedding=embed_model.encode([claim_text]).tolist()
    results=collection.query(
        query_embeddings=query_embedding,
        n_results=k
    )

    retrieved = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        retrieved.append({"header": meta["header"], "text": doc})

    return retrieved

# Smoke test 
if __name__=="__main__":
    ingest_manual("policy_manual.md")
    test_claim="my Car was rear-ended and my neck hurts lil bit"
    matches=retrieve_rules(claim_text=test_claim,k=5)
    print("="*30)
    for m in matches:
        print(m['header'])
        print(m['text'])
        print('-----')
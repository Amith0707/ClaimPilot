import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    """Create and return a PostgreSQL database connection.

    Establishes a new connection to the PostgreSQL database using
    credentials provided through environment variables. If an
    environment variable is not defined, a sensible default value
    is used instead.

    Environment Variables
    ---------------------
    DB_HOST : str, optional
        Database host name (default is ``"localhost"``).
    DB_PORT : str, optional
        Database port number (default is ``"5432"``).
    DB_NAME : str, optional
        Database name (default is ``"claimbot"``).
    DB_USER : str, optional
        Database username (default is ``"postgres"``).
    DB_PASSWORD : str, optional
        Database password (default is empty string).

    Returns
    -------
    psycopg2.extensions.connection
        An active PostgreSQL connection object ready for executing
        SQL queries.

    Examples
    --------
    >>> conn = get_connection()
    >>> conn.closed
    0
    """

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "claimbot"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )

def init_db():
    """Initialize the application database schema.

    Creates the ``claims`` table if it does not already exist.
    The table stores routed claim information, including the
    original claim text, routing decision, confidence level,
    processing latency, source, and creation timestamp.

    This function is intended to be executed during application
    startup to ensure the required database schema exists before
    claims are stored or queried.

    Returns
    -------
    None

    Notes
    -----
    The operation is idempotent because it uses
    ``CREATE TABLE IF NOT EXISTS``. Running the function multiple
    times will not overwrite existing data or recreate the table.

    Examples
    --------
    >>> init_db()
    """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id SERIAL PRIMARY KEY,
            claim_text TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            assigned_team TEXT NOT NULL,
            reasoning TEXT NOT NULL,
            confidence TEXT NOT NULL,
            elapsed_ms INTEGER,
            source TEXT NOT NULL DEFAULT 'single',
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_claim(claim_text, result, elapsed_ms, source="single"):
    """Persist a routed claim and its metadata to the database.

    Inserts a claim record into the ``claims`` table, including
    the original claim text, routing decision, processing time,
    confidence score, and request source.

    Parameters
    ----------
    claim_text : str
        Raw claim description submitted for routing.
    result : dict
        Validated routing result containing the keys
        ``category``, ``priority``, ``assigned_team``,
        ``reasoning``, and ``confidence``.
    elapsed_ms : int
        Total processing time in milliseconds for generating
        the routing decision.
    source : str, optional
        Origin of the claim request. Common values include
        ``"single"`` for individual claims and ``"batch"``
        for bulk processing (default is ``"single"``).

    Returns
    -------
    int
        The database-generated primary key ID of the newly
        inserted claim record.

    Notes
    -----
    The function commits the transaction immediately after the
    insert succeeds and closes all database resources before
    returning.

    Examples
    --------
    >>> claim_id = save_claim(
    ...     "My car was rear-ended",
    ...     result,
    ...     1243
    ... )
    >>> claim_id
    42
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO claims (claim_text, category, priority, assigned_team, reasoning, confidence, elapsed_ms, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        claim_text, result["category"], result["priority"],
        result["assigned_team"], result["reasoning"], result["confidence"],
        elapsed_ms, source
    ))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id

def get_all_claims(limit=100):
    """Retrieve previously processed claims from the database.

    Fetches claim records ordered by creation time in descending
    order, returning the most recent claims first. Results are
    returned as dictionaries for convenient access by column name.

    Parameters
    ----------
    limit : int, optional
        Maximum number of records to return (default is 100).

    Returns
    -------
    list[dict]
        A list of claim records. Each dictionary contains the
        columns stored in the ``claims`` table, including claim
        text, routing decision, confidence level, processing
        latency, source, and timestamp.

    Notes
    -----
    Records are sorted by ``created_at`` in descending order so
    that the newest claims appear first.

    Examples
    --------
    >>> claims = get_all_claims(limit=10)
    >>> len(claims)
    10
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM claims ORDER BY created_at DESC LIMIT %s;", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
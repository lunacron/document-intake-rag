CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id         SERIAL PRIMARY KEY,
    filename   TEXT NOT NULL,
    sha256     TEXT NOT NULL UNIQUE,
    status     TEXT NOT NULL DEFAULT 'ingested',
    -- What the document is and whose it is; written at the top of every chunk.
    label      TEXT NOT NULL DEFAULT '',
    -- Whose document this is (e.g. a student). NULL for general documents like the handbook.
    -- Search narrows to the person a question names; use a real ID so two people with the same
    -- name stay distinct.
    subject_id   TEXT,
    subject_name TEXT,
    pii_found  JSONB NOT NULL DEFAULT '{}',
    -- 'public' (e.g. handbook) is visible to every role; 'restricted' (student records) only to registrar.
    access_level TEXT NOT NULL DEFAULT 'restricted' CHECK (access_level IN ('public', 'restricted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- snowflake-arctic-embed-s produces 384-dim vectors; change both if you swap models.
CREATE TABLE chunks (
    id        SERIAL PRIMARY KEY,
    doc_id    INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page      INT,
    idx       INT NOT NULL,
    text      TEXT NOT NULL,
    embedding vector(384) NOT NULL
);

-- One row per /query call that reached Claude: audit trail and cost tracking.
CREATE TABLE query_log (
    id            SERIAL PRIMARY KEY,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    role          TEXT NOT NULL,
    question      TEXT NOT NULL,
    input_tokens  INT NOT NULL,
    output_tokens INT NOT NULL,
    cost_usd      NUMERIC(10, 6) NOT NULL,
    request_id    TEXT
);

-- One structured record per document, waiting for (or past) human review.
CREATE TABLE extractions (
    id            SERIAL PRIMARY KEY,
    doc_id        INT NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
    -- pending_review -> approved -> sent; or rejected / failed
    status        TEXT NOT NULL CHECK (status IN ('pending_review', 'approved', 'sent', 'rejected', 'failed')),
    data          JSONB NOT NULL,                -- what Claude proposed
    flags         JSONB NOT NULL DEFAULT '[]',   -- what the checks found (for the reviewer)
    final_data    JSONB,                         -- what was approved (after corrections)
    changed_fields JSONB,                        -- fields the reviewer corrected: labeled data
    legacy_result TEXT,
    error         TEXT,
    reviewed_by   TEXT,
    reviewed_at   TIMESTAMPTZ,
    model         TEXT,
    input_tokens  INT,
    output_tokens INT,
    cost_usd      NUMERIC(10, 6),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Stand-in for the legacy system. application_id is the idempotency key.
CREATE TABLE legacy_students (
    application_id TEXT PRIMARY KEY,
    data           JSONB NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX chunks_doc_idx ON chunks (doc_id);

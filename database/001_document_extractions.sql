CREATE TABLE IF NOT EXISTS document_extractions (
    extraction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    extraction_version INTEGER NOT NULL DEFAULT 1,
    ocr_text TEXT NOT NULL DEFAULT '',
    extraction_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    extraction_method TEXT NOT NULL,
    model_name TEXT NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'needs_review'
        CHECK (processing_status IN ('completed', 'needs_review', 'failed')),
    reviewer_corrected_json JSONB,
    reviewer_ref TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, extraction_version)
);
CREATE INDEX IF NOT EXISTS idx_document_extractions_document
    ON document_extractions(document_id, created_at DESC);

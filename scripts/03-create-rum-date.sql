CREATE INDEX apod_tsv_date_idx ON apod USING rum (fts rum_tsvector_timestamp_ops, date)
	WITH (attach = 'date', to = 'fts', order_by_attach='t');

UPDATE pg_index SET indisvalid = false
	WHERE indexrelid = 'apod_tsv_idx'::regclass;
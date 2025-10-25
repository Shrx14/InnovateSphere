"""Migrate existing float-array embeddings to pgvector Vector column (safe).

This script does a dry-run by default. It will:
 - ensure the pgvector extension exists
 - create a DB-side backup table `project_vectors_backup_<ts>` (always)
 - (optional) attempt a file backup using pg_dump if --backup-file is provided
 - add a new column `embedding_vec` of type vector(384)
 - copy values from the existing `embedding` column into `embedding_vec`, converting
   numpy scalars to native Python floats and validating dimension
 - when run with --commit, drop the old `embedding` column and rename `embedding_vec` -> `embedding`

Usage (dry-run):
    python migrate_embeddings_to_pgvector.py

To apply destructive rename/drop:
    python migrate_embeddings_to_pgvector.py --commit --backup-file=project_vectors.sql

Notes:
 - The script will detect if the current `embedding` column is already pgvector and exit safely.
 - We prefer creating a DB-side backup table as it doesn't rely on pg_dump availability.
"""
import os
import sys
import argparse
import subprocess
import datetime
import psycopg2
from pgvector.psycopg2 import register_vector
from psycopg2.extras import register_default_json


DB_URL = os.getenv('DATABASE_URL', 'postgresql://innovate_admin:innovate_pass_2025@localhost:5432/innovatesphere_dev')


def create_backup_table(cur, timestamp_suffix):
    backup_name = f'project_vectors_backup_{timestamp_suffix}'
    print(f'Creating DB-side backup table `{backup_name}`...')
    cur.execute(f"DROP TABLE IF EXISTS {backup_name};")
    cur.execute(f"CREATE TABLE {backup_name} AS TABLE project_vectors;")
    print(f'Backup table created: {backup_name}')
    return backup_name


def try_pg_dump(db_url, out_file):
    # Attempt to run pg_dump if available; return True on success
    try:
        print(f'Trying pg_dump to write backup SQL to {out_file}...')
        subprocess.run(['pg_dump', db_url, '-t', 'project_vectors', '-f', out_file], check=True)
        print('pg_dump completed successfully.')
        return True
    except FileNotFoundError:
        print('pg_dump not found in PATH; skipping file dump.')
    except subprocess.CalledProcessError as e:
        print('pg_dump failed:', e)
    return False


def migrate(commit=False, backup_file=None):
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False

    # Register vector type after establishing connection
    register_vector(conn)
    register_default_json(conn)
    try:
        with conn.cursor() as cur:
            print('Enabling pgvector extension (if not present)...')
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Detect current embedding column type; if already vector, exit safely
            cur.execute("SELECT data_type, udt_name FROM information_schema.columns WHERE table_name='project_vectors' AND column_name='embedding';")
            col = cur.fetchone()
            if col is not None:
                data_type, udt_name = col[0], col[1]
                # If column is already pgvector, skip
                if udt_name == 'vector' or (data_type and data_type.lower() == 'user-defined'):
                    print('Detected existing `embedding` column of pgvector type. Nothing to migrate.')
                    return

            # Create DB-side backup table (fast, contained)
            ts = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_table = create_backup_table(cur, ts)

            # Optionally attempt a file backup using pg_dump (best-effort)
            if backup_file:
                backed = try_pg_dump(DB_URL, backup_file)
                if not backed:
                    print('pg_dump failed or not present; DB-side backup table created as fallback.')

            # Add new column
            print('Ensuring new column embedding_vec exists...')
            cur.execute("ALTER TABLE project_vectors ADD COLUMN IF NOT EXISTS embedding_vec vector(384);")

            # Fetch existing embeddings (old float[] column expected)
            print('Selecting existing rows with embeddings...')
            cur.execute("SELECT id, embedding FROM project_vectors;")
            rows = cur.fetchall()
            # Only consider rows that actually have a non-null embedding in the old column
            expected_total = sum(1 for r in rows if r[1] is not None)
            print(f'Found {len(rows)} total rows, {expected_total} with non-null embeddings. Copying embeddings...')

            updated = 0
            for r in rows:
                pid = r[0]
                emb = r[1]
                if emb is None:
                    continue
                # emb is expected to be a list/tuple of floats or similar; ensure native floats
                try:
                    cleaned = [float(x) for x in emb]
                    if len(cleaned) != 384:
                        raise ValueError(f'expected 384 dimensions, not {len(cleaned)}')
                    cur.execute("UPDATE project_vectors SET embedding_vec = %s::vector WHERE id = %s;", (cleaned, pid))
                    updated += 1
                except Exception as e:
                    print(f'Failed to update id={pid}:', e)

            print(f'Copied embeddings for {updated}/{expected_total} rows.')

            # Finalize: only drop/rename if commit flag provided AND we copied all expected rows
            if not commit:
                print('\nDRY RUN (no destructive changes applied).')
                print('To apply destructive rename/drop, re-run with --commit.')
                print(f'You may inspect backup table `{backup_table}` or supply --backup-file to create an external dump.')
            else:
                if updated != expected_total:
                    print('\nRefusing destructive rename/drop: number of copied rows does not match expected non-null rows.')
                    print(f'Copied: {updated}, Expected: {expected_total}. Aborting destructive changes.')
                    print(f'Inspect backup table `{backup_table}` and investigate differences before re-running with --commit.')
                else:
                    print('All rows copied successfully; dropping old embedding column and renaming embedding_vec -> embedding')
                    cur.execute("ALTER TABLE project_vectors DROP COLUMN IF EXISTS embedding;")
                    cur.execute("ALTER TABLE project_vectors RENAME COLUMN embedding_vec TO embedding;")

        conn.commit()
        print('Migration completed successfully.' + ('' if commit else ' (dry-run committed non-destructive steps).'))
    except Exception as e:
        conn.rollback()
        print('Migration failed, rolled back. Error:', e)
        raise
    finally:
        conn.close()


def parse_args(argv):
    p = argparse.ArgumentParser(description='Migrate float[] embeddings to pgvector (safe, with backups).')
    p.add_argument('--commit', action='store_true', help='Actually drop/rename columns (destructive). Default is dry-run.')
    p.add_argument('--backup-file', type=str, help='Optional path to write pg_dump SQL for table backup (best-effort).')
    return p.parse_args(argv)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    migrate(commit=args.commit, backup_file=args.backup_file)
"""Migrate existing float-array embeddings to pgvector Vector column.

Workflow this script performs:
 - Ensures pgvector extension is enabled
 - Adds a new column `embedding_vec` of type vector(384) if missing
 - Copies values from the existing `embedding` float[] column into `embedding_vec`
 - Drops the old `embedding` column and renames `embedding_vec` -> `embedding`

Run this after `enable_pgvector.py` and with the Flask app's DATABASE_URL available.
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from psycopg2.extras import register_default_json


DB_URL = os.getenv('DATABASE_URL', 'postgresql://innovate_admin:innovate_pass_2025@localhost:5432/innovatesphere_dev')


def migrate():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    
    # Register vector type after establishing connection
    register_vector(conn)
    register_default_json(conn)
    try:
        with conn.cursor() as cur:
            print('Enabling pgvector extension (if not present)...')
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Add new column
            print('Ensuring new column embedding_vec exists...')
            cur.execute("ALTER TABLE project_vectors ADD COLUMN IF NOT EXISTS embedding_vec vector(384);")

            # Fetch existing embeddings
            print('Selecting existing rows with embeddings...')
            cur.execute("SELECT id, embedding FROM project_vectors;")
            rows = cur.fetchall()
            total = len(rows)
            print(f'Found {total} rows. Copying embeddings...')

            updated = 0
            for r in rows:
                pid = r[0]
                emb = r[1]
                if emb is None:
                    continue
                # emb is expected to be a list/tuple of floats
                try:
                    # Ensure elements are native Python floats (psycopg2/pgvector can't adapt numpy.float32)
                    cleaned = [float(x) for x in emb]
                    # Optional: verify dimension matches expected (384)
                    if len(cleaned) != 384:
                        raise ValueError(f'expected 384 dimensions, not {len(cleaned)}')
                    cur.execute("UPDATE project_vectors SET embedding_vec = %s::vector WHERE id = %s;", (cleaned, pid))
                    updated += 1
                except Exception as e:
                    print(f'Failed to update id={pid}:', e)

            print(f'Copied embeddings for {updated}/{total} rows.')

            # Drop old column and rename new one
            print('Dropping old embedding column and renaming embedding_vec -> embedding')
            cur.execute("ALTER TABLE project_vectors DROP COLUMN IF EXISTS embedding;")
            cur.execute("ALTER TABLE project_vectors RENAME COLUMN embedding_vec TO embedding;")

        conn.commit()
        print('Migration completed successfully.')
    except Exception as e:
        conn.rollback()
        print('Migration failed, rolled back. Error:', e)
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()

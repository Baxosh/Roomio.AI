#!/usr/bin/env python3
"""
Extract database schema from PostgreSQL and write to structure.txt
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )

def get_tables(cursor):
    """Get all tables in public schema"""
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    return [row[0] for row in cursor.fetchall()]

def get_table_info(cursor, table_name):
    """Get detailed information about a table"""
    # Get columns
    cursor.execute("""
        SELECT
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))

    columns = []
    for row in cursor.fetchall():
        col_name, data_type, max_len, nullable, default = row

        # Format data type
        if max_len and data_type in ('character varying', 'character'):
            type_str = f"{data_type}({max_len})"
        else:
            type_str = data_type

        columns.append({
            'name': col_name,
            'type': type_str,
            'nullable': nullable,
            'default': default
        })

    # Get primary keys
    cursor.execute("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public'
        AND tc.table_name = %s
        AND tc.constraint_type = 'PRIMARY KEY'
        ORDER BY kcu.ordinal_position
    """, (table_name,))

    primary_keys = [row[0] for row in cursor.fetchall()]

    # Get foreign keys
    cursor.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
        AND tc.table_name = %s
    """, (table_name,))

    foreign_keys = []
    for row in cursor.fetchall():
        col_name, foreign_table, foreign_col, constraint_name = row
        foreign_keys.append({
            'column': col_name,
            'references': f"{foreign_table}({foreign_col})",
            'constraint': constraint_name
        })

    # Get indexes
    cursor.execute("""
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = %s
        ORDER BY indexname
    """, (table_name,))

    indexes = []
    for row in cursor.fetchall():
        index_name, index_def = row
        indexes.append({
            'name': index_name,
            'definition': index_def
        })

    return {
        'columns': columns,
        'primary_keys': primary_keys,
        'foreign_keys': foreign_keys,
        'indexes': indexes
    }

def format_table_info(table_name, info):
    """Format table information as text"""
    output = []
    output.append("=" * 80)
    output.append(f"Table: public.{table_name}")
    output.append("=" * 80)
    output.append("")

    # Columns section
    output.append("Columns:")
    output.append("-" * 80)

    # Calculate column widths for alignment
    max_name_len = max(len(col['name']) for col in info['columns'])
    max_type_len = max(len(col['type']) for col in info['columns'])

    # Header
    header = f"{'Column':<{max_name_len}}  {'Type':<{max_type_len}}  {'Nullable'}  {'Default'}"
    output.append(header)
    output.append("-" * len(header))

    for col in info['columns']:
        pk_marker = " (PK)" if col['name'] in info['primary_keys'] else ""
        default_val = col['default'] if col['default'] else ""

        line = f"{col['name']:<{max_name_len}}  {col['type']:<{max_type_len}}  {col['nullable']:<8}  {default_val}{pk_marker}"
        output.append(line)

    output.append("")

    # Primary keys
    if info['primary_keys']:
        output.append("Primary Key:")
        output.append(f"    {', '.join(info['primary_keys'])}")
        output.append("")

    # Foreign keys
    if info['foreign_keys']:
        output.append("Foreign Keys:")
        for fk in info['foreign_keys']:
            output.append(f"    {fk['column']} -> {fk['references']}")
            output.append(f"        Constraint: {fk['constraint']}")
        output.append("")

    # Indexes
    if info['indexes']:
        output.append("Indexes:")
        for idx in info['indexes']:
            output.append(f"    {idx['name']}")
            # Show simplified index definition
            if 'UNIQUE' in idx['definition']:
                output.append(f"        Type: UNIQUE")
            elif idx['name'].endswith('_pkey'):
                output.append(f"        Type: PRIMARY KEY")
            else:
                output.append(f"        Type: INDEX")
        output.append("")

    return "\n".join(output)

def main():
    """Main function to extract schema"""
    print("Connecting to database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("Fetching table list...")
        tables = get_tables(cursor)
        print(f"Found {len(tables)} tables")

        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append(f"Database Schema: {os.getenv('POSTGRES_DB', 'postgres')}")
        output_lines.append(f"Generated: {os.popen('date').read().strip()}")
        output_lines.append("=" * 80)
        output_lines.append("")

        for i, table in enumerate(tables, 1):
            print(f"Processing table {i}/{len(tables)}: {table}")
            info = get_table_info(cursor, table)
            table_text = format_table_info(table, info)
            output_lines.append(table_text)
            output_lines.append("")

        # Write to structure.txt
        output_file = "structure.txt"
        with open(output_file, 'w') as f:
            f.write("\n".join(output_lines))

        print(f"\n✓ Schema written to {output_file}")
        print(f"  Total tables: {len(tables)}")

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()

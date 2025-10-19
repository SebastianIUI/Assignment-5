#!/usr/bin/env python3
"""
Pure-Python CSV parser and utility to compute the most common Schedule (time) per genre.

Usage:
    python most_common_schedule_by_genre.py <csv_path>

Expected CSV header includes:
 - Genres
 - Schedule (time)

No external modules are used.
"""

import sys
import os


def split_csv_line(line):
    """Split a CSV line into fields (RFC4180-style), handling quoted fields and escaped quotes."""
    fields, cur, i, n = [], [], 0, len(line)
    in_quotes = False

    while i < n:
        ch = line[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and line[i + 1] == '"':
                    cur.append('"')
                    i += 2
                else:
                    in_quotes = False
                    i += 1
            else:
                cur.append(ch)
                i += 1
        else:
            if ch == '"':
                in_quotes = True
                i += 1
            elif ch == ',':
                fields.append(''.join(cur))
                cur = []
                i += 1
            else:
                cur.append(ch)
                i += 1

    fields.append(''.join(cur))

    return [
        f if (len(f) > 1 and f[0] == '"' and f[-1] == '"') else f.strip()
        for f in fields
    ]


def iter_csv_rows(path):
    """Yield parsed rows from a CSV file, handling multiline quoted fields."""
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        buffer = ''
        for raw_line in f:
            line = raw_line.rstrip('\n')
            buffer = f"{buffer}\n{line}" if buffer else line

            # Count unescaped quotes to determine if the line is complete
            quote_count = buffer.count('"')
            if quote_count % 2 == 0:
                yield split_csv_line(buffer)
                buffer = ''


def extract_genres(genre_field):
    """Parse and return a list of genres from a genre field."""
    genre_field = genre_field.strip()

    if genre_field.startswith('"') and genre_field.endswith('"'):
        genre_field = genre_field[1:-1]

    if genre_field.startswith('[') and genre_field.endswith(']'):
        inside = genre_field[1:-1].strip()
        genres, cur, in_q, qchar = [], '', False, None
        i = 0
        while i < len(inside):
            ch = inside[i]
            if not in_q and ch in ('"', "'"):
                in_q = True
                qchar = ch
                cur = ''
                i += 1
            elif in_q:
                if ch == qchar:
                    genres.append(cur)
                    in_q, qchar = False, None
                    i += 1
                    while i < len(inside) and inside[i] in ', ':
                        i += 1
                else:
                    cur += ch
                    i += 1
            else:
                # Unquoted token
                j = i
                while j < len(inside) and inside[j] != ',':
                    j += 1
                token = inside[i:j].strip().strip('"\'')
                if token:
                    genres.append(token)
                i = j + 1
        return genres

    # Fallback: split on commas
    return [g.strip().strip('"\'') for g in genre_field.split(',') if g.strip()]


def get_most_common_schedule_by_genre(csv_path):
    """Return a dict mapping genre -> most common schedule time."""
    rows = iter_csv_rows(csv_path)

    try:
        header = next(rows)
    except StopIteration:
        return {}

    # Identify columns
    header_map = {h.strip(): idx for idx, h in enumerate(header)}
    genres_col = next((idx for name, idx in header_map.items() if 'genre' in name.lower()), None)
    schedule_col = next((idx for name, idx in header_map.items() if 'schedule' in name.lower() and 'time' in name.lower()), None)

    if genres_col is None:
        raise ValueError('Could not find a Genres column in header')
    if schedule_col is None:
        raise ValueError('Could not find a Schedule (time) column in header')

    # genre -> { time -> count }
    counts = {}

    for row in rows:
        if max(genres_col, schedule_col) >= len(row):
            continue

        raw_genres = row[genres_col]
        time = row[schedule_col].strip()
        if not time:
            continue

        genres = extract_genres(raw_genres)
        for genre in genres:
            if not genre:
                continue
            genre_counts = counts.setdefault(genre, {})
            genre_counts[time] = genre_counts.get(time, 0) + 1

    # Determine most common time per genre
    result = {}
    for genre, time_counts in counts.items():
        # Sort by count descending, then time ascending for tie-break
        best_time = max(time_counts.items(), key=lambda x: (x[1], x[0]))
        result[genre] = best_time[0]

    return result


def _main(argv):
    # Optional: fallback hardcoded CSV path (for testing)
    fallback_path = "C:/Users/sebas/Downloads/TV_show_data.csv"

    if len(argv) >= 2:
        path = argv[1]
    else:
        print("⚠️  No CSV path provided as argument.")
        print(f"ℹ️  Using fallback path: {fallback_path}")
        path = fallback_path

    if not os.path.isfile(path):
        print(f"❌ File not found: {path}")
        return 1

    try:
        result = get_most_common_schedule_by_genre(path)
        if not result:
            print("⚠️  No valid data found in the CSV.")
            return 1
        for genre in sorted(result):
            print(f"{genre}: {result[genre]}")
        return 0
    except ValueError as ve:
        print(f"Value error: {ve}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    try:
        code = _main(sys.argv)
        if not isinstance(code, int):
            code = 1
        sys.exit(code)
    except Exception as e:
        print(f"🔥 Fatal error in script execution: {e}")
        sys.exit(1)

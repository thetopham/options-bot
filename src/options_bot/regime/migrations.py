from __future__ import annotations

import sqlite3

import pandas as pd


def ensure_regime_labels_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        create table if not exists regime_labels (
            timestamp text not null,
            symbol text not null,
            timeframe text not null,
            model_version text not null,
            regime_id integer not null,
            regime_name text not null,
            regime_probability real not null,
            created_at text not null default current_timestamp,
            primary key (timestamp, symbol, timeframe, model_version)
        )
        """
    )
    conn.execute("create index if not exists idx_regime_labels_symbol_time on regime_labels(symbol, timeframe, timestamp)")
    conn.commit()


def write_regime_labels(conn: sqlite3.Connection, labels: pd.DataFrame) -> int:
    required = ["timestamp", "symbol", "timeframe", "model_version", "regime_id", "regime_name", "regime_probability"]
    missing = [col for col in required if col not in labels.columns]
    if missing:
        raise ValueError(f"missing regime label columns: {missing}")
    rows = labels[required].to_records(index=False).tolist()
    conn.executemany(
        """
        insert or replace into regime_labels(timestamp, symbol, timeframe, model_version, regime_id, regime_name, regime_probability)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)

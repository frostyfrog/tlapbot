import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def insert_counters(db):
    for redeem, redeem_info in current_app.config['REDEEMS'].items():
        if redeem_info["type"] == "counter":
            try:
                db.execute(
                    "INSERT INTO counters(name, count) VALUES(?, 0)",
                    (redeem,)
                )
                db.commit()
            except Error as e:
                print("Failed inserting counters to db:", e.args[0])


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    insert_counters(db)


def clear_redeem_queue():
    db = get_db()

    try:
        cursor = db.execute(
            "DELETE FROM redeem_queue"
        )
        cursor.execute(
            """UPDATE counters SET count = 0"""
        )
        db.commit()
    except Error as e:
        print("Error occured deleting redeem queue:", e.args[0])


def refresh_counters():
    db = get_db()

    try:
        db.execute("DELETE FROM counters")
        db.commit()
    except Error as e:
        print("Error occured deleting old counters:", e.args[0])
    
    for redeem, redeem_info in current_app.config['REDEEMS'].items():
        if redeem_info["type"] == "counter":
            try:
                cursor = db.execute(
                    "INSERT INTO counters(name, count) VALUES(?, 0)",
                    (redeem,)
                )
                db.commit()
            except Error as e:
                print("Failed inserting counters to db:", e.args[0])


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


@click.command('clear-queue')
@with_appcontext
def clear_queue_command():
    """Remove all redeems from the redeem queue."""
    clear_redeem_queue()
    click.echo('Cleared redeem queue.')


@click.command('refresh-counters')
@with_appcontext
def refresh_counters_command():
    """Refresh counters from current config file. (Remove old ones, add new ones.)"""
    refresh_counters()
    click.echo('Counters refreshed.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

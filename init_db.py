import alembic.config

alembicArgs = [
    '--raiseerr',
    'upgrade', 'head',
]

if __name__ == "__main__":
    alembic.config.main(argv=alembicArgs)

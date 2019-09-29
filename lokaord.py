#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------------------------- #
import logman

import database.db

if __name__ == '__main__':
    logman.init(role='cli')
    logman.info('Loka-Orð initialized')
    db_name = 'lokaord'
    database.db.setup_data_directory(db_name, __file__)
    db_uri = database.db.create_db_uri(db_name)
    database.db.setup_connection(db_uri, db_echo=False)
    database.db.init_db()

# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

class Common(object):
    """
    This object is a base for another objects
    """
    _delimiter = None
    _statement = None
    _data = None
    
    def __init__(self, delimiter):
        self._delimiter = delimiter
        self._data = {"tables": [],
                      "cols": [],
                      "values": [],
                      "order": [],
                      "where": ""
        }

    def set_table(self, tablename):
        self._data["tables"].append(tablename)

    def get_statement(self):
        return self._statement

    def get_values(self):
        return self._data["values"]

    def clear(self):
        self._statement = None
        self._data = {"tables": [],
                      "cols": [],
                      "values": [],
                      "order": [],
                      "where": ""
        }

class Select(Common):
    # NOTE: delimiter is not used
    def __init__(self, delimiter=None):
        super(Select, self).__init__(delimiter)

    def set_cols(self, colname):
       self._data["cols"].append(colname)

    def set_filter(self, filter, value=None, attachment=None):
        if value:
            self._data["values"].append(value)

        if not attachment:
            self._data["where"] = filter
        else:
            if attachment in [SQL_AND, SQL_OR]:
                self._data["where"] = " ".join([self._data["where"],
                                                attachment, filter])
            else:
                # FIXME: is the case to generate an exception?
                pass

    def order_by(self, colname, direction=None):
        if direction:
            self._data["order"] = " ".join([colname, direction])
        else:
            self._data["order"] = colname

    def build(self):
        self._statement = " ".join(["SELECT", ", ".join(self._data["cols"]),
                                   "FROM", ", ".join(self._data["tables"])])

        if self._data["where"]:
            self._statement = " ".join([self._statement, "WHERE",
                                        self._data["where"]])

        if self._data["order"]:
            self._statement = " ".join([self._statement, "ORDER BY",
                                        self._data["order"]])

class Insert(Common):
    def __init__(self, delimiter):
        super(Insert, self).__init__(delimiter)

    def set_data(self, **kwargs):
        for key, item in kwargs.items():
            self._data["cols"].append(key)
            self._data["values"].append(item)

    def build(self):
        for i in range(len(self._data["values"])):
            if i == 0:
                values_alias = self._delimiter
            else:
                values_alias = ", ".join([values_alias, self._delimiter])

        self._statement = " ".join(["INSERT INTO", self._data["tables"][0],
                                    "(", ", ".join(self._data["cols"]),
                                    ") VALUES (", values_alias, ")"])

class Update(Common):
    def __init__(self, delimiter):
        # TODO: write the class
        super(Update, self).__init__(delimiter)
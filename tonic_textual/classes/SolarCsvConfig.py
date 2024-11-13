class SolarCsvConfig:
    def __init__(self, num_columns, has_header=False, escape_char="\"", quote_char="\"", delimiter=",", null_char="\\N"):
        self.num_columns = num_columns
        self.has_header = has_header
        self.escape_char = escape_char
        self.quote_char = quote_char
        self.delimiter = delimiter
        self.null_char = null_char

    def to_dict(self):
        return {
            "numColumns": self.num_columns,
            "hasHeader": self.has_header,
            "escapeChar": self.escape_char,
            "quoteChar": self.quote_char,
            "delimiter": self.delimiter,
            "nullChar": self.null_char
        }
from enum import Enum


class StringDateFormat(str, Enum):
    YearMonthDayNoSeparator = "YearMonthDayNoSeparator"
    YearMonthDayHyphen = "YearMonthDayHyphen"
    DayMonthYearSlash = "DayMonthYearSlash"
    DayMonthYearHyphen = "DayMonthYearHyphen"
    MonthDayYearSlash = "MonthDayYearSlash"
    MonthDayShortYearSlash = "MonthDayShortYearSlash"
    ShortMonthDayYearSlash = "ShortMonthDayYearSlash"
    MonthDayYearHyphen = "MonthDayYearHyphen"
    MonthDayYearNoSeparator = "MonthDayYearNoSeparator"
    DayThreeCharMonthYearSlash = "DayThreeCharMonthYearSlash"
    DayThreeCharMonthYearHyphen = "DayThreeCharMonthYearHyphen"
    DayFullMonthyearSpace = "DayFullMonthyearSpace"
    MonthYearHyphen = "MonthYearHyphen"
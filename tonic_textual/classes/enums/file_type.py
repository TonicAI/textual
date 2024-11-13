from enum import Enum


class FileTypeEnum(str, Enum):
    csv = ("Csv",)
    raw = ("Raw",)
    pdf = ("Pdf",)
    docX = ("DocX",)
    png = ("Png",)
    jpg = ("Jpg",)
    tif = ("Tif",)
    xlsx = ("Xlsx",)

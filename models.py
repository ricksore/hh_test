"""
Module for storing models
"""

from datetime import datetime

from pony.orm import *

database = Database(
    provider='postgres',
    user='postgres',
    host='postgres',
    password='postgres',
    database='postgres'
)


class MediaAsset(database.Entity):
    """
    Model for storing media assets.
    """

    gtin = Required(str, unique=True)
    channel = Required(str)
    mediaId = Required(str)
    contentType = Optional(str)
    mediaType = Optional(str)
    description = Optional(str)
    brand = Optional(str)
    category = Optional(str)
    hasCopyright = Optional(bool)
    media = Optional(Json)

    status = Required(str)
    resolutionKey = Required(str)
    resolutionInPx = Required(str)
    sizeInBytes = Optional(int)

    licenseValidFrom = Required(datetime, default=datetime.now)
    licenseValidUntil = Required(datetime, default=datetime.now)
    sourceUrl = Optional(str)
    sourceUrlValidFrom = Optional(datetime)
    sourceUrlValidUntil = Optional(datetime)


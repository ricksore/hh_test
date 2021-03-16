"""
Module for the main application.
"""

from datetime import datetime
import json
import os

from enum import Enum
from pydantic import BaseModel
from pydantic import Json
from pydantic import constr
from pydantic import validator
from pydantic.typing import Literal
from typing import List
from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.security import APIKeyHeader

from models import database, db_session, MediaAsset

X_API_KEY = APIKeyHeader(name='X-API-Key')

app = FastAPI()

@app.on_event('startup')
def startup():
    """
    Initialize the database.
    """

    database.generate_mapping(create_tables=True)


media_lake_router = APIRouter()

class MediaModel(BaseModel):
    """
    Validation model for the media field in media asset.
    """

    payload: Optional[str]
    sourceUrl: Optional[str]
    sourceUrlValidUntil: Optional[datetime]

    @validator('payload')
    def validate_payload(cls, value, values, **kwargs):
        if value:
            if values.get('sourceUrl') or values.get('sourceUrlValidUntil'):
                raise ValueError(
                    'Only 1 of payload or sourceUrl/sourceUrlValidUntil may be '
                    'entered at the same time.'
                )
        return value


class MediaAssetQueryModel(BaseModel):
    """
    Query model for searching Media Asset model.
    """

    gtin: Optional[str]
    channel: Optional[str]
    mediaId: Optional[str]
    contentType: Optional[Literal[
        "image/tiff",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/bmp"
    ]]
    mediaType: Optional[Literal[
        "MainImage",
        "AuxiliaryImage",
        "AdditionalImage",
        "SwatchImage"
    ]]
    resolutionKey: Optional[Literal[
        "ORIGINAL",
        "X240",
        "X1024",
        "X2048"
    ]]


class BaseMediaAssetModel(BaseModel):
    """
    Base model for create and response model.
    """
    
    gtin: str
    channel: str
    mediaId: str
    contentType: Literal[
        "image/tiff",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/bmp"
    ]

    mediaType: Optional[Literal[
        "MainImage",
        "AuxiliaryImage",
        "AdditionalImage",
        "SwatchImage"
    ]]
    description: Optional[str]
    brand: Optional[str]
    category: Optional[str]
    status: Optional[Literal[
        "ML010New",
        "ML030Imported",
        "ML060QaPending",
        "ML070QaApproved",
        "ML090Retired",
        "ML099Error"
    ]]
    resolutionKey: Optional[Literal[
        "ORIGINAL",
        "X240",
        "X1024",
        "X2048"
    ]]
    resolutionInPx: Optional[str]
    hasCopyright: bool


class MediaAssetCreateModel(BaseMediaAssetModel):
    """
    Create model for Media Asset model.
    """

    media: Optional[MediaModel] = None


class MediaAssetResponseModel(BaseMediaAssetModel):
    """
    Response model for Media Asset model.
    """


class MediaAssetDeleteModel(BaseModel):
    """
    Delete model for Media Asset model.
    """

    channel: Optional[str]
    gtin: Optional[str]
    mediaId: Optional[str]
    contentType: Optional[Literal[
        "image/tiff",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/bmp"
    ]]


@media_lake_router.get('/', response_model=List[MediaAssetResponseModel])
async def get_media_assets(params: MediaAssetQueryModel = Depends()):
    """
    View for fetching media assets matching the params.
    """

    with db_session:
        media_assets = MediaAsset.select(**params.dict(exclude_none=True))
        media_assets = [media_asset.to_dict() for media_asset in media_assets]

    return media_assets


@media_lake_router.post('/', status_code=202, response_model=List[MediaAssetResponseModel])
async def create_media_assets(media_assets: List[MediaAssetCreateModel]):
    """
    View for creating media assets.
    """
    
    try:
        with db_session:
            for media_asset in media_assets:
                data = media_asset.dict()

                if media_asset.media and media_asset.media.sourceUrl:
                    data['sourceUrl'] = media_asset.media.sourceUrl
                    # NOTE: I don't know where to get this so I'll get this from this
                    # for the mean time :P
                    data['sourceUrlValidFrom'] = (
                        media_asset.media.sourceUrlValidUntil
                    )
                    data['sourceUrlValidUntil'] = (
                        media_asset.media.sourceUrlValidUntil
                    )
                
                data['media'] = json.dumps(data['media'], default=str)
                MediaAsset(**data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return media_assets


@media_lake_router.patch('/', status_code=202, response_model=List[MediaAssetResponseModel])
async def update_media_assets(media_assets: List[MediaAssetResponseModel]):
    """
    View for creating media assets.
    """
    
    with db_session:
        for media_asset in media_assets:
            media_asset_object = MediaAsset.get(gtin=media_asset.gtin)
            if not media_asset_object:
                continue
            media_asset_object.set(**media_asset.dict())
    return media_assets


@media_lake_router.delete('/', status_code=200)
async def delete_media_asset(media_asset: MediaAssetDeleteModel):
    """
    View for creating media assets.
    """
    
    with db_session:
        media_asset_object = MediaAsset.get(**media_asset.dict())

        if not media_asset_object:
            raise HTTPException(status_code=404)

        media_asset_object.delete()
    return None


async def is_authenticated(api_key: str = Depends(X_API_KEY)):
    """
    Makes sure that the api key lives in the header.
    """

    if api_key != os.environ.get('API_KEY', ''):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return

app.include_router(
    media_lake_router,
    prefix='/media',
    tags=['Media Lake'],
    dependencies=[Depends(is_authenticated)]
)
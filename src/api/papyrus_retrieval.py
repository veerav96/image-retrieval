import logging
from typing import List
from uuid import UUID
from celery.result import AsyncResult
from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel, Field
from starlette.requests import Request
from src.tasks.workflow_tasks import papyrus_retrieval
from src.vision.utils import preprocess_image
from fastapi import HTTPException
import json


router = APIRouter(prefix='/papyrus', tags=['papyrus'])

log = logging.getLogger(__name__)


class ScheduleResponse(BaseModel):
    task_id: UUID = Field(
        title='Task ID',
        description='Processing papyrus retrieval task id than can be used to fetch the results when ready',
        examples=['some-unique-task-id'],
    )
    status: str = Field(
        title='Status', description='Initial status of the task', examples=['Papyrus Retrieval has started!']
    )


@router.post('/submit/', description='initiates a workflow to retrieve top k matches')
async def schedule_papyrus_retrieval(
    request: Request, coordinates: str = Form(...), image: UploadFile = File(...)
) -> ScheduleResponse:
    minio_client = request.app.state.minio_client

    try:
        coordinate_list = json.loads(coordinates)  # Parse coordinates from JSON string to List[List[float]]
        if not isinstance(coordinate_list, list):
            raise ValueError('Coordinates must be a list of lists.')
    except json.JSONDecodeError:
        raise ValueError('Invalid JSON format for coordinates.')

    image_content = await image.read()
    file_path = preprocess_image(image_content, coordinate_list, minio_client)
    log.info(f'file_path: {file_path}')
    task = papyrus_retrieval(file_path)  # Execute the workflow
    return ScheduleResponse(task_id=task.id, status='Papyrus Retrieval has started!')


class RetrieveResponse(BaseModel):
    request_id: UUID = Field(
        title='Estimation ID',
        description='Processing task ID that can be used to fetch the result when ready',
        examples=['123e4567-e89b-12d3-a456-426614174000'],  # Example as string UUID
    )
    query_status: str = Field(
        title='Query Status',
        description='Status of the computation',
        examples=['SUCCESS'],
    )

    query_result: List[str] = Field(
        title='Query Result',
        description='Result URLs or other information',
        examples=[['http://example.com/papyrus']],
        default=[],  # Set default to an empty list
    )


@router.get(
    '/result/{task_id}',
    description='Retrieve, previously scheduled, top k similar papyrus images for a given user query',
)
async def retrieve_papyrus(task_id: UUID) -> RetrieveResponse:
    task_result = AsyncResult(str(task_id))

    if task_result.status in ['PENDING', 'STARTED']:
        return RetrieveResponse(
            request_id=task_result.task_id,
            query_status=task_result.status,
            query_result=[],  # Empty result as it's not available yet
        )
    elif task_result.status == 'FAILURE':
        raise HTTPException(status_code=500, detail='Task failed to complete.')

    else:
        print(f'task_result.result {task_result.result}')
        return RetrieveResponse(
            request_id=task_result.task_id, query_status=task_result.status, query_result=task_result.result
        )

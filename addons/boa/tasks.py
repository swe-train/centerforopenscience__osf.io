import asyncio
import logging
from urllib import request
from urllib.error import HTTPError, URLError

from asgiref.sync import async_to_sync, sync_to_async
from boaapi.boa_client import BoaClient, BoaException
from boaapi.status import CompilerStatus, ExecutionStatus

from addons.boa import settings as boa_settings
from addons.boa.boa_error_code import BoaErrorCode
from framework import sentry
from framework.celery_tasks import app as celery_app
from osf.models import OSFUser
from osf.utils.fields import ensure_str, ensure_bytes
from website import settings as osf_settings
from website.mails import send_mail, ADDONS_BOA_JOB_COMPLETE, ADDONS_BOA_JOB_FAILURE

logger = logging.getLogger(__name__)


@celery_app.task(name='addons.boa.tasks.submit_to_boa')
def submit_to_boa(host, username, password, user_guid, project_guid, query_dataset,
                  query_file_name, file_full_path, query_download_url, output_upload_url):
    """
    Download Boa query file, submit it to Boa API, wait for Boa to finish the job
    and upload result output to OSF. Send success / failure emails notifications.

    A few Notes:
        * All the parameters must be verified by the caller.
        * Both the ``query_download_url`` and ``output_upload_url`` must be WB URL for two reasons:
            * It generates fewer requests between OSF and WB;
            * It has authentication passed via the headers securely.
        * Running asyncio in celery is tricky. Refer to the discussion below for details:
            * https://stackoverflow.com/questions/39815771/how-to-combine-celery-with-asyncio
    """
    async_to_sync(submit_to_boa_async)(host, username, password, user_guid, project_guid, query_dataset,
                                       query_file_name, file_full_path, query_download_url, output_upload_url)


async def submit_to_boa_async(host, username, password, user_guid, project_guid, query_dataset,
                              query_file_name, file_full_path, query_download_url, output_upload_url):
    """
    Download Boa query file, submit it to Boa API, wait for Boa to finish the job
    and upload result output to OSF. Send success / failure emails notifications.

    A couple of notes:
        * This is the async function that must be wrapped with ``async_to_sync`` by the caller
        * See notes in ``submit_to_boa()`` for details.
    """

    logger.debug('>>>>>>>> Task begins')
    user = await sync_to_async(OSFUser.objects.get)(guids___id=user_guid)
    cookie_value = (await sync_to_async(user.get_or_create_cookie)()).decode()
    project_url = f'{osf_settings.DOMAIN}{project_guid}/'

    logger.debug(f'Downloading Boa query file: user=[{user_guid}], project=[{project_guid}], '
                 f'file_name=[{query_file_name}], full_path=[{file_full_path}], url=[{query_download_url}] ...')
    download_request = request.Request(query_download_url)
    download_request.add_header('Cookie', f'{osf_settings.COOKIE_NAME}={cookie_value}')
    try:
        boa_query = ensure_str(request.urlopen(download_request).read())
    except (ValueError, HTTPError, URLError):
        message = f'Failed to download Boa query file: user=[{user_guid}], project=[{project_guid}], ' \
                  f'file_name=[{query_file_name}], full_path=[{file_full_path}], url=[{query_download_url}] ...'
        await sync_to_async(handle_error)(message, BoaErrorCode.UNKNOWN, user.username, user.fullname, project_url, query_file_name)
        return
    logger.info('Boa query successfully downloaded.')
    logger.debug(f'Boa query:\n########\n{boa_query}\n########')

    logger.debug('Boa client opened.')
    client = BoaClient(endpoint=host)
    logger.debug(f'Checking Boa credentials: boa_username=[{username}], boa_host=[{host}] ...')
    try:
        client.login(username, password)
    except BoaException:
        client.close()
        message = f'Boa login failed: boa_username=[{username}], boa_host=[{host}]!'
        await sync_to_async(handle_error)(message, BoaErrorCode.AUTHN_ERROR, user.username, user.fullname, project_url, query_file_name)
        return
    logger.info('Boa login completed.')

    logger.debug(f'Retrieving Boa dataset: dataset=[{query_dataset}] ...')
    try:
        dataset = client.get_dataset(query_dataset)
    except BoaException:
        client.close()
        message = f'Failed to retrieve or verify the target Boa dataset: dataset=[{query_dataset}]!'
        await sync_to_async(handle_error)(message, BoaErrorCode.UNKNOWN, user.username, user.fullname, project_url, query_file_name)
        return
    logger.info('Boa dataset retrieved.')

    logger.debug(f'Submitting the query to Boa API: boa_host=[{host}], dataset=[{query_dataset}] ...')
    try:
        boa_job = client.query(boa_query, dataset)
    except BoaException:
        client.close()
        message = f'Failed to submit the query to Boa API: : boa_host=[{host}], dataset=[{query_dataset}]!'
        await sync_to_async(handle_error)(message, BoaErrorCode.UNKNOWN, user.username, user.fullname, project_url, query_file_name)
        return
    logger.info('Query successfully submitted.')
    logger.debug(f'Waiting for job to finish: job_id = [{str(boa_job.id)}] ...')
    while boa_job.is_running():
        logger.debug(f'Boa job still running, waiting 10s: job_id = [{str(boa_job.id)}] ...')
        boa_job.refresh()
        await asyncio.sleep(10)
    if boa_job.compiler_status is CompilerStatus.ERROR:
        client.close()
        message = f'Boa job failed with compile error: job_id = [{str(boa_job.id)}]!'
        await sync_to_async(handle_error)(message, BoaErrorCode.QUERY_ERROR, user.username, user.fullname,
                                          project_url, query_file_name, boa_job.id)
        return
    elif boa_job.exec_status is ExecutionStatus.ERROR:
        client.close()
        message = f'Boa job failed with execution error: job_id = [{str(boa_job.id)}]!'
        await sync_to_async(handle_error)(message, BoaErrorCode.QUERY_ERROR, user.username, user.fullname,
                                          project_url, query_file_name, boa_job.id)
        return
    else:
        try:
            boa_job_output = boa_job.output()
        except BoaException:
            client.close()
            message = f'Boa job output is not available: job_id = [{str(boa_job.id)}]!'
            await sync_to_async(handle_error)(message, BoaErrorCode.UNKNOWN, user.username, user.fullname, project_url, query_file_name)
            return
        logger.info('Boa job finished.')
        logger.debug(f'Boa job output: job_id = [{str(boa_job.id)}]\n########\n{boa_job_output}\n########')
        client.close()
        logger.debug('Boa client closed.')

    output_file_name = query_file_name.replace('.boa', boa_settings.OUTPUT_FILE_SUFFIX)
    logger.debug(f'Uploading Boa query output to OSF: name=[{output_file_name}], upload_url=[{output_upload_url}] ...')
    try:
        # TODO: either let the caller v1 view provide the full upload URL w/ all query params
        upload_request = request.Request(f'{output_upload_url}&name={output_file_name}')
        upload_request.method = 'PUT'
        upload_request.data = ensure_bytes(boa_job_output)
        upload_request.add_header('Cookie', f'{osf_settings.COOKIE_NAME}={cookie_value}')
        request.urlopen(upload_request)
    except (ValueError, HTTPError, URLError):
        message = f'Failed to upload query output file to OSF: ' \
                  f'name=[{output_file_name}], user=[{user_guid}], url=[{output_upload_url}]!'
        await sync_to_async(handle_error)(message, BoaErrorCode.UPLOAD_ERROR, user.username, user.fullname,
                                          project_url, query_file_name, boa_job.id)
        return

    logger.info('Successfully uploaded query output to OSF.')
    logger.debug('Task ends <<<<<<<<')
    await sync_to_async(send_mail)(
        mail=ADDONS_BOA_JOB_COMPLETE,
        to_addr=user.username,
        fullname=user.fullname,
        query_file_name=query_file_name,
        output_file_name=output_file_name,
        job_id=boa_job.id,
        project_url=project_url,
        boa_job_list_url=boa_settings.BOA_JOB_LIST_URL,
        boa_support_email=boa_settings.BOA_SUPPORT_EMAIL,
        osf_support_email=osf_settings.OSF_SUPPORT_EMAIL,
    )
    return


def handle_error(message, code, username, fullname, project_url, query_file_name, job_id=None):
    """Handle Boa and WB API errors and send emails.
    """
    logger.error(message)
    sentry.log_message(message, skip_session=True)
    send_mail(
        to_addr=username,
        mail=ADDONS_BOA_JOB_FAILURE,
        fullname=fullname,
        code=code,
        message=message,
        query_file_name=query_file_name,
        job_id=job_id,
        project_url=project_url,
        boa_job_list_url=boa_settings.BOA_JOB_LIST_URL,
        osf_support_email=osf_settings.OSF_SUPPORT_EMAIL,
    )

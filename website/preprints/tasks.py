import logging

from framework import sentry
from framework.exceptions import HTTPError
from framework.celery_tasks import app as celery_app
from framework.postcommit_tasks.handlers import enqueue_postcommit_task, get_task_from_postcommit_queue


logger = logging.getLogger(__name__)


@celery_app.task(ignore_results=True, max_retries=5, default_retry_delay=60)
def on_preprint_updated(preprint_id, saved_fields=None, **kwargs):
    # WARNING: Only perform Read-Only operations in an asynchronous task, until Repeatable Read/Serializable
    # transactions are implemented in View and Task application layers.
    from osf.models import Preprint
    preprint = Preprint.load(preprint_id)
    if not preprint:
        return
    need_update = bool(preprint.SEARCH_UPDATE_FIELDS.intersection(saved_fields or {}))

    if need_update:
        preprint.update_search()

    if should_update_preprint_identifiers(preprint, saved_fields):
        update_or_create_preprint_identifiers(preprint)


def should_update_preprint_identifiers(preprint, saved_fields):
    # Only update identifier metadata iff...
    return (
        # DOI didn't just get created
        preprint and preprint.date_published and
        not (saved_fields and 'preprint_doi_created' in saved_fields) and
        # preprint isn't QA test
        preprint.should_request_identifiers
    )


def update_or_create_preprint_identifiers(preprint):
    try:
        preprint.request_identifier_update(category='doi')
    except HTTPError as err:
        sentry.log_exception()
        sentry.log_message(err.args[0])


def update_or_enqueue_on_preprint_updated(preprint_id, saved_fields=None):
    task = get_task_from_postcommit_queue(
        'website.preprints.tasks.on_preprint_updated',
        predicate=lambda task: task.kwargs['preprint_id'] == preprint_id
    )
    if task:
        task.kwargs['saved_fields'] = list(set(task.kwargs['saved_fields']).union(saved_fields))
    else:
        enqueue_postcommit_task(
            on_preprint_updated,
            (),
            {
                'preprint_id': preprint_id,
                'saved_fields': saved_fields
            },
            celery=True
        )

import logging

from django.core.management.base import BaseCommand

from osf.models import CedarMetadataTemplate
from osf.external.cedar.client import CedarClient
from osf.external.cedar.exceptions import CedarClientError

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        try:
            ids = CedarClient().retrieve_all_template_ids()
        except CedarClientError as e:
            logger.error(f'Unable to retrieve all cedar template ids: e={e.reason}')
            return

        fetched = set()
        failed = set()
        for cedar_id in ids:
            try:
                template = CedarClient().retrieve_template_by_id(cedar_id)
            except CedarClientError as e:
                logger.error(f'Unable to retrieve the cedar template: id={cedar_id}, e={e.reason}')
                failed.add(cedar_id)
                continue
            else:
                fetched.add(cedar_id)
            schema_name = template['schema:name']
            pav_last_updated_on = template['pav:lastUpdatedOn']
            existing_versions = CedarMetadataTemplate.objects.filter(cedar_id=cedar_id)
            if existing_versions:
                latest_version = existing_versions.order_by('-template_version').first()
                if pav_last_updated_on != latest_version.template['pav:lastUpdatedOn']:
                    # New version should be inactive
                    CedarMetadataTemplate.objects.create(
                        schema_name=schema_name,
                        template=template,
                        cedar_id=cedar_id,
                        active=False,
                        template_version=latest_version.template_version + 1
                    )
            else:
                # Initial version should be active
                CedarMetadataTemplate.objects.create(
                    schema_name=schema_name,
                    template=template,
                    cedar_id=cedar_id,
                    template_version=1
                )

        logger.info(f'fetched ({len(fetched)})={fetched}')
        logger.error(f'failed ({len(failed)})={failed}')

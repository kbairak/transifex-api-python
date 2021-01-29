import time

import jsonapi

from jsonapi.exceptions import JsonApiException

_api = jsonapi.JsonApi(host="https://rest.api.transifex.com")


def setup(auth, host=None, headers=None):
    _api.setup(host=host, auth=auth, headers=headers)


@_api.register
class User(jsonapi.Resource):
    TYPE = "users"


@_api.register
class Organization(jsonapi.Resource):
    TYPE = "organizations"


@_api.register
class Language(jsonapi.Resource):
    TYPE = "languages"


@_api.register
class Project(jsonapi.Resource):
    TYPE = "projects"


@_api.register
class ProjectWebhook(jsonapi.Resource):
    TYPE = "project_webhooks"


@_api.register
class Resource(jsonapi.Resource):
    TYPE = "resources"

    def purge(self):
        count = 0
        # Instead of filter, if Resource had a plural relationship to
        # ResourceString, we could do `self.fetch('resource_strings')`
        for page in list(ResourceString.filter(resource=self).all_pages()):
            count += len(page)
            ResourceString.bulk_delete(page)
        return count


@_api.register
class ResourceString(jsonapi.Resource):
    TYPE = "resource_strings"


@_api.register
class ResourceStringsAsyncUpload(jsonapi.Resource):
    TYPE = "resource_strings_async_uploads"

    @classmethod
    def upload(cls, resource, content, interval=5):
        """ Upload source content with multipart/form-data.

            :param resource: A (transifex) Resource instance or ID
            :param content: A string or file-like object
            :param interval: How often (in seconds) to poll for the completion
                             of the upload job
        """

        if isinstance(resource, Resource):
            resource = resource.id

        upload = cls.create_with_form(data={'resource': resource},
                                      files={'content': content})

        while True:
            if hasattr(upload, 'errors') and len(upload.errors) > 0:
                errors = [{
                    'code': e['code'],
                    'detail': e['detail'],
                    'title': e['detail'],
                    'status': '409'} for e in upload.errors]
                raise JsonApiException(409, errors)

            if upload.redirect:
                return upload.follow()
            if (hasattr(upload, 'attributes')
                    and upload.attributes.get("details")):
                return upload.attributes.get("details")

            time.sleep(interval)
            upload.reload()


@_api.register
class ResourceStringComment(jsonapi.Resource):
    TYPE = "resource_string_comments"


@_api.register
class I18nFormat(jsonapi.Resource):
    TYPE = "i18n_formats"


@_api.register
class ContextScreenshot(jsonapi.Resource):
    TYPE = "context_screenshots"


@_api.register
class ContextScreenshotMap(jsonapi.Resource):
    TYPE = "context_screenshot_map"


@_api.register
class OrganizationActivityReportsAsyncDownload(jsonapi.Resource):
    TYPE = "organization_activity_reports_async_downloads"


@_api.register
class ProjectActivityReportsAsyncDownload(jsonapi.Resource):
    TYPE = "project_activity_reports_async_downloads"


@_api.register
class ResourceActivityReportsAsyncDownload(jsonapi.Resource):
    TYPE = "resource_activity_reports_async_downloads"


@_api.register
class ResourceLanguageStats(jsonapi.Resource):
    TYPE = "resource_language_stats"


@_api.register
class ResourceTranslation(jsonapi.Resource):
    TYPE = "resource_translations"


@_api.register
class ResourceTranslationsAsyncDownload(jsonapi.Resource):
    TYPE = "resource_translations_async_downloads"

    @classmethod
    def download(cls, interval=5, *args, **kwargs):
        download = cls.create(*args, **kwargs)
        while True:
            if hasattr(download, 'errors') and len(download.errors) > 0:
                errors = [{'code': e['code'],
                           'detail': e['detail'],
                           'title': e['detail'],
                           'status': '409'}
                          for e in download.errors]
                raise JsonApiException(409, errors)
            if download.redirect:
                return download.redirect
            time.sleep(interval)
            download.reload()


@_api.register
class ResourceTranslationsAsyncUpload(Resource):
    TYPE = "resource_translations_async_uploads"

    @classmethod
    def upload(cls, resource, content, language, interval=5,
               file_type='default'):
        """ Upload translation content with multipart/form-data.

            :param resource: A (transifex) Resource instance or ID
            :param content: A string or file-like object
            :param language: A (transifex) Language instance or ID
            :param interval: How often (in seconds) to poll for the completion
                             of the upload job
            :param file_type: The content file type
        """

        if isinstance(resource, Resource):
            resource = resource.id

        upload = cls.create_with_form(data={'resource': resource,
                                            'language': language,
                                            'file_type': file_type},
                                      files={'content': content})

        while True:
            if hasattr(upload, 'errors') and len(upload.errors) > 0:
                errors = [{
                    'code': e['code'],
                    'detail': e['detail'],
                    'title': e['detail'],
                    'status': '409'} for e in upload.errors]
                raise JsonApiException(409, errors)

            if upload.redirect:
                return upload.follow()
            if (hasattr(upload, 'attributes')
                    and upload.attributes.get("details")):
                return upload.attributes.get("details")

            time.sleep(interval)
            upload.reload()


@_api.register
class TeamMembership(jsonapi.Resource):
    TYPE = "team_memberships"


@_api.register
class Team(jsonapi.Resource):
    TYPE = "teams"


@_api.register
class TmxAsyncdownload(jsonapi.Resource):
    TYPE = "tmx_async_downloads"

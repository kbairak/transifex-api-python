import time

import jsonapi

from jsonapi.exceptions import JsonApiException


class TransifexApi(jsonapi.JsonApi):
    HOST = "https://rest.api.transifex.com"


@TransifexApi.register
class Organization(jsonapi.Resource):
    TYPE = "organizations"


@TransifexApi.register
class Team(jsonapi.Resource):
    TYPE = "teams"


@TransifexApi.register
class Project(jsonapi.Resource):
    TYPE = "projects"


@TransifexApi.register
class Language(jsonapi.Resource):
    TYPE = "languages"


@TransifexApi.register
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


@TransifexApi.register
class ResourceString(jsonapi.Resource):
    TYPE = "resource_strings"


@TransifexApi.register
class ResourceTranslation(jsonapi.Resource):
    TYPE = "resource_translations"
    EDITABLE = ["strings", 'reviewed', "proofread"]


@TransifexApi.register
class ResourceStringsAsyncUpload(jsonapi.Resource):
    TYPE = "resource_strings_async_uploads"

    @classmethod
    def upload(cls, resource, content, interval=5, sync=True):
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

            if not sync:
                return upload
            if upload.redirect:
                return upload.follow()
            if (hasattr(upload, 'attributes')
                    and upload.attributes.get("details")):
                return upload.attributes.get("details")

            time.sleep(interval)
            upload.reload()


@TransifexApi.register
class ResourceTranslationsAsyncUpload(Resource):
    TYPE = "resource_translations_async_uploads"

    @classmethod
    def upload(cls, resource, content, language, interval=5,
               file_type='default', sync=True):
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

            if not sync:
                return upload
            if upload.redirect:
                return upload.follow()
            if (hasattr(upload, 'attributes')
                    and upload.attributes.get("details")):
                return upload.attributes.get("details")

            time.sleep(interval)
            upload.reload()


@TransifexApi.register
class User(jsonapi.Resource):
    TYPE = "users"


@TransifexApi.register
class TeamMembership(jsonapi.Resource):
    TYPE = "team_memberships"


@TransifexApi.register
class ResourceLanguageStats(jsonapi.Resource):
    TYPE = "resource_language_stats"


@TransifexApi.register
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


# This is our global object
transifex_api = TransifexApi()

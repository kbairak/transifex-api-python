from jsonapi import setup, Resource as JsonApiResource  # noqa


class Organization(JsonApiResource):
    TYPE = "organizations"


class Project(JsonApiResource):
    TYPE = "projects"


class Language(JsonApiResource):
    TYPE = "languages"


class Resource(JsonApiResource):
    TYPE = "resources"

    def purge(self):
        count = 0
        for page in list(ResourceString.filter(resource=self).all_pages()):
            count += len(page)
            ResourceString.bulk_delete(page)
        return count

        # If there was a 'resource_strings' plural relationship on Resource, we
        # could do:
        # self.fetch('resource_strings')
        # for page in list(self.resource_strings.all_pages()):
        #     ResourceString.bulk_delete(page)


class ResourceString(JsonApiResource):
    TYPE = "resource_strings"


class ResourceTranslation(JsonApiResource):
    TYPE = "resource_translations"
    EDITABLE = ["strings", 'reviewed', "proofread"]


class ResourceStringsAsyncUpload(JsonApiResource):
    TYPE = "resource_strings_async_uploads"

    @classmethod
    def upload(cls, resource, content):
        """ Upload source content with multipart/form-data.

            :param resource: A (transifex) Resource instance or ID
            :param content: A string or file-like object
        """

        if isinstance(resource, Resource):
            resource = resource.id
        return cls.create_with_form(data={'resource': resource},
                                    files={'content': content})

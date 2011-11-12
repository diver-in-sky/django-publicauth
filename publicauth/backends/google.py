from __future__ import absolute_import

from openid.extensions.ax import FetchRequest, AttrInfo, FetchResponse

from publicauth.backends.openid import OpenIDBackend
from publicauth import settings


class GoogleBackend(OpenIDBackend):
    
    def get_extra_data(self, resp):
        return FetchResponse.fromSuccessResponse(resp)

    def extract_data(self, extra, backend_field, form_field):
        return {form_field: extra.getSingle(settings.AX_URIS[backend_field], '')}


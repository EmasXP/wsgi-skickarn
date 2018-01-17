import os
import mimetypes
from werkzeug.datastructures import Headers
from werkzeug.http import HTTP_STATUS_CODES
from datetime import datetime

"""
TODO
- Mimic werkzeug Response construct order
- self.filename can be True
- Setting use_wsgi_file_wrapper?
- Internet Explorer tweaks?
- multipart/byteranges
- 416 support

TESTA:
- wsgi.file_wrapper
- File close på wsgi.file_wrapper
- Python2
- Displosition and filename

INFORMATIVE LINKS
https://github.com/pallets/werkzeug/blob/master/werkzeug/wsgi.py
http://modwsgi.readthedocs.io/en/develop/user-guides/file-wrapper-extension.html
https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range
https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/416
https://www.python.org/dev/peps/pep-0333/#optional-platform-specific-file-handling
https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-Range
"""


class FileResponse(object):

    def __init__(self,
                 f,
                 disposition=None,
                 filename=None,
                 block_size=16384,
                 mimetype=None,
                 headers={},
                 auto_etag=False
                 ):
        self.f = f
        self.disposition = disposition
        self.filename = filename
        self.block_size = block_size
        self.mimetype = mimetype
        self.headers = Headers(headers)
        self.auto_etag = auto_etag

        self._stat = None
        self._last_modified = None

    def _get_filename(self):
        if self.filename is not None:
            return self.filename
        return self.f.name  # TODO: Check if this is correct

    def _get_mimetype(self):
        if self.mimetype is not None:
            return self.mimetype
        return mimetypes.guess_type(self.f.name)[0]

    def _get_disposition(self):
        if self.disposition is not None:
            return self.disposition
        return "attachment"

    def _get_stat(self):
        if self._stat is None:
            self._stat = os.fstat(self.f.fileno())
        return self._stat

    def _get_filesize(self):
        return self._get_stat().st_size

    def _get_last_modified(self):
        if self._last_modified is not None:
            return self._last_modified
        if "Last-Modified" in self.headers:
            return self.headers["Last-Modified"]
        epoch = self._get_stat().st_mtime
        dt = datetime.utcfromtimestamp(epoch)
        self._last_modified = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        return self._last_modified

    def _get_etag(self):
        return '"{}"'.format(self._get_stat().st_mtime)

    def _check_if_range(self, environ):
        if "HTTP_IF_RANGE" not in environ:
            return True

        ifrange = environ["HTTP_IF_RANGE"]

        if not self.auto_etag and self.headers.get("Etag") == ifrange:
            return True

        if self.auto_etag and ifrange == self._get_etag():
            return True

        if ifrange == self._get_last_modified():
            return True

        return False

    def _build_content_disposition(self):
        if self.disposition is not None and (self.filename is None
                                             or self.filename is False):
            return self._get_disposition()

        if self.filename is not None and self.filename is not False:
            return "{}; filename=\"{}\"".format(
                self._get_disposition(),
                self._get_filename()
            )

        return None

    def _get_range_data(self, environ, size):
        start = 0
        end = size - 1

        # Not a range request, sending 200
        if "HTTP_RANGE" not in environ:
            return 200, start, end, size

        # If-Range "failed"
        if not self._check_if_range(environ):
            return 200, start, end, size

        unit_ranges = environ["HTTP_RANGE"].split("=")
        # Missing ranges ("bytes="), or not "bytes". Sending 200
        if len(unit_ranges) <= 1 or unit_ranges[0] != "bytes":
            return 200, start, end, size

        ranges = unit_ranges[1].split(",")
        ran = ranges[0].split("-")
        # Too few params in range (for example "10" not "10-20")
        if len(ran) <= 1:
            return 200, start, end, size

        try:
            # Example: -10
            if len(ran[0]) == 0:
                start = end - int(ran[1]) + 1
            # Example: 10-
            elif len(ran[1]) == 0:
                start = int(ran[0])
            # Start byte is after end byte (20-10). Sending 200
            elif int(ran[0]) > int(ran[1]):
                return 200, start, end, size
            # Example: 10-20
            else:
                start = int(ran[0])
                end = int(ran[1])
        except Exception:
            # Most likely happens if the range did not contain a number
            # Example: 10-abc
            return 200, start, end, size

        return (
            206,
            start,
            end,
            (end - start) + 1
        )

    def _build_headers(self, status, start, end, length, size):
        headers = self.headers.copy()

        if status == 206:
            headers["Content-Range"] = "bytes {}-{}/{}".format(
                start,
                end,
                size
            )

        content_disposition = self._build_content_disposition()
        if content_disposition is not None:
            headers["Content-Disposition"] = content_disposition

        if self.auto_etag:
            headers["Etag"] = self._get_etag()

        headers["Accept-Ranges"] = "bytes"
        headers["Content-Type"] = self._get_mimetype()
        headers["Content-Length"] = length
        headers["Last-Modified"] = self._get_last_modified()

        return headers

    def __call__(self, environ, start_response):
        size = self._get_filesize()
        status, start, end, length = self._get_range_data(environ, size)

        headers = self._build_headers(status, start, end, length, size)

        start_response(
            '{} {}'.format(
                status,
                HTTP_STATUS_CODES[status]
            ),
            headers.to_wsgi_list()
        )

        if status == 200 and "wsgi.file_wrapper" in environ:
            print("wsgi.file_wrapper")
            return environ["wsgi.file_wrapper"](self.f, self.block_size)

        self.f.seek(start)

        return self._generator(end)

    def _generator(self, end):
        with self.f:
            block = self.block_size
            while self.f.tell() <= end:
                pos = self.f.tell()
                if pos + block > end:
                    block = end - pos + 1
                yield self.f.read(block)

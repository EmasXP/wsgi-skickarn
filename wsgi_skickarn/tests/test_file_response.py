"""
MISSING TESTS:
- Bad ranges
    - "10-asd"
    - "asd-20"
    - "-"
    - "asd"
    - ""
    - Not "bytes"
- Auto filename
- Set filename
- Set disposition
- Set mimetype
- Set etag
- Auto etag
- Block size
- wsgi.file_wrapper
"""

import unittest
import os
from datetime import datetime
from wsgi_skickarn import FileResponse

TESTDATA_FILENAME = os.path.join(
    os.path.dirname(__file__),
    'test_data/sample_data.txt'
)

with open(TESTDATA_FILENAME, "rb") as fh:
    TESTDATA_CONTENT = fh.read()
    TESTDATA_FILESIZE = len(TESTDATA_CONTENT)


class DummyStartResponse(object):
    def __init__(self):
        self._http_code = None
        self._headers = None

    def __call__(self, http_code, headers):
        self._http_code = http_code
        self._headers = headers

    def get_http_code(self):
        return self._http_code

    def get_headers(self):
        return self._headers

    def get_header(self, header):
        for k, v in self._headers:
            if k == header:
                return v
        return None


def make_dummy_request(environ={}, headers={}):
    r = FileResponse(open(TESTDATA_FILENAME, "rb"), headers=headers)
    start_response = DummyStartResponse()
    gener = r(environ, start_response)
    outdata = b""
    for data in gener:
        outdata += data
    return outdata, start_response


class FileResponseTests(unittest.TestCase):
    def test_simple_request_response(self):
        data, start_response = make_dummy_request()

        self.assertEqual(start_response.get_http_code(), "200 OK")

        self.assertEqual(
            int(start_response.get_header("Content-Length")),
            TESTDATA_FILESIZE
        )

        self.assertEqual(
            int(start_response.get_header("Content-Length")),
            len(data)
        )

        self.assertEqual(TESTDATA_CONTENT, data)

        self.assertEqual(start_response.get_header("Accept-Ranges"), "bytes")

        self.assertEqual(
            start_response.get_header("Content-Type"),
            "text/plain"
        )

    def test_last_modified(self):
        _data, start_response = make_dummy_request()
        stat = os.stat(TESTDATA_FILENAME)
        epoch = stat.st_mtime
        dt = datetime.utcfromtimestamp(epoch)
        last_modified = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        self.assertEqual(
            start_response.get_header("Last-Modified"),
            last_modified
        )

    def test_last_modified_header(self):
        dt = "Strange datetime is allowed"
        _data, start_response = make_dummy_request(headers={
            "Last-Modified": dt
        })
        self.assertEqual(start_response.get_header("Last-Modified"), dt)

    def test_range_zero_to_ten(self):
        data, start_response = make_dummy_request(environ={
            "HTTP_RANGE": "bytes=0-10",
        })

        self.assertEqual(start_response.get_http_code(), "206 Partial Content")

        self.assertEqual(
            int(start_response.get_header("Content-Length")),
            11
        )

        self.assertEqual(
            int(start_response.get_header("Content-Length")),
            len(data)
        )

        self.assertEqual(TESTDATA_CONTENT[:11], data)

        self.assertEqual(start_response.get_header("Accept-Ranges"), "bytes")

        self.assertEqual(
            start_response.get_header("Content-Type"),
            "text/plain"
        )

        self.assertEqual(
            start_response.get_header("Content-Range"),
            "bytes 0-10/" + str(len(TESTDATA_CONTENT))
        )

    def test_range_ten_to_twentyone(self):
        data, start_response = make_dummy_request(environ={
            "HTTP_RANGE": "bytes=10-21",
        })

        self.assertEqual(start_response.get_http_code(), "206 Partial Content")

        self.assertEqual(
            int(start_response.get_header("Content-Length")),
            12
        )

        self.assertEqual(
            int(start_response.get_header("Content-Length")),
            len(data)
        )

        self.assertEqual(TESTDATA_CONTENT[10:22], data)

        self.assertEqual(start_response.get_header("Accept-Ranges"), "bytes")

        self.assertEqual(
            start_response.get_header("Content-Type"),
            "text/plain"
        )

        self.assertEqual(
            start_response.get_header("Content-Range"),
            "bytes 10-21/" + str(len(TESTDATA_CONTENT))
        )

    def test_range_ten_to_none(self):
        data, start_response = make_dummy_request(environ={
            "HTTP_RANGE": "bytes=10-",
        })

        self.assertEqual(start_response.get_http_code(), "206 Partial Content")

        self.assertEqual(
            int(start_response.get_header("Content-Length")),
            len(TESTDATA_CONTENT) - 10
        )

        self.assertEqual(
            int(start_response.get_header("Content-Length")),
            len(data)
        )

        self.assertEqual(TESTDATA_CONTENT[10:], data)

        self.assertEqual(start_response.get_header("Accept-Ranges"), "bytes")

        self.assertEqual(
            start_response.get_header("Content-Type"),
            "text/plain"
        )

        self.assertEqual(
            start_response.get_header("Content-Range"),
            "bytes 10-{}/{}".format(
                len(TESTDATA_CONTENT) - 1,
                len(TESTDATA_CONTENT)
            )
        )

    def test_range_none_to_ten(self):
        data, start_response = make_dummy_request(environ={
            "HTTP_RANGE": "bytes=-10",
        })

        self.assertEqual(start_response.get_http_code(), "206 Partial Content")

        self.assertEqual(
            int(start_response.get_header("Content-Length")),
            10
        )

        self.assertEqual(
            int(start_response.get_header("Content-Length")),
            len(data)
        )

        self.assertEqual(TESTDATA_CONTENT[-10:], data)

        self.assertEqual(start_response.get_header("Accept-Ranges"), "bytes")

        self.assertEqual(
            start_response.get_header("Content-Type"),
            "text/plain"
        )

        self.assertEqual(
            start_response.get_header("Content-Range"),
            "bytes {}-{}/{}".format(
                len(TESTDATA_CONTENT) - 10,
                len(TESTDATA_CONTENT) - 1,
                len(TESTDATA_CONTENT)
            )
        )

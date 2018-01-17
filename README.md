# wsgi-skickarn

wsgi-skickarn is a (Python) WSGI file response library with support for the `Content-Range` HTTP header. It can easily be used in Flask and probably other frameworks based on WSGI.


## Flask example

```python
from flask import Flask
from wsgi_skickarn import FileResponse

app = Flask(__name__)

@app.route("/")
def index():
    f = open("toystory.mp4", "rb")
    return FileResponse(f)

if __name__ == "__main__":
    app.run()
```

## Pure WSGI example

```python
from wsgi_skickarn import FileResponse

def app(environ, start_response):
    f = open("toystory.mp4", "rb")
    return FileResponse(f)(environ, start_response)
```

## Dependencies

werkzeug, but that's it.


## What it does not have

* Support the `416` HTTP code. This might come in the future as a setting. 
  <https://tools.ietf.org/html/rfc7233#section-4.4> says:

  > ```
  > Note: Because servers are free to ignore Range, many
  >       implementations will simply respond with the entire selected
  >       representation in a 200 (OK) response.  That is partly because
  >       most clients are prepared to receive a 200 (OK) to complete the
  >       task (albeit less efficiently) and partly because clients might
  >       not stop making an invalid partial request until they have
  >       received a complete representation.  Thus, clients cannot depend
  >       on receiving a 416 (Range Not Satisfiable) response even when it
  >       is most appropriate.
  > ```

* `multipart/byteranges` support. I'm not sure how much this is used by clients, but I'll probably add support for this in the future. Parts of the structure of the code needs to be re-thought.



## TODO

* Write tests. This is the main priority. I want to have tests for everything existing before I start making changes.
* `wsgi.file_wrapper` is only used for `200 OK` responses. Investigate if it's worth making a wrapper around the file for `206` responses and use `wsgi.file_wrapper`. I think the wrapper is only needed for `206` via `wsgi.file_wrapper` though, to not waste resources in vain.
* I've seen that some implementation of `Content-Range` in different languages have Internet Explorer fixes. I need to investigate this and see if something needs to be implemented.
* PyPI package. I have no experience with this, though.
* More things in `setup.py`.

## To write

- Uses "wsgi.file_wrapper" for `200 OK` responses if available.
- Auto closing file
- Custom headers
- Configuration
  - Examples. Send to constructor, alter object.
- If-Range
# throttler
This is a threaded throttle/retry function that is thread safe, completely implemented in software. It works in Python 2.7 and 3.6.

Use of this library is not recommended for larger web applications, as they should most likely use a queue service to deal with calls in a more scalable way.

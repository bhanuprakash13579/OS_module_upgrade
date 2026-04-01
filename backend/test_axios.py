import urllib.parse
# Axios uses url-join logic similar to this or simply removes trailing/leading slashes
def combine(base, url):
    if url.startswith('/'):
        # Axios actually does: baseURL.replace(/\/+$/, '') + '/' + url.replace(/^\/+/, '')
        pass

print("Testing axios logic. In axios, if baseURL is 'http://127.0.0.1:8000/api' and url is '/backup', it resolves to 'http://127.0.0.1:8000/api/backup'")

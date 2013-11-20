import requests
import re
import urlparse
import os.path
import time
import hashlib
import imboclient.url.signed as url_signature
import json
from imboclient.url import image
from imboclient.url import images
from imboclient.url import user
from imboclient.url import status
from imboclient.url import metadata

class Client:

    def __init__(self, server_urls, public_key, private_key, driver = None, version = None):
        self.server_urls = self._parse_urls(server_urls)
        self._public_key = public_key
        self._private_key = private_key
        self._driver = driver
        self._version = version

    @property
    def driver(self, value):
        self._driver = value

    @property
    def metadata(self):
        return self._metadata;

    def metadata_url(self, image_identifier):
        return metadata.UrlMetadata(self.server_urls[0], self._public_key, self._private_key, image_identifier).url()

    def status_url(self):
        return status.UrlStatus(self.server_urls[0], self._public_key, self._private_key).url()

    def user_url(self):
        return user.UrlUser(self.server_urls[0], self._public_key, self._private_key).url()

    def images_url(self):
        return images.UrlImages(self.server_urls[0], self._public_key, self._private_key).url()

    def image_url(self, image_identifier):
        host = self._host_for_image_identifier(image_identifier)
        return image.UrlImage(host, self._public_key, self._private_key, image_identifier).url()

    def add_image(self, path):
        image_file_data = self._image_file_data(path)
        signed_url = self._signed_url('PUT', self.image_url(self.image_identifier(path)))
        return requests.put(signed_url, image_file_data)

    def _signed_url(self, method, url):
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return url_signature.Signed(
                self._public_key,
                self._private_key,
                method,
                url,
                timestamp).str()

    def add_image_from_string(self, image):
        image_identifier = self.image_identifier_from_string(image)
        image_url = self.image_url(image_identifier)
        signed_image_url = self._signed_url('PUT', image_url)
        requests.put(signed_image_url, image)

    def add_image_from_url(self, image):
        image_url = image.url()
        image_data = requests.get(image_url)
        return self.add_image_from_string(image_url, image_data)

    def image_exists(self, path):
        image_identifier = self.image_identifier(path)
        return self.image_identifier_exists(image_identifier)

    def image_identifier_exists(self, image_identifier):
        result = self.head_image(image_identifier)
        return result.status_code == requests.codes.ok

    def head_image(self, image_identifier):
        response = requests.head(self.image_url(image_identifier))
        return response

    def delete_image(self, image_identifier):
        response = requests.delete(self.image_url(image_identifier))
        return response

    def edit_metadata(self, image_identifier, metadata):
        edit_metadata_url = self.metadata_url()
        edit_metadata_url_signed = self._signed_url('POST', edit_metadata_url)
        metadata = json.dumps(metadata)

        return requests.post(edit_metadata_url_signed, data = metadata, headers = {'Content-Type': 'application/json', 'Content-Length': len(metadata), 'Content-MD5': hashlib.md5(metadata).hexdigest()})

    def replace_metadata(self, image_identifier, metadata):
        edit_metadata_url = self.metadata_url()
        edit_metadata_url_signed = self._signed_url('PUT', edit_metadata_url)
        metadata = json.dumps(metadata)

        return requests.put(edit_metadata_url_signed, data = metadata, headers = {'Content-Type': 'application/json', 'Content-Length': len(metadata), 'Content-MD5': hashlib.md5(metadata).hexdigest()})

    def delete_metadata(self, image_identifier):
        delete_metadata_url = self.metadata_url()
        delete_metadata_url_signed = self._signed_url('DELETE', delete_metadata_url)
        return requests.delete(delete_metadata_url_signed)

    def num_images(self):
        user_url = self.user_url()
        user_data = requests.get(user_url)
        user_data_decoded = json.loads(user_data.text)
        return user_data_decoded['numImages']

    def images(self, query = None):
        images_url = images.UrlImages(self.server_urls[0], self._public_key, self._private_key)

        if query:
            images_url.add_query(query)

        images_data = requests.get(images_url.url())
        images_data_decoded = json.loads(images_data.text)
        return images_data_decoded

    def image_data(self, image_identifier):
        return

    def image_data_from_url(self, url):
        return requests.get(url.url()).text

    def image_properties_from_url(self, url):
        return

    def image_properties(self, image_identifier):
        return

    def image_identifier(self, path):
        if self._validate_local_file(path):
            return self._generate_image_identifier(open(path).read())

        raise ValueError("Either the path is invalid or empty file")

    def _validate_local_file(self, path):
        return os.path.isfile(path) and os.path.getsize(path) > 0

    def _generate_image_identifier(self, content):
        return hashlib.md5(content).hexdigest()

    def _host_for_image_identifier(self, image_identifier):
        dec = int(image_identifier[0] + image_identifier[1], 16)
        return self.server_urls[dec % len(self.server_urls)]

    def image_identifier_from_string(self, image):
        return self._generate_image_identifier(image)

    def server_status(self):
        url = self.status_url()
        status_data = requests.get(url)
        status_data_decoded = json.loads(status_data.text)
        return status_data_decoded

    def user_info(self):
        url = self.user_url()
        user_data = requests.get(url)
        user_data_decoded = json.loads(user_data.text)
        return user_data_decoded

    def _image_file_data(self, path):
        return open(path).read()

    def _parse_urls(self, urls):
        def should_remove_port(self, url_parts):
            return parts.port and (parts.scheme == 'http' and parts.port == 80 or (parts.scheme == 'https' and parts.port == 443))

        parsed_urls = []
        pattern = re.compile("https?://")

        for url in urls:
            if not pattern.match(url):
                parsed_urls.append('http://' + url)

            parts = urlparse.urlparse(url)

            if should_remove_port(self, parts):
                url = parts.scheme + '://' + parts.hostname + '/' + parts.path

            parsed_urls.append(url.rstrip('/'))

        return parsed_urls


    class ParsedUrl:
        def __init__(self, scheme, host, port):
            self.scheme = scheme
            self.host = host
            self.port = port



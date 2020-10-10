# based on https://raw.githubusercontent.com/kneufeld/minio-put/master/minio-put.py

import os
import sys
import glob
import argparse
import datetime
import urllib.request

def get_headers(method, key, secret, host, bucket, file_name):
    resource     = f"/{bucket}/{file_name}"
    content_type = "application/octet-stream"
    date         = tznow().strftime('%a, %d %b %Y %X %z')
    _signature   = f"{method}\n\n{content_type}\n{date}\n{resource}"
    signature    = sig_hash(secret, _signature)

    return {
        'Host': host,
        'Date': date, # eg. Sat, 03 Mar 2018 10:11:16 -0700
        'Content-Type': content_type,
        'Authorization': f"AWS {key}:{signature}",
    }

def tznow():
    def utc_to_local(utc_dt):
        return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

    ts = datetime.datetime.utcnow()
    return utc_to_local(ts)


# based on: https://gist.github.com/heskyji/5167567b64cb92a910a3
def sig_hash(secret, sig):
    import hashlib
    import hmac
    import base64

    #signature=`echo -en ${sig} | openssl sha1 -hmac ${secret} -binary | base64`

    secret     = bytes(secret, 'UTF-8')
    sig        = bytes(sig, 'UTF-8')

    digester   = hmac.new(secret, sig, hashlib.sha1)
    signature1 = digester.digest()
    signature2 = base64.standard_b64encode(signature1)
    # signature2 = base64.urlsafe_b64encode(signature1)

    return str(signature2, 'UTF-8')

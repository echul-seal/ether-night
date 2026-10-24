#!/bin/bash
# pin_upload.sh FILE 'SIGNED_URL'  -> uploads a file to a Pinata presigned URL (multipart POST), prints the JSON (cid).
curl -s -m 60 -X POST -F "file=@$1" "$2"

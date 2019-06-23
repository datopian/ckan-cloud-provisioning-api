import sys
import json

from ckan_cloud_provisioner.values import convert_body


if __name__=='__main__':
  body = json.load(sys.stdin)
  print(json.dumps(convert_body(body)))

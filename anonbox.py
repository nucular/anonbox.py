import os.path
import urllib.request
import re

ssl = None
try: import ssl
except ImportError: pass

__dir__ = os.path.dirname(__file__)


class EMail(object):
  """Parses and encapsulates a received email."""
  def __init__(self):
    """Initializes the email instance"""
    raise NotImplementedError()

class AnonBox(object):
  """Provides an interface for accessing the anonbox one-time email service."""

  def __init__(self, server="anonbox.net", https=True):
    """Creates a new inbox on the passed anonbox server."""
    self.server = server
    if https:
      if not ssl: raise ImportError("SSL not supported")
      context = ssl.create_default_context()
      context.load_verify_locations(cafile=os.path.join(__dir__, "certs.pem"))
      httpshandler = urllib.request.HTTPSHandler(context=context)
      self.opener = urllib.request.build_opener(httpshandler)
    else:
      self.opener = urllib.request.build_opener()

    with self.opener.open("https://" + self.server + "/en") as res:
      content = res.read().decode(res.info().get_content_charset() or "utf-8")

    m = re.search(
      r"<dd><p>([0-9a-z]{10})@([0-9a-z]{5})\."
      + re.escape(server), content
    )
    if not m: raise IOError("Could not match email address in reponse")
    self.publickey = m.groups()[0]
    self.datehash = m.groups()[1]
    self.address = "{}@{}.{}".format(self.publickey, self.datehash, server)

    m = re.search(
      r"<dd><p><a href=\"" + re.escape(
        ("https://" if https else "http://") + server
      ) + r"/([0-9a-z]{5})/([0-9a-z]{10})\">", content
    )
    if not m: raise IOError("Could not match access URL in reponse")
    if m.groups()[0] != self.datehash:
      raise IOError("Date hash of the access URL does not match the email address")
    self.privatekey = m.groups()[1]

  def check(self):
    """Checks for new emails in the box. Returns a list of the new emails."""
    raise NotImplementedError()

if __name__ == "__main__":
  AnonBox()

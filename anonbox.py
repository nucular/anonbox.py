import os.path
import urllib.request, urllib.error
import re
import email

ssl = None
try: import ssl
except ImportError: pass

__dir__ = os.path.dirname(__file__)


class AnonBox(object):
  """Provides an interface for accessing the anonbox one-time E-mail service."""

  def __init__(self, server="anonbox.net", https=True):
    """Creates a new inbox on the passed anonbox server."""
    self.mails = []
    self.valid = True
    self.protocol = "https" if https else "http"
    self.server = server

    if https:
      if not ssl: raise ImportError("SSL not supported")
      context = ssl.create_default_context()
      context.load_verify_locations(cafile=os.path.join(__dir__, "certs.pem"))
      httpshandler = urllib.request.HTTPSHandler(context=context)
      self.opener = urllib.request.build_opener(httpshandler)
    else:
      self.opener = urllib.request.build_opener()

    with self.opener.open("{}://{}/en".format(self.protocol, self.server)) as res:
      content = res.read().decode(res.info().get_content_charset() or "utf-8")

    m = re.search(
      r"<dd><p>([0-9a-z]{10})@([0-9a-z]{5})\."
      + re.escape(self.server), content
    )
    if not m: raise IOError("Could not match mail address in reponse")
    self.publickey = m.groups()[0]
    self.datehash = m.groups()[1]
    self.address = "{}@{}.{}".format(self.publickey, self.datehash, self.server)

    m = re.search(
      r"<dd><p><a href=\"" + re.escape(
        self.protocol + "://" + self.server
      ) + r"/([0-9a-z]{5})/([0-9a-z]{10})\">", content
    )
    if not m: raise IOError("Could not match access URL in reponse")
    if m.groups()[0] != self.datehash:
      raise IOError("Date hash of the access URL does not match the mail address")
    self.privatekey = m.groups()[1]

  def check(self):
    """Checks for new mails in the box. Returns a list of all new mails."""
    if not self.valid:
      return []

    try:
      with self.opener.open("{}://{}/{}/{}/".format(self.protocol, self.server, self.datehash, self.publickey)) as res:
        if res.getcode() == 404:
          self.valid = False
          return []
        content = res.read().decode(res.info().get_content_charset() or "utf-8")
    except urllib.error.HTTPError as e:
      self.valid = False
      return []

    if not "From " in content:
      return []
    mails = content.split("\nFrom ")
    newmails = [
      email.message_from_string(data.split("\n", 1))
      for data in mails[len(self.mails):]
    ]
    self.mails += newmails
    return newmails

if __name__ == "__main__":
  AnonBox()

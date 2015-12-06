import os.path
import urllib.request, urllib.error
import re
import email

ssl = None
try: import ssl
except ImportError: pass

__dir__ = os.path.dirname(__file__)


class Mailbox(object):
  """
  Provides an interface for accessing the anonbox one-time email service.

  Attributes
  ----------
  datehash : str
    A 5-character hash of the current date.
  privatekey : str
    A 10-character random key that is needed to access received messages.
  publickey : str
    A 10-character random key that is the local part of the address.
  host : str
    The host name of the anonbox service used.
  messages : list of email.message.Message
    Messages received since the creation of the mailbox.
  valid : bool
    Whether the mailbox is still available on the service and can receive
    messages.
  """

  def __init__(self, datehash, privatekey, publickey, host="anonbox.net",
    usessl=True, opener=None):
    """
    Initializes the instance from the keys of an existing mailbox on the anonbox
    server.

    If you want to create a new mailbox, use
    :Mailbox.create:`~anonbox.Mailbox.create` instead.

    Parameters
    ----------
    datehash : str
      A 5-character hash of the current date.
    privatekey : str
      A 10-character random key that is needed to access received messages.
    publickey : str
      A 10-character random key that is the local part of the address.
    host : str
      The host name of the anonbox service used.
    usessl : bool
      Use SSL to connect to the service, don't change this unless it doesn't
      support HTTPS.
    opener : urllib.request.OpenerDirector
      A custom opener that will be used to do all requests. Allows you to
      configure a proxy, for example. Overrides the `usessl` parameter.
    """
    self.datehash = datehash
    self.privatekey = privatekey
    self.publickey = publickey
    self.host = host

    self.messages = []
    self.valid = True
    self.protocol = "https" if usessl else "http"

    if opener:
      self.opener = opener
    else:
      if usessl:
        if not ssl: raise ImportError("SSL not supported")
        context = ssl.create_default_context()
        context.load_verify_locations(cafile=os.path.join(__dir__, "certs.pem"))
        httpshandler = urllib.request.HTTPSHandler(context=context)
        self.opener = urllib.request.build_opener(httpshandler)
      else:
        self.opener = urllib.request.build_opener()

  @classmethod
  def create(cls, host="anonbox.net", usessl=True, opener=None):
    """
    Creates a new mailbox on the anonbox server.

    Parameters
    ----------
    host : str
      The host name of the anonbox service used.
    usessl : bool
      Use SSL to connect to the service, don't change this unless it doesn't
      support HTTPS.
    opener : urllib.request.OpenerDirector
      A custom opener that will be used to do all requests. Allows you to
      configure a proxy, for example. Overrides the `usessl` parameter.

    Returns
    -------
    anonbox.Mailbox
      An instance that can access the new mailbox.
    """
    # Create the instance first so we have the right opener
    self = cls("", "", "", host=host, usessl=usessl, opener=None)
    with self.opener.open("{}://{}/en".format(self.protocol, self.host)) as res:
      content = res.read().decode(res.info().get_content_charset() or "utf-8")

    m = re.search(
      r"<dd><p>([0-9a-z]{10})@([0-9a-z]{5})\."
      + re.escape(self.host), content
    )
    if not m: raise IOError("Could not match mail address in response")
    # Now set the keys
    self.publickey = m.groups()[0]
    self.datehash = m.groups()[1]

    m = re.search(
      r"<dd><p><a href=\"" + re.escape(
        self.protocol + "://" + self.host
      ) + r"/([0-9a-z]{5})/([0-9a-z]{10})\">", content
    )
    if not m: raise IOError("Could not match access URL in reponse")
    if m.groups()[0] != self.datehash:
      raise IOError("Date hash of the access URL does not match the mail address")
    # Set more keys
    self.privatekey = m.groups()[1]

    self.valid = True
    return self

  def check(self):
    """
    Checks for new messages in the box. Returns a list of all new messages.

    In case the service returns a 404, the Mailbox instance is set as invalid.
    If the instance isn't `valid` anymore, calling this method will do nothing
    besides returning an empty `list`.

    Returns
    -------
    list of email.message.Message
      Mails received since the last successful check.
    """
    if not self.valid:
      return []

    try:
      with self.opener.open("{}://{}/{}/{}".format(
        self.protocol, self.host, self.datehash, self.publickey)) as res:
        if res.getcode() == 404:
          self.valid = False
          return []
        content = res.read().decode(res.info().get_content_charset() or "utf-8")
    except urllib.error.HTTPError as e:
      self.valid = False
      return []
    self.valid = True

    if not "From " in content:
      return []
    messages = content.split("\nFrom ")
    newmessages = [
      email.message_from_string(data.split("\n", 1)[1])
      for data in messages[len(self.messages):]
    ]
    self.messages += newmessages
    return newmessages

  @property
  def address(self):
    """
    The address of the mailbox.
    Formatted like `publickey@datehash.host`.

    Returns
    -------
    str
      The address of the mailbox.
    """
    return "{}@{}.{}".format(self.publickey, self.datehash, self.host)

  @property
  def accessurl(self):
    """
    The plain-text access URL of the mailbox.
    Formatted like `protocol://host/datehash/privatekey`.

    Returns
    -------
    str
      The plain-text access URL of the mailbox.
    """
    return "{}://{}/{}/{}".format(self.protocol, self.host, self.datehash, self.privatekey)

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
  Provides an interface for accessing the anonbox one-time E-mail service.

  Attributes
  ----------
  datehash : str
    A 5-character hash of the current date.
  privatekey : str
    A 10-character random key that is needed to read received mails.
  publickey : str
    A 10-character random key that is the local part of the address.
  host : str
    The host name of the anonbox service used.

  mails : list of email.message.Message
    Mails received since the creation of the mailbox.
  valid : bool
    Whether the mailbox is still available on the service and can receive mails.
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
      A 10-character random key that is needed to read received mails.
    publickey : str
      A 10-character random key that is the local part of the address.
    host : str
      The host name of the anonbox service used.
    usessl : bool
      Use SSL to connect to the service, don't change this unless it doesn't
      support HTTPS.
    opener : urllib.request.OpenerDirector
      A custom opener that will be used to do all requests. Allows you to
      configure a proxy, for example. Overrides the usessl parameter.
    """
    self.datehash = datehash
    self.privatekey = privatekey
    self.publickey = publickey
    self.host = host

    self.mails = []
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
    Checks for new mails in the box. Returns a list of all new mails.

    In case the service returns a 404, the :Mailbox:`anonbox.Mailbox` instance is
    set to be invalid.
    If the instance isn't :valid:`anonbox.Mailbox.valid` anymore, calling this
    method will do nothing besides returning an empty list.

    Returns
    -------
    list of email.message.Message
      Mails received since the last successful call to
      :check:`anonbox.Mailbox.check`.
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
    mails = content.split("\nFrom ")
    newmails = [
      email.message_from_string(data.split("\n", 1)[1])
      for data in mails[len(self.mails):]
    ]
    self.mails += newmails
    return newmails

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


if __name__ == "__main__":
  import argparse
  import time
  import webbrowser
  import base64

  parser = argparse.ArgumentParser(
    description="A tiny Python utility and module to access the anonbox.net one-time email service.",
    epilog="<https://github.com/nucular/anonboxpy>"
  )
  subparsers = parser.add_subparsers(help="The action to perform")
  # Shown headers
  headers = ["From", "To", "Date", "Subject"]

  def findPayload(mail, type):
    if mail.is_multipart():
      for k in mail.walk():
        contenttype = k.get_content_type()
        if contenttype == type:
          return k.get_payload(decode=True).decode(mail.get_charset() or "utf-8"), contenttype
      for k in mail.walk():
        contenttype = k.get_content_type()
        if k.get_content_type() == mail.get_default_type():
          return k.get_payload(decode=True).decode(mail.get_charset() or "utf-8"), contenttype
    return mail.get_payload(decode=True).decode(mail.get_charset() or "utf-8"), mail.get_content_type()

  # anonbox create

  def create(args):
    print("Creating new mailbox...")
    mailbox = Mailbox.create(host=args.host, usessl=not args.nossl)
    print("Address", mailbox.address)
    print("Access URL", mailbox.accessurl)
    print("--mailbox {},{},{}\n".format(mailbox.datehash, mailbox.privatekey, mailbox.publickey))
    return mailbox
  parser_create = subparsers.add_parser("create",
    help="create a mailbox and show the access keys"
  )
  parser_create.set_defaults(func=create)

  # anonbox check

  def check(args):
    if not args.mailbox:
      args.mailbox = create(args)
    print("Checking for mails...")
    newmails = args.mailbox.check()
    if not args.mailbox.valid:
      print("Mailbox was deleted")
      return
    print("{} new mails".format(len(newmails)))
    for i, v in enumerate(newmails):
      print("====== {} ======".format(i))
      for h in headers:
        print("{}: {}".format(h, v.get(h)))
      print("---------------")
      payload, contenttype = findPayload(v, "text/plain")
      print(payload)

      if args.browse:
        raise NotImplementedError()
        payload, contenttype = findPayload(v, "text/html")
        if contenttype == "text/html":
          payload = "<p><h1>{}</h1><ul>{}</ul></p>{}".format(
            i,
            "".join(["<li>{}: {}</li>".format(h, v.get(h)) for h in headers]),
            payload
          )
        else:
          payload = "====== {} ======\n{}\n----------------\n".format(
            i,
            ["{}: {}\n".format(h, v.get(h)) for h in headers],
            payload
          )
        datauri = "data:" + contenttype + ";base64," + base64.b64encode(payload.encode("utf-8")).decode("utf-8")
        webbrowser.get().open(datauri, autoraise=True)

  parser_check = subparsers.add_parser("check",
    help="check a mailbox for new mails"
  )
  parser_check.set_defaults(func=check)

  # anonbox watch

  def watch(args):
    if not args.mailbox:
      args.mailbox = create(args)
    try:
      while True:
        time.sleep(args.delay)
        check(args)
        if not args.mailbox.valid:
          break
    except KeyboardInterrupt:
      pass
  parser_watch = subparsers.add_parser("watch")
  parser_watch.set_defaults(func=watch)

  def add_argument(parsers, *args, **kwargs):
    for parser in parsers:
      parser.add_argument(*args, **kwargs)


  add_argument([parser_create, parser_check, parser_watch],
    "--host",
    help="the host name of the anonbox service used, defaults to anonbox.net",
    type=str, action="store", default="anonbox.net"
  )
  add_argument([parser_create, parser_check, parser_watch],
    "--nossl",
    help="don't use SSL when accessing the service",
    action="store_true", default=False
  )
  add_argument([parser_check, parser_watch],
    "--mailbox",
    help="use an existing mailbox instead of creating a new one",
    type=lambda a: Mailbox(*(a.split(","))), action="store", default=None,
    metavar=("DATEHASH,PRIVATE,PUBLIC")
  )
  add_argument([parser_check, parser_watch],
    "--browse", "-b",
    help="open received messages in the browser (HTML emails may compromise your anonymity)",
    action="store_true", default=False
  )
  add_argument([parser_watch],
    "--delay", "-d",
    help="delay between checks in seconds, defaults to 30",
    type=int, action="store", default=30
  )


  args = parser.parse_args()
  if "func" in args:
    args.func(args)
  else:
    parser.error("a subcommand is required")

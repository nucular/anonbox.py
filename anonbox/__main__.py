
import sys, os
import argparse
import time
import webbrowser
import base64

# oh
sys.path.insert(0, os.path.join(os.path.dirname(sys.modules[__name__].__file__), ".."))
import anonbox


SHOWNHEADERS = ["From", "To", "Date", "Subject"]

def findPayload(message, type):
  """
  Find a payload/part that matches a type as closely as possible and decode it
  properly.

  Parameters
  ----------
  message : email.message.Message
    The message to search.
  type : str
    A MIME type.

  Returns
  -------
  str
    The payload as a string.
  """
  charset = message.get_charset() or "utf-8"
  if message.is_multipart():
    for k in message.walk():
      contenttype = k.get_content_type()
      if contenttype == type:
        return k.get_payload(decode=True).decode(charset), contenttype
    for k in message.walk():
      contenttype = k.get_content_type()
      if k.get_content_type() == message.get_default_type():
        return k.get_payload(decode=True).decode(charset), contenttype
  return message.get_payload(decode=True).decode(charset), message.get_content_type()

def create(args):
  """
  The `anonbox create` subcommand.

  Parameters
  ----------
  args : argparse.Namespace
    The program arguments parsed by argparse.

  Returns
  -------
  mailbox : anonbox.Mailbox
    The created Mailbox instance.
  """
  print("Creating new mailbox...")
  mailbox = anonbox.Mailbox.create(host=args.host, usessl=not args.nossl)
  print("Address:", mailbox.address)
  print("Access URL:", mailbox.accessurl)
  print("--mailbox {},{},{}\n".format(mailbox.datehash, mailbox.privatekey, mailbox.publickey))
  return mailbox

def check(args):
  """
  The `anonbox check` subcommand.

  Parameters
  ----------
  args : argparse.Namespace
    The program arguments parsed by argparse.
  """
  if not args.mailbox:
    args.mailbox = create(args)
  print("Checking for messages...")
  newmessages = args.mailbox.check()
  if not args.mailbox.valid:
    print("Mailbox was deleted")
    return
  print("{} new messages".format(len(newmessages)))
  for i, v in enumerate(newmessages):
    print("====== {} ======".format(i))
    for h in SHOWNHEADERS:
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
          "".join(["<li>{}: {}</li>".format(h, v.get(h)) for h in SHOWNHEADERS]),
          payload
        )
      else:
        payload = "====== {} ======\n{}\n----------------\n".format(
          i,
          ["{}: {}\n".format(h, v.get(h)) for h in SHOWNHEADERS],
          payload
        )
      datauri = "data:" + contenttype + ";base64," + base64.b64encode(payload.encode("utf-8")).decode("utf-8")
      webbrowser.get().open(datauri, autoraise=True)

def watch(args):
  """
  The `anonbox watch` subcommand.

  Parameters
  ----------
  args : argparse.Namespace
    The program arguments parsed by argparse.
  """
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

def main(args=None):
  """The main routine."""
  if args is None:
      args = sys.argv[1:]

  parser = argparse.ArgumentParser(
    description="A tiny Python utility and module to access the anonbox.net one-time email service.",
    epilog="<https://github.com/nucular/anonboxpy>"
  )
  subparsers = parser.add_subparsers(help="The action to perform")

  parser_create = subparsers.add_parser("create",
    help="create a mailbox and show the access keys"
  )
  parser_create.set_defaults(func=create)

  parser_check = subparsers.add_parser("check",
    help="check a mailbox for new messages"
  )
  parser_check.set_defaults(func=check)

  parser_watch = subparsers.add_parser("watch",
    help="check a mailbox for new messages periodically"
  )
  parser_watch.set_defaults(func=watch)


  def add_argument(parsers, *args, **kwargs):
    """Call add_argument on multiple :argparse.ArgumentParser: instances."""
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
    help="open received messages in the browser (HTML messages may compromise your anonymity)",
    action="store_true", default=False
  )
  add_argument([parser_watch],
    "--delay", "-d",
    help="delay between checks in seconds, defaults to 30",
    type=int, action="store", default=30
  )

  args = parser.parse_args(args)
  if "func" in args:
    args.func(args)
  else:
    parser.error("a subcommand is required")

if __name__ == "__main__":
  main()

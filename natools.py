#!/usr/bin/env python3

"""
	CopyLeft 2020 Pascal Engélibert <tuxmain@zettascript.org>

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU Affero General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU Affero General Public License for more details.

	You should have received a copy of the GNU Affero General Public License
	along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

__version__ = "1.0"

import os, sys, duniterpy.key, libnacl.sign, base58, base64

def getargv(arg:str, default:str="", n:int=1, args:list=sys.argv) -> str:
	if arg in args and len(args) > args.index(arg)+n:
		return args[args.index(arg)+n]
	else:
		return default

def read_data(data_path, b=True):
	if data_path == "-":
		if b:
			return sys.stdin.read().encode()
		else:
			return sys.stdin.read()
	else:
		return open(os.path.expanduser(data_path), "rb" if b else "r").read()

def write_data(data, result_path):
	if result_path == "-":
		os.fdopen(sys.stdout.fileno(), 'wb').write(data)
	else:
		open(os.path.expanduser(result_path), "wb").write(data)

def encrypt(data, pubkey):
	return duniterpy.key.PublicKey(pubkey).encrypt_seal(data)

def decrypt(data, privkey):
	return privkey.decrypt_seal(data)

def sign(data, privkey):
	return privkey.sign(data)

def verify(data, pubkey):
	try:
		sys.stderr.write("Signature OK!\n")
		return libnacl.sign.Verifier(duniterpy.key.PublicKey(pubkey).hex_pk()).verify(data)
	except ValueError:
		sys.stderr.write("Bad signature!\n")
		exit(1)

def get_privkey(privkey_path, pubsec):
	if pubsec:
		return duniterpy.key.SigningKey.from_pubsec_file(privkey_path)
	else:
		return duniterpy.key.SigningKey.from_seedhex(read_data(privkey_path, False))

fmt = {
	"raw": lambda data: data,
	"16": lambda data: data.hex().encode(),
	"32": lambda data: base64.b32encode(data),
	"58": lambda data: base58.b58encode(data),
	"64": lambda data: base64.b64encode(data),
	"64u": lambda data: base64.urlsafe_b64encode(data),
	"85": lambda data: base64.b85encode(data),
}

def show_help():
	print("""Usage:
python3 natools.py <command> [options]

Commands:
  encrypt  Encrypt data
  decrypt  Decrypt data
  sign     Sign data
  verify   Verify data

Options:
  -i <path>  Input file path (default: -)
  -k <path>  Privkey file path (default: authfile.key)
  --pubsec   Use pub/sec format for -p
  -p <str>   Pubkey (base58)
  -o <path>  Output file path (default: -)
  --noinc    Do not include msg after signature
  -O <fmt>   Output format: raw 16 32 58 64 64u 85 (default: raw)
  
  --help     Show help
  --version  Show version

Note: "-" means stdin or stdout.
""")

if __name__ == "__main__":
	
	if "--help" in sys.argv:
		show_help()
		exit()
	
	if "--version" in sys.argv:
		print(__version__)
		exit()
	
	data_path = getargv("-i", "-")
	privkey_path = getargv("-k", "authfile.key")
	pubsec = "--pubsec" in sys.argv
	pubkey = getargv("-p")
	result_path = getargv("-o", "-")
	output_format = getargv("-O", "raw")
	
	try:
		if sys.argv[1] == "encrypt":
			write_data(fmt[output_format](encrypt(read_data(data_path), pubkey)), result_path)
		
		elif sys.argv[1] == "decrypt":
			write_data(fmt[output_format](decrypt(read_data(data_path), get_privkey(privkey_path, pubsec))), result_path)
		
		elif sys.argv[1] == "sign":
			data = read_data(data_path)
			signed = sign(data, get_privkey(privkey_path, pubsec))
			
			if "--noinc" in sys.argv:
				signed = signed[:len(signed)-len(data)]
			
			write_data(fmt[output_format](signed), result_path)
		
		elif sys.argv[1] == "verify":
			write_data(fmt[output_format](verify(read_data(data_path), pubkey)), result_path)
		
		else:
			show_help()
		
	except Exception as e:
		sys.stderr.write("Error: {}\n".format(e))
		show_help()
		exit(1)


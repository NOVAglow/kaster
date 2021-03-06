"""
vault/vault.py - Password managing subprogram for Kaster

Copyright (C) 2017-2018 Nguyen Hoang Duong <novakglow@gmail.com>
Licensed under MIT License (see LICENSE).
"""

import sys
import os
import traceback
from random import randint
from getpass import getpass
import fnmatch
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from pyperclip import copy as p_copy
sys.path.insert(0, "../system")
import Instructor
import pre_vault
sys.path.insert(0, "../utils")
from global_vars import *
from k_random import random_string


def pre_action():
    """
    An operation which alert the user if there's no Kaster account
    or there's a problem with their account (files missing, invalid files,...).
    Typically put before performing a password manager action (like --new, --get, ...).
    If there's something wrong with the user's account, call sys.exit() and pass 521 to that function
    :return:
    """
    __process__ = "vault.py -> pre_action()"

    check_result = pre_vault.check_user_account()
    try:
        if check_result == 334:
            kaster_logger.warning("%s: No account created. "
                                  "Use './kaster.py --vault --account' to create one."
                                  % __process__)
        if check_result == 331:
            kaster_logger.warning("%s: Found problem(s) with user's account and/or Kaster's files\n"
                                  "  Resolve them and try again. See %s for more details."
                                  % (__process__, log_path))
        if check_result != 330:
            # We don't return but exit so that the
            # vault won't perform any further operation (because we received error, 334 or 331)
            sys.exit(521)
    finally:
        del check_result


def key(inp_pass):
    """
    Create key for password encrypting.
    This is mostly used with the user's master password passed in, to create key
    for a login's password encryption. No need to store key in a file.
    The same password outputs the same key.
    :param inp_pass: Password as input
    :return: Key
    """
    # TODO: Get salt
    f = open(kaster_dir + "/0000.salt", "r")
    salt = f.read()
    f.close()
    del f

    # TODO: Create hash
    f_hash = SHA256.new()
    f_hash.update((inp_pass + salt).encode("utf-8"))
    del salt

    return f_hash.digest()


def new_login(master_password, login_name, login, password, note):
    """
    Interface: Create new login
    :param master_password: Master password as input
    :param login_name: Login's name
    :param login: Login (e-mail address, username, ID, ...)
    :param password: Login's password
    :param note: Login's note/comment
    :return:
    """
    __process__ = "vault.py -> new_login()"

    # TODO: Create a unique ID
    login_id = None
    while True:
        login_id = "%04d" % randint(1, 9999)
        if not os.path.isfile("%s/%s.dat" % (vault_dir, login_id)):
            break

    # TODO: Assign login_name, login and/or password a value if they have a value of "" (empty string)
    if login_name == "":
        kaster_logger.info("%s: Input for login name is empty, "
                           "assigning login name to login's ID: %s"
                           % (__process__, login_id))
        login_name = login_id

    if login == "":
        kaster_logger.info("%s: Input for login is empty, "
                           "assigning login to username: %s"
                           % (__process__, os.environ["SUDO_USER"]))
        login = os.environ["SUDO_USER"]

    if password == "":
        kaster_logger.info("%s: Input for password is empty, a random password is used instead" % __process__)
        password = random_string("ps")

    # TODO: Save login name, login, and comment

    # TODO: Create .DAT file saving the login name, login, and note
    f = open("%s/%s.dat" % (vault_dir, login_id), "w")
    f.write(login_name + "\n")
    f.write(login + "\n")
    f.write(note + "\n")
    f.close()

    # TODO: Create an IV and save it in a .KIV file
    iv = os.urandom(16)
    f = open("%s/%s.kiv" % (vault_dir, login_id), "wb")
    f.write(iv)
    f.close()

    # TODO: Encrypt password using AES with Cipher Feedback mode and the IV created above
    flag = AES.new(key(master_password), AES.MODE_CFB, iv)
    del iv
    f = open("%s/%s.kas" % (vault_dir, login_id), "wb")
    f.write(flag.encrypt(password))
    del flag, password
    f.close()
    del f
    kaster_logger.info("%s: Created a new login with ID %s" % (__process__, login_id))
    del login_id


def get_login(login_id):
    """
    Get login credentials based on login's ID
    :param login_id: Target login's ID
    :return:
    """
    f = open("%s/%s.dat" % (vault_dir, login_id), "r")
    print(f.readline()[:-1])  # Print login name
    print("====================")
    print("Login: %s" % f.readline()[:-1])
    print("ID: %s" % login_id)
    comment = f.readline()[:-1]
    if comment != "":
        print("Comment: %s" % comment)

    f.close()
    del f, comment


def get_id_from_arg(arg, program_terminate=True):
    """
    Turn argument arg to integer if possible, else terminate the program if told to.
    Created to get ID without rewriting a try-catch block over and over.
    If the input ID is invalid, and program_terminate is True, then call sys.exit() and pass 531 to it
    :param arg: ID string (user's input)
    :param program_terminate: Specify whether to terminate the whole program after operation
    :return:
    """
    __process__ = "vault.py -> get_id_from_arg()"

    try:
        return "%04d" % int(arg)
    except ValueError:  # Get this when arg contains non-numerical character(s)
        kaster_logger.warning("%s: Invalid login ID (%s)" % (__process__, arg))

    if program_terminate:
        sys.exit(531)


def vault(com_list):
    """
    Main program for the vault
    :param com_list: Arguments passed to the vault
    :return:
    """
    __process__ = "vault.py -> vault()"

    if len(com_list) == 0:
        Instructor.main("man_vault.txt")
        return 502

    pre_vault.main(False)

    for v_idx, (v_opt, v_arg) in enumerate(com_list):
        if v_opt in ("-h", "--help"):
            Instructor.main("man_vault.txt")

        elif v_opt == "--account":
            if pre_vault.check_user_account(True) == 334:
                if input("No account created, create one now? [Y|N] ").lower() == "y":
                    print()
                    pre_vault.main(True)
                else:
                    return 503

        elif v_opt == "--new":
            pre_action()

            if len(fnmatch.filter(os.listdir(vault_dir), "*.dat")) == 9999:
                kaster_logger.warning("%s: Cannot save a new login: Limit of 9999 logins reached\n"
                                      "  Try deleting an existed login" % __process__)
                return 505

            master = pre_vault.sign_in()
            if master == 321:  # Login failed
                del master
                return 504

            if len(com_list[v_idx + 1:]) == 0:  # User does not specify additional arguments, so prompt
                print("\nNew login\n"
                      "===============")
                login_name = input("Login name: ")
                login = input("Login: ")
                password = getpass("Password (leave blank to generate one): ")
                note = input("Note/Comment (leave blank if there's nothing): ")
            else:  # User specifies additional arguments, so process them
                login_name = ""
                login = ""
                password = ""
                note = ""
                for login_opt, login_arg in com_list[v_idx + 1:]:
                    if login_opt == "--name":
                        login_name = login_arg
                    elif login_opt == "--login":
                        login = login_arg
                    elif login_opt == "--password":
                        password = login_arg
                    elif login_opt == "--comment":
                        note = login_arg
                    else:
                        kaster_logger.error("%s: Invalid option: %s" % (__process__, login_opt))
                        del master
                        del login_name, login, password, note
                        return 506

            new_login(master, login_name, login, password, note)
            return 500

        elif v_opt == "--list":
            pre_action()

            # Check if there is any .dat file (file containing login credentials except password)
            if len(fnmatch.filter(os.listdir(vault_dir), "*.dat")) == 0:
                kaster_logger.info("%s: No login to list" % __process__)
                continue

            login_name = None
            login_id = None
            print("ID   | Login name")
            print("==== | ==========")

            # Get data
            for k_login_f in fnmatch.filter(os.listdir(vault_dir), "*.dat"):
                f = open("%s/%s" % (vault_dir, k_login_f), "rb")
                login_name = f.readline()[:-1].decode("utf-8")
                f.close()
                login_id = k_login_f[:-4]
                print("%s | %s" % (login_id, login_name))

            del login_name, login_id

        elif v_opt == "--get":
            pre_action()

            get_id = get_id_from_arg(v_arg)
            if not os.path.isfile("%s/%s.dat" % (vault_dir, get_id)):
                kaster_logger.error("%s: Login %s does not exist" % (__process__, get_id))
                del get_id
                return 507

            get_login(get_id)
            del get_id

        elif v_opt == "--getpass":
            pre_action()
            master = pre_vault.sign_in()

            if master == 321:  # Login failed
                del master
                return 504

            get_id = get_id_from_arg(v_arg)
            if not os.path.isfile("%s/%s.dat" % (vault_dir, get_id)):
                kaster_logger.error("%s: Login %s does not exist" % (__process__, get_id))
                del get_id
                return 507

            # Get IV
            f = open("%s/%s.kiv" % (vault_dir, get_id), "rb")
            iv = f.read()
            f.close()

            # Get encrypted password
            f = open("%s/%s.kas" % (vault_dir, get_id), "rb")
            pss = f.read()
            f.close()
            del f

            # Decrypt password
            flag = AES.new(key(master), AES.MODE_CFB, iv)
            del iv, master
            pss = flag.decrypt(pss)
            del flag

            # Copy password to clipboard
            try:
                p_copy(pss.decode("utf-8"))
                kaster_logger.info("%s: Password for login %s copied" % (__process__, get_id))
            except UnicodeDecodeError as e:
                del pss, get_id
                kaster_logger.error("CRITICAL::%s: An error occurred while decoding the password: %s" % (__process__, e))
                return 1
            except Exception as e:
                kaster_logger.error("%s: An error occurred while attempting to copy password to clipboard: %s. "
                                    "Could not copy password to clipboard"
                                    % (__process__, e))
                print("=====Traceback=====")
                traceback.print_exc()
            del pss, get_id

        elif v_opt == "--edit":
            pre_action()
            master = pre_vault.sign_in()

            if master == 321:  # Login failed
                del master
                return 504

            if len(com_list[v_idx + 1:]) == 0:
                kaster_logger.error("%s: Must specify more options" % __process__)
                print("Type './kaster.py --vault --help' for the manual page")
                return 1

            login_id = "%04d" % int(v_arg)
            if not os.path.isfile("%s/%s.dat" % (vault_dir, login_id)):
                kaster_logger.error("%s: Login %s does not exist" % (__process__, login_id))
                del login_id
                return 507

            for edit_opt, new_value in com_list[v_idx + 1:]:
                if edit_opt == "--name":
                    flag = new_value
                    if new_value == "":
                        kaster_logger.info("%s: Empty input for new login name, assigning it to login's ID: %s" % (__process__, login_id))
                        flag = login_id
                    f = open("%s/%s.dat" % (vault_dir, login_id), "rb")
                    f.readline()
                    rest = f.read()
                    f.close()
                    f = open("%s/%s.dat" % (vault_dir, login_id), "wb")
                    f.write(bytes(flag + "\n", "utf-8"))
                    f.write(rest)
                    f.close()
                    del flag, rest, f

                elif edit_opt == "--login":
                    flag = new_value
                    if new_value == "":
                        kaster_logger.info("%s: Empty input for new login, assigning it to username: %s"
                                           % (__process__, os.environ["SUDO_USER"]))
                        flag = os.environ["SUDO_USER"]

                    f = open("%s/%s.dat" % (vault_dir, login_id), "rb")
                    mediate_a = f.readline()
                    f.readline()
                    rest = f.read()
                    f.close()

                    f = open("%s/%s.dat" % (vault_dir, login_id), "wb")
                    f.write(mediate_a)
                    f.write(bytes(flag + "\n", "utf-8"))
                    f.write(rest)
                    f.close()
                    del mediate_a, flag, rest, f

                elif edit_opt == "--password":
                    flag = new_value
                    if new_value == "":
                        kaster_logger.info("%s: Empty input for new password, assigning it to a random password" % __process__)
                        flag = random_string("ps")

                    os.remove("%s/%s.kas" % (vault_dir, login_id))
                    os.remove("%s/%s.kiv" % (vault_dir, login_id))

                    # IV
                    iv = os.urandom(16)
                    f = open("%s/%s.kiv" % (vault_dir, login_id), "wb")
                    f.write(iv)
                    f.close()

                    # Save (encrypted) password
                    enc_object = AES.new(key(master), AES.MODE_CFB, iv)
                    del iv
                    f = open("%s/%s.kas" % (vault_dir, login_id), "wb")
                    f.write(enc_object.encrypt(flag))
                    del enc_object, flag
                    f.close()
                    del f

                elif edit_opt == "--comment":
                    flag = new_value
                    if new_value == "":
                        kaster_logger.info("%s: Empty input for login's comment" % __process__)
                        continue

                    f = open("%s/%s.dat" % (vault_dir, login_id), "rb")
                    flag_a = f.readline()
                    flag_b = f.readline()
                    f.close()

                    f = open("%s/%s.dat" % (vault_dir, login_id), "wb")
                    f.write(flag_a)
                    f.write(flag_b)
                    f.write(bytes(flag + "\n", "utf-8"))
                    f.close()
                    del flag_a, flag_b, flag, f

                else:
                    kaster_logger.error("%s: Invalid option: %s" % (__process__, edit_opt))
                    return 506
            del master

            kaster_logger.info("%s: Edited login %s" % (__process__, login_id))
            del login_id
            return 0

        elif v_opt == "--del":
            get_id = get_id_from_arg(v_arg)
            if not os.path.isfile("%s/%s.dat" % (vault_dir, get_id)):  # If the login does not exist :/
                kaster_logger.error("%s: Login %s does not exist" % (__process__, get_id))
                del get_id
                return 507

            master = pre_vault.sign_in()
            if master == 321:  # Login failed
                del master
                return 504
            del master

            flag_exitcode = 500
            if input("Are you really sure you want to delete login #%s? [Y|N] " % get_id).lower() == "y":
                try:
                    os.remove("%s/%s.dat" % (vault_dir, get_id))
                    os.remove("%s/%s.kas" % (vault_dir, get_id))
                    os.remove("%s/%s.kiv" % (vault_dir, get_id))
                    kaster_logger.info("%s: Login %s removed" % (__process__, get_id))
                except FileNotFoundError:
                    pass
                except OSError as e:
                    kaster_logger.critical("%s: An error occurred while deleting login %s: %s" % (__process__, get_id, e))
                    print("=====Traceback=====")
                    traceback.print_exc()
                    flag_exitcode = 508
                finally:
                    del get_id
                    return flag_exitcode
            else:
                print("Aborting...")

        elif v_opt == "--delall":
            if len(fnmatch.filter(os.listdir(vault_dir), "*.dat")) == 0:
                kaster_logger.info("%s: No saved login" % __process__)
                return 500

            master = pre_vault.sign_in()
            if master == 321:  # Login failed
                del master
                return 504
            del master

            if input("Are you really sure you want to delete all saved logins? [Y|N] ").lower() == "y":
                os.system("rm -rf %s" % vault_dir)
                os.mkdir(vault_dir)
                kaster_logger.info("%s: Removed all saved logins" % __process__)
            else:
                print("Aborting...")
        else:
            kaster_logger.error("%s: Not recognized option: %s" % (__process__, v_opt))
            return 501

import sys
import os
import traceback
from random import randint
import zlib
from getpass import getpass
import fnmatch
from Crypto.Hash import SHA512
from Crypto.Cipher import AES
sys.path.insert(0, "../system")
import global_var
import LogWriter
import pre_vault
import Instructor


def clear_vault_dir():
    """
    Clear vault's folder (/usr/share/kaster/vault).
    :return:
    """
    os.system("rm -rf /usr/share/kaster/vault")
    os.mkdir(global_var.program_file_dir + "/vault")


def mediate_check_account():
    """
    A function to mediate session pre_vault.check_user_account().
    Base on the returned value, the program can make further decisions.
    :return: pre_vault.check_user_account()
    """
    LogWriter.write_to_log("Start session: pre_vault.check_user_account()")
    print("In session: pre_vault.check_user_account()...")
    try:
        result = pre_vault.check_user_account()
    except Exception as e:
        LogWriter.write_to_log("Failed session: pre_vault.check_user_account() with exception: %s" % e)
        print("Session encountered an error: pre_vault.check_user_account()")
        print("Full traceback")
        traceback.print_exc()
        sys.exit(1)
    print("Finish session: pre_vault.check_user_account()...")
    LogWriter.write_to_log("End session: pre_vault.check_user_account()")
    return result


def key(inp_pass):
    """
    Create key for password encrypting.
    This is mostly used with the user's master password passed in, to create key
    for a login's password encryption. No need to store key in a file.
    The same password outputs the same key.
    :param inp_pass: Password as input
    :return: Key
    """
    # Get salt
    f = open(global_var.program_file_dir + "/0000.salt", "r")
    salt = f.read()
    f.close()

    # Create hash
    f_hash = SHA512.new()
    f_hash.update((inp_pass + salt).encode("utf-8"))
    del salt
    flag = f_hash.digest()
    del f_hash

    return zlib.compress(flag)


def new_login_ui(master_password):
    """
    Interface: Create new login
    :param: master_password: Master password as input
    :return:
    """
    # Create ID
    # Make sure the ID login is not a duplicate
    while True:
        login_id = "%04d" % randint(1, 9999)
        if not os.path.isfile("%s/%s.dat" % (global_var.vault_file_dir, login_id)):
            break

    print("New login")

    login_name = input("Login name: ")
    if login_name == "":
        print("Input empty, assigning login name to login's ID: %s" % login_id)
        login_name = login_id

    login = input("Login: ")
    if login == "":
        print("Input empty, assiging login to username: %s" % os.environ["SUDO_USER"])
        login = os.environ["SUDO_USER"]

    password = getpass("Password: ")
    note = input("Note/Comment (you can hit enter if there's nothing): ")

    # Save login name, login, and comment
    f = open("%s/%s.dat" % (global_var.vault_file_dir, login_id), "wb")
    f.write(bytes(login_name, "utf-8") + b"\n")
    f.write(bytes(login, "utf-8") + b"\n")
    f.write(bytes(note, "utf-8") + b"\n")
    f.close()

    # Create IV and save it
    iv = os.urandom(24)
    f = open("%s/%s.kiv" % (global_var.vault_file_dir, login_id), "wb")
    f.write(iv)
    f.close()

    # Save encrypted password
    flag = AES.new(key(master_password), AES.MODE_CBC, iv)
    del iv
    f = open("%s/%s.kas" % (global_var.vault_file_dir, login_id), "wb")
    f.write(flag.encrypt(password))
    del flag
    f.close()
    del f


def vault(com_list):
    """
    Main program for the vault
    :param com_list: Arguments passed to the vault
    :return:
    """
    if len(com_list) == 0:
        Instructor.main("man_vault.txt")
        sys.exit(0)
    pre_vault.main(False)
    for v_idx, (v_opt, v_arg) in enumerate(com_list):
        if v_opt in ("-h", "--help"):
            Instructor.main("man_vault.txt")
        elif v_opt == "--account":
            if mediate_check_account() == -1:
                if input("No account created, create one now? [Y|N] ").lower() == "y":
                    pre_vault.main(True)
                else:
                    sys.exit(0)
        elif v_opt == "--new":
            if mediate_check_account() == -1:
                print("No account created. Use './kaster.py --vault --account' to create one.")
                sys.exit(0)
            if mediate_check_account() == 1:
                print("Warning: Found problem(s) during pre_vault.check_user_account() session, "
                      "resolve them and try again")
                sys.exit(1)
            if len(fnmatch.filter(os.listdir(global_var.vault_file_dir), "*.dat")) == 9999:
                print("Warning: Cannot save a new login, try deleting an existed login")
                sys.exit(1)
            master = pre_vault.sign_in()
            if master == 1:
                del master
                sys.exit(1)  # Login failed
            if com_list[v_idx + 1:] == 0:  # No further argument -> Login UI
                LogWriter.write_to_log("Start session: vault > new_login_ui()")
                print("In session: new_login_ui()")
                try:
                    new_login_ui(master)
                    del master
                except Exception as e:
                    del master
                    LogWriter.write_to_log("Failed session: vault > new_login_ui() with exception: %s" % e)
                    print("Session encountered an error: new_login_ui()")
                    print("Full traceback")
                    traceback.print_exc()
                    sys.exit(1)
                LogWriter.write_to_log("End session: vault > new_login_ui()")
                print("Finish session: new_login_ui()")
        else:
            print("Not recognized option '%s'. Quitting..." % v_opt)
            sys.exit(1)

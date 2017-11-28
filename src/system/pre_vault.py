import sys
import os
from getpass import getpass
import fnmatch
from global_var import *
import LogWriter
import k_random
from k_check_pss import k_check_pss
from Crypto.Hash import SHA512


def check_user_account():
    """
    Check if a Kaster account is created, and if yes, check the state of the account
    Return 0 if everything is okay.
    Return -1 if no account is created.
    Return 1 if something is wrong.
    :return: An integer indicates user's account state
    """
    flag = 0
    # If no account has not yet been created, exit
    # It doesn't matter because when a new account is created,
    # all files containing credentials, key, and IVs will be deleted
    if not os.path.isfile(program_file_dir + "/0000.kas"):
        print("No account created.")
        LogWriter.write_to_log("pre_vault.check_user_account() : "
                               "0000.kas not found -> No account created, session abort")
        return -1

    print("Username: %s" % os.environ["SUDO_USER"])

    f_checker = open(program_file_dir + "/0000.kas", "rb")
    # Check 0000.kas file content
    first_line = f_checker.readline()
    if first_line == b"":
        flag = 1
        print("Warning: 0000.kas is empty")
        LogWriter.write_to_log("pre_vault.check_user_account() : Found file /usr/share/kaster/0000.kas to be empty")
    elif first_line != bytes(os.environ["SUDO_USER"] + "\n", "utf-8"):
        flag = 1
        print("Warning: Got wrong username '%s', expected '%s'." % (os.environ["SUDO_USER"], first_line))
        LogWriter.write_to_log("pre_vault.check_user_account() : Username that is written in "
                               "/usr/share/kaster/0000.kas does not seem to match with current username")
    del first_line
    if f_checker.read() == b"":
        flag = 1
        print("Warning: Couldn't find master password hash.")
        LogWriter.write_to_log("pre_vault.check_user_account() : Found no password hash, this is a danger")
    f_checker.close()

    # Check file containing salt
    if not os.path.isfile(program_file_dir + "/0000.salt"):
        flag = 1
        print("Warning: Couldn't find file containing master password salt.")
        LogWriter.write_to_log("pre_vault.check_user_account() : Found no file containing the salt that is used "
                               "for master password's hashing, this is a danger")
        print("Should clear vault's files after this operation.")
    else:
        f_checker = open(program_file_dir + "/0000.salt")
        if len(f_checker.read()) != 32:
            flag = 1
            print("Warning: Unexpected file length: File containing salt.")
            LogWriter.write_to_log("pre_vault.check_user_account() : Unexpected length: /usr/share/kaster/0000.salt, "
                                   "the file might have been modified")
    del f_checker

    # Check the availability of vault's files
    for file in fnmatch.filter(os.listdir(vault_file_dir), "*.dat"):
        if not os.path.isfile(vault_file_dir + "/" + file[:-4] + ".kas"):
            print("Warning: Couldn't find file containing password for login #%s" % file[:-4])
            LogWriter.write_to_log("pre_vault.check_user_account() : "
                                   "Found no file containing password for login #%s" % file[:-4])
            flag = 1
        if not os.path.isfile(vault_file_dir + "/" + file[:-4] + ".kiv"):
            print("Warning: Couldn't find file containing IV for login #%s" % file[:-4])
            LogWriter.write_to_log("pre_vault.check_user_account() : "
                                   "Found no file containing IV for login #%s" % file[:-4])
            flag = 1

    # Result
    if flag == 0:
        print("Account state: OK")
        LogWriter.write_to_log("pre_vault.check_user_account() : Found no problem, session end")
        del flag
        return 0
    else:
        print("Account state: NOT OK")
        LogWriter.write_to_log("pre_vault.check_user_account() : Found problem(s), session end")
        del flag
        return 1


def create_default_std():
    """
    Create the default file that defines Kaster's password standards
    :return:
    """
    if not os.path.isdir(std_file_dir):
        os.mkdir(std_file_dir)
    f = open(std_file_dir + "/kaster.std", "w")
    f.write("2 / 9 * 100\n")
    f.write("12:30\n")
    f.write("2:4\n")
    f.write("2:4\n")
    f.write("2:4\n")
    f.write("2:4\n")
    f.close()
    del f


def sign_up():
    """
    Sign up session
    :return:
    """
    # Clear vault path
    if os.path.isdir(vault_file_dir):
        os.system("rm -rf %s" % vault_file_dir)
    os.mkdir(vault_file_dir)
    mst_pass = None
    p_hash = SHA512.new()
    try:
        print("Sign Up")
        print("==============================")
        print("Username: %s" % os.environ["SUDO_USER"])
        f = open(program_file_dir + "/0000.kas", "wb")
        f.write(bytes(os.environ["SUDO_USER"] + "\n", "utf-8"))
        mst_pass = getpass("Password: ")
        if len(mst_pass) == 0:
            # If input is nothing then generate a random password as said
            # Usually k_random.random_string("ps") would return a strong-enough password
            # Just having a while loop to make sure it does return a strong password
            while True:
                mst_pass = k_random.random_string("ps")
                if k_check_pss(mst_pass, std_file_dir + "/kaster.std") == 10:
                    print("Your password is: '%s'" % mst_pass)
                    print("(Exclude the single quotes around it)")
                    print("Please REMEMBER this password.")
                    input("Hit Enter to continue")
                    break
        elif getpass("Confirm password: ") == mst_pass:
            pss_score = k_check_pss(mst_pass, std_file_dir + "/kaster.std")
            if pss_score != 10:  # Compare password to Kaster's standard
                os.system("clear")
                print("Warning: Your password is not strong enough based on Kaster Password Standard (%d/10)." % pss_score)
                print("You can enter nothing to get a randomly-generated password")
                del pss_score, mst_pass
                sign_up()
                return
        else:
            print("Warning: Passwords do not match. Aborting...")
            f.close()
            os.remove(program_file_dir + "/0000.kas")
            del f, mst_pass
            sys.exit(12)
        salt = k_random.random_hex(32)  # Create salt
        p_hash.update((mst_pass + salt).encode("utf-8"))  # Create hash
        f.write(p_hash.digest())  # Save hash
        f.close()
        os.system("chmod o-r %s" % (program_file_dir + "/0000.kas"))  # Make file unreadable to non-sudo privilege
        f = open(program_file_dir + "/0000.salt", "w")
        f.write(salt)  # Save salt
        del salt
        f.close()
        os.system("chmod o-r %s" % (program_file_dir + "/0000.salt"))
        del f, mst_pass
        print("New account for user %s created." % os.environ["SUDO_USER"])
        LogWriter.write_to_log("Created an account for %s." % os.environ["SUDO_USER"])
    except (KeyboardInterrupt, Exception):
        # Remove file containing user name and encrypted password (0000.kas) and file containing salt (0000.salt)
        # to avoid problems when user enters --account next.
        os.remove(program_file_dir + "/0000.kas")
        if os.path.isfile(program_file_dir + "/0000.salt"):
            os.remove(program_file_dir + "/0000.salt")
        return


def sign_in():
    """
    Sign in session
    :return:
    """
    print("Sign In")
    print("==============================")
    print("Username: %s" % os.environ["SUDO_USER"])

    # Get password hash right away
    # No get password then get hash 'cuz that's more dangerous, perhaps?
    f = open(program_file_dir + "/0000.kas", "rb")
    f.readline()
    p_hash = f.read()
    f.close()

    # Get salt
    f = open(program_file_dir + "/0000.salt", "r")
    p_salt = f.read()
    f.close()
    del f

    input_mst_pass = getpass("Password: ")
    hash_factor = SHA512.new()
    hash_factor.update((input_mst_pass + p_salt).encode("utf-8"))
    del input_mst_pass, p_salt
    # Check if the input password hash is the same as the saved hash
    if hash_factor.digest() != p_hash:
        print("Authentication failed: Wrong password.")
        del p_hash, hash_factor
        return 1

    del p_hash, hash_factor
    return 0


def main(create_acc):
    """
    All processes to be ran if pre_vault is called.
    :param create_acc: Boolean to tell if creating an account is required
    :return:
    """
    create_default_std()

    if not create_acc:
        return
    sign_up()

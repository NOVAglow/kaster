# Shell script to create Kaster's program files directory
# Invoked by install.sh. DO NOT EXECUTE THIS SCRIPT MANUALLY.

# Make sure this script isn't being executed manually.

if [[ $fcheck != "0" ]]
then
    >&2 echo -e "\033[0;31mERROR\033[0m: Do not execute this script manually."
    exit 1
fi

# Create Kaster's directory to store program files
# Program files are the ones in the source code,
# not the ones generated by Kaster.

mkdir -p $kaster_home
mv $src_path/* $kaster_home

# Create default .kasterrc

drcp="$kaster_home/kasterrc"
touch $drcp
echo -e "# Default Kaster configuration\n# DO NOT EDIT." > $drcp
echo "program_file_dir = \"$def_kaster_home\"" >> $drcp
echo "user_file_dir = \"$def_user_home\""      >> $drcp
echo "date_format = \"$def_df\""               >> $drcp
echo "time_format = \"$def_tf\""               >> $drcp

exit 0

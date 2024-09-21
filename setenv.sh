# setenv.sh is a script to set sensitive environment variables in your shell.
# You should almost always run it as `. ./setenv.sh` so that the variables
# are actually set in your shell post execution.

# Funtion to sign the current shell into 1password
function op_signin () {
	op list items --account account 1> /dev/null 2>&1
	return_code=$?
	if [ $return_code -eq "1" ]; then
			echo "you are not signed in -- signing in ..."
			raw=$(op signin account --raw)
			export OP_SESSION_account="$raw"
	else
			echo "You are already signed in"
	fi
}

# Function to export an environment variable with a name and set
# the value based on a secret in 1password.
# first arg: 1password api credential name
# second arg: the name of the environment variable.
function load_key () {
	export $2="$(op get item $1 --fields credential)"
	echo "Loaded $2 ..."
}

op_signin

if [ -z "$OP_SESSION_account" ]; then
	echo "Could not sign into 1password. Exiting"
	return 127
fi

echo "Loading secrets from 1password ...\n"

# These keys should go into your "Personal" vault in account's 1password account.
load_key 'my_aws_access_key_id' 'AWS_ACCESS_KEY_ID'
load_key 'my_aws_secret_access_key' 'AWS_SECRET_ACCESS_KEY'

export AWS_DEFAULT_REGION="us-east-1"

echo "\nFinished loading secrets from 1password!"

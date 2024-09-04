import os
import argparse
import configparser
import sys

yabs_version = "0.1.0"


def get_default_config_path():
    xdg_config_home = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(xdg_config_home, "yabs", "config.ini")


def load_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def validate_directory(directory, should_exist=True):
    if should_exist:
        if not os.path.isdir(directory):
            print(f"Error: Directory '{directory}' does not exist.")
            return False
    else:
        try:
            os.makedirs(directory, exist_ok=True)
        except PermissionError:
            print(f"Error: No permission to create directory '{directory}'.")
            return False
    return True


def validate_read_access(directory):
    try:
        # Attempt to list contents to check read access
        if os.listdir(directory) is None:
            raise PermissionError
    except (PermissionError, FileNotFoundError):
        print(f"Error: No read access to directory '{directory}'.")
        return False
    return True


def get_input(prompt, default_value=None):
    response = input(prompt + f" [{default_value}] ").strip()
    return response if response else default_value


def init():
    print("Configuration File Generator")

    # Determine the default save location
    default_save_location = get_default_config_path()
    save_path = get_input(
        "Enter the path to save the configuration file", default_save_location
    )

    # Validate and create the parent directory if needed
    save_dir = os.path.dirname(save_path)
    if not validate_directory(save_dir, should_exist=False):
        sys.exit(1)

    # Collect backup destination
    backup_destination = get_input("Enter the backup destination directory")
    if not validate_directory(backup_destination, should_exist=False):
        sys.exit(1)

    # Collect list of directories to back up
    directories = []
    print("Enter the directories to back up (leave blank to finish):")
    while True:
        directory = input("Directory: ").strip()
        if not directory:
            break
        if not validate_directory(directory):
            sys.exit(1)
        directories.append(directory)

    # Collect retention policies with defaults
    days = int(get_input("Enter the number of daily backups to keep", "7"))
    weeks = int(get_input("Enter the number of weekly backups to keep", "4"))
    months = int(get_input("Enter the number of monthly backups to keep", "12"))
    years = int(get_input("Enter the number of yearly backups to keep", "2"))

    # Write the configuration file
    config = configparser.ConfigParser()
    config["backup"] = {
        "directories": ",".join(directories),
        "destination": backup_destination,
        "days": days,
        "weeks": weeks,
        "months": months,
        "years": years,
    }

    # Display configuration for user approval
    print("\nConfiguration Summary:")
    for key, value in config["backup"].items():
        print(f"{key.capitalize()}: {value}")

    approval = input("\nIs this configuration correct? (yes/no): ").strip().lower()
    if approval.lower() not in ["yes", "y"]:
        print("Configuration not saved.")
        sys.exit(1)

    with open(save_path, "w") as config_file:
        config.write(config_file)

    print(f"Configuration saved to '{save_path}'")


def backup(args):
    print("Backup command not yet implemented.")
    # Backup logic would go here
    pass


def restore(args):
    print("Restore command not yet implemented.")
    # Restore logic would go here
    pass


def list_backups(args):
    print("List Backups command not yet implemented.")
    # List backups logic would go here
    pass


def prune(args):
    print("Prune command not yet implemented.")
    # Prune backups logic would go here
    pass


def validate(args):
    print("Validate command not yet implemented.")
    # Validate backups logic would go here
    pass


def status(args):
    print("Status command not yet implemented.")
    # Status logic would go here
    pass


def version():
    print(f"YABS version {yabs_version}")
    exit()


def help(parser):
    print_usage(parser)
    exit()


def parse_arguments():
    parser = argparse.ArgumentParser(description="Yet Another Backup Script")
    subparsers = parser.add_subparsers(dest="command")

    # Subcommand for initializing configuration
    init_parser = subparsers.add_parser(
        "init", help="Initialize and save a new configuration file"
    )

    # Subcommand for backup script execution
    backup_parser = subparsers.add_parser(
        "backup", help="Run the backup with the given configuration"
    )
    backup_parser.add_argument("-c", "--config", help="Path to the configuration file")
    backup_parser.add_argument(
        "-d", "--directories", nargs="+", help="List of directories to back up"
    )
    backup_parser.add_argument(
        "-t", "--destination", help="Destination directory where backups will be stored"
    )
    backup_parser.add_argument(
        "--days", type=int, help="Number of days of backups to keep"
    )
    backup_parser.add_argument(
        "--weeks", type=int, help="Number of weeks of backups to keep"
    )
    backup_parser.add_argument(
        "--months", type=int, help="Number of months of backups to keep"
    )
    backup_parser.add_argument(
        "--years", type=int, help="Number of years of backups to keep"
    )

    # Subcommand for restore
    restore_parser = subparsers.add_parser(
        "restore", help="Restore files from a backup"
    )

    # Subcommand for listing backups
    ls_parser = subparsers.add_parser("ls", help="List all available backups")

    # Subcommand for pruning old backups
    prune_parser = subparsers.add_parser(
        "prune", help="Prune old backups according to retention policies"
    )

    # Subcommand for validating backups
    validate_parser = subparsers.add_parser(
        "validate", help="Validate the integrity of backups"
    )

    # Subcommand for showing status
    status_parser = subparsers.add_parser(
        "status", help="Show the current status of the backup system"
    )

    # Subcommand for showing version
    version_parser = subparsers.add_parser(
        "version", help="Show the version of the tool"
    )

    # Subcommand for showing help
    help_parser = subparsers.add_parser(
        "help", help="Show the arguments and usage info for the yabs command"
    )

    return parser.parse_args(), parser


def print_usage(parser):
    parser.print_help()
    print("\nUsage scenarios:")
    print("1. Initialize a new configuration file:")
    print("   yabs.py init")
    print("\n2. Run the backup with a configuration file:")
    print("   yabs.py backup --config /path/to/config.ini")
    print("\n3. Run the backup with command line arguments:")
    print(
        "   yabs.py backup -d /dir1 /dir2 -t /backup/destination --days 7 --weeks 4 --months 12 --years 2"
    )
    print("\n4. Run the backup using the default config location:")
    print("   yabs.py backup")
    print("\n5. Restore from a backup:")
    print("   yabs.py restore")
    print("\n6. List available backups:")
    print("   yabs.py ls")
    print("\n7. Prune old backups:")
    print("   yabs.py prune")
    print("\n8. Validate the integrity of backups:")
    print("   yabs.py validate")
    print("\n9. Show the current backup status:")
    print("   yabs.py status")
    print("\n10. Show the version of the tool:")
    print("   yabs.py version")
    print(
        "\nNote: If no config file is provided and not all CLI arguments are specified, the script will look for a config file at the default location (~/.config/yabs/config.ini)."
    )


def main():
    args, parser = parse_arguments()

    if args.command == "init":
        init()
    elif args.command == "backup":
        backup(args)
    elif args.command == "restore":
        restore(args)
    elif args.command == "ls":
        list_backups(args)
    elif args.command == "prune":
        prune(args)
    elif args.command == "validate":
        validate(args)
    elif args.command == "status":
        status(args)
    elif args.command == "version":
        version()
    elif args.command == "help":
        help(parser)
    else:
        print("Error: No command provided.")
        print_usage(parser)
        sys.exit(1)


if __name__ == "__main__":
    main()

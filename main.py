import os
import argparse
import configparser
import sys
import hashlib
import tarfile
import zstandard as zstd
import time
from datetime import datetime
from pathlib import Path

yabs_version = "0.1.0"


def get_default_config_path():
    xdg_config_home = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(xdg_config_home, "yabs", "config.ini")


def load_config(config_path=None):
    if config_path:
        config_path = Path(config_path).expanduser()
    else:
        config_path = Path(
            os.getenv("YABS_CONFIG", get_default_config_path())
        ).expanduser()

    if not config_path.is_file():
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)

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
    # Load configuration
    config = load_config(args.config)
    directories = config.get("backup", "directories").split(",")
    destination = config.get("backup", "destination")
    retention_policy = {
        "days": int(config.get("backup", "days")),
        "weeks": int(config.get("backup", "weeks")),
        "months": int(config.get("backup", "months")),
        "years": int(config.get("backup", "years")),
    }

    # Determine backup category
    backup_category = determine_backup_category(retention_policy)

    # Create a compressed archive
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    archive_name = f"backup-{timestamp}.tar.zst"  # Example using zstandard
    archive_path = os.path.join(destination, backup_category, archive_name)

    # Ensure the destination directory exists
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)

    # Use zstandard compression for the archive
    cctx = zstd.ZstdCompressor()
    with open(archive_path, "wb") as f:
        with cctx.stream_writer(f) as compressed_file:
            with tarfile.open(fileobj=compressed_file, mode="w") as tar:
                for directory in directories:
                    tar.add(directory, arcname=os.path.basename(directory))

    # Generate SHA-256 hashes and update metadata
    sha256_hash = generate_sha256(archive_path)
    update_metadata(destination, backup_category, archive_name, sha256_hash)

    print(f"Backup created and stored in {archive_path}")


def determine_backup_category(retention_policy):
    # Determine which backup category to use based on retention policy
    if retention_policy["days"] > 0:
        return "daily"
    elif retention_policy["weeks"] > 0:
        return "weekly"
    elif retention_policy["months"] > 0:
        return "monthly"
    elif retention_policy["years"] > 0:
        return "yearly"
    else:
        raise ValueError("Invalid retention policy. All categories set to 0.")


def generate_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256.update(byte_block)
    return sha256.hexdigest()


def update_metadata(destination, category, archive_name, sha256_hash):
    metadata_file = os.path.join(destination, category, "metadata.txt")
    with open(metadata_file, "a") as f:
        f.write(f"{archive_name} {sha256_hash}\n")


# priority 3
def restore(args):
    config = load_config(args.config)
    print("Restore command not yet implemented.")
    # Restore logic would go here
    pass


def list_backups(args):
    # Load configuration
    config = load_config(args.config)
    backup_categories = ["daily", "weekly", "monthly", "yearly"]
    base_path = config.get("backup", "destination")

    # Function to read the metadata file and return a set of valid backup filenames
    def load_metadata(category_path):
        metadata_file = os.path.join(category_path, "metadata.txt")
        valid_files = set()
        if os.path.isfile(metadata_file):
            with open(metadata_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split()
                        if parts:
                            valid_files.add(parts[0])  # Only add the filename
        return valid_files

    for category in backup_categories:
        category_path = os.path.join(base_path, category)
        if os.path.isdir(category_path):
            # Load valid backup filenames from metadata
            valid_files = load_metadata(category_path)

            print(f"\n{category.capitalize()} Backups:")
            for filename in sorted(os.listdir(category_path), reverse=True):
                file_path = os.path.join(category_path, filename)
                if (
                    os.path.isfile(file_path)
                    and filename in valid_files
                    and filename != "metadata.txt"
                ):
                    file_size = os.path.getsize(file_path)
                    human_size = human_readable_size(file_size)
                    timestamp = datetime.fromtimestamp(os.path.getmtime(file_path))
                    formatted_date = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{filename} - Size: {human_size} - Date: {formatted_date}")


def human_readable_size(size):
    """Convert a file size to a human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


# priority 4
def prune(args):
    config = load_config(args.config)
    print("Prune command not yet implemented.")
    # Prune backups logic would go here
    pass


# priority 6
def validate(args):
    config = load_config(args.config)
    print("Validate command not yet implemented.")
    # Validate backups logic would go here
    pass


# priority 5
def status(args):
    config = load_config(args.config)
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
    parser.add_argument("--config", help="Path to the configuration file", default=None)
    subparsers = parser.add_subparsers(dest="command")

    # Subcommand for initializing configuration
    subparsers.add_parser("init", help="Initialize and save a new configuration file")

    # Subcommand for backup script execution
    backup_parser = subparsers.add_parser(
        "backup", help="Run the backup with the given configuration"
    )
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

    # Add --config to the subcommands that need it
    for command in ["restore", "ls", "prune", "validate", "status"]:
        subparser = subparsers.add_parser(
            command,
            help=(
                f"{command.capitalize()} files from a backup"
                if command == "restore"
                else (
                    f"{command.capitalize()} old backups"
                    if command == "prune"
                    else (
                        f"Validate the integrity of backups"
                        if command == "validate"
                        else (
                            f"Show the current status of the backup system"
                            if command == "status"
                            else f"List all available backups"
                        )
                    )
                )
            ),
        )
        subparser.add_argument(
            "--config", help="Path to the configuration file", default=None
        )

    # Subcommand for showing version
    subparsers.add_parser("version", help="Show the version of the tool")

    # Subcommand for showing help
    subparsers.add_parser(
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

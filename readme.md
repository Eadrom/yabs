# Yet Another Backup Script

YABS is a simple python backup management script. It takes a target list of directories, a destination directory to store the backups, and runs periodic backups of the files. After creating a backup, it then prunes old backups. The default behavior is to keep the last 7 days, the last 4 weeks, the last 4 months, and the last 4 years. The last backup of a period is what is pushed to the longer term retention. 

What this means is if your daily period is friday to thursday, then after the first 7 days, on the second friday, it will take a new backup, and then the old friday's backup becomes the next weekly backup. This process rolls forward for all long term periods past the base backup period. In this way, backups don't overlap when they are effective for. 

The number of backups and in which periods are configurable, so if you want to retain two weeks or a month of daily backups before dropping to weekly backups, that's possible. 


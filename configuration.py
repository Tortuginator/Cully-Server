#DEF Variables
global Config_Mysql_host
global Config_Mysql_password
global Config_Mysql_username
global Config_Mysql_database

global Config_Server_port
global Config_Server_address
global Config_Server_buffer

global Config_Server_Storage
global Config_Server_TimeFormat
global Config_Server_DebugOverlay
#INIT CONFIG

Config_Mysql_host ="localhost"
Config_Mysql_password = "test123"
Config_Mysql_username = "root"
Config_Mysql_database = "sys"

Config_Server_port = int(5541)
Config_Server_port_public = int(5541)
Config_Server_address = "192.168.0.100"
Config_Server_address_public = "192.168.0.100"
Config_Server_buffer = 1024*3

Config_Server_Storage = "C:\\xampp\\htdocs\\php\\storage\\"
Config_Server_TimeFormat = "%Y-%m-%d %H:%M:%S"
Config_Server_DebugOverlay = True
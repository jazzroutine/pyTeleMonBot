import os
import json
import psutil
import subprocess
import requests
import asyncio
import aioschedule
import datetime
import tabulate
import psycopg2
import datetime
from functools import wraps
from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv
from tabulate import tabulate
from hurry.filesize import size


"""
========================================================================
Import vars from .env
========================================================================
"""

load_dotenv() # Python-dotenv reads key-value pairs from a .env

# get API_KEY
API_KEY = os.getenv('API_KEY')

# get users for bot securing
list_of_users = json.loads(os.environ['LIST_OF_USERS'])
list_of_users_chats = json.loads(os.environ['LIST_OF_USERS_CHATS'])

# services info
service_1_url=os.getenv('SERVICE_1_URL')
service_1_name=os.getenv('SERVICE_1_NAME')
service_2_name=os.getenv('SERVICE_2_NAME')
service_2_user=os.getenv('SERVICE_2_USER')
service_2_process=os.getenv('SERVICE_2_PROCESS')
service_3_name=os.getenv('SERVICE_3_NAME')
service_4_usage_path=os.getenv('SERVICE_4_USAGE_PATH')
service_5_url=os.getenv('SERVICE_5_URL')
service_5_name=os.getenv('SERVICE_5_NAME')
m_service_4_export_path=os.getenv('M_SERVICE_4_EXPORT_PATH')


"""
========================================================================
var initializations
========================================================================
"""

# temp var for cicle stamp in monitor_service4
m_users_tmp_len = 0


"""
========================================================================
Bot's service block.
Bot connection and private functions.
========================================================================
"""

bot = AsyncTeleBot(API_KEY)  # main bot connection

def is_known_username(username):
    """Returns a boolean if the username is present in 
    the LIST_OF_USERS from .env
    """
    return username in list_of_users

def private_access():
    """Wrapper to restrict access to the command to users 
    allowed by the is_known_username function
    """
    def deco_restrict(f):
        @wraps(f)
        async def f_restrict(message, *args, **kwargs):
            username = message.from_user.username

            if is_known_username(username):
                return await f(message, *args, **kwargs)
            else:
                text = 'Who are you?!'
                await bot.reply_to(message, text)
        return f_restrict  # true decorator
    return deco_restrict


"""
========================================================================
Bot's main interactive functions to use
inside Telegram bot's chat or group.
========================================================================
"""

@bot.message_handler(commands=['help', 'start'])
@private_access()
async def send_welcome(message):
    """Returns initial message and help (/start, /help)"""

    msg = '''
Server Monitoring Bot
---------
Services Status → /status
Server info → /server
---------
Matrix users → /matrix
Nextcloud users → /nextcloud
---------
Chat ID → /id
Users → /bot_users
Help → /help
---------
    '''
    await bot.send_message(message.chat.id, msg)

@bot.message_handler(commands=['server'])
@private_access()
async def server(message):
    """Returns basic server info (/server)"""

    uname = subprocess.check_output(['uname','-rsoi']).decode('UTF-8')
    host = subprocess.check_output(['hostname']).decode('UTF-8')
    ipAddr = subprocess.check_output(['hostname','-I']).decode('UTF-8')
    upTime = subprocess.check_output(['uptime','-p']).decode('UTF-8')
    distr = subprocess.check_output(['lsb_release','-ds']).decode('UTF-8')
    cpuUsage = psutil.cpu_percent(interval=1)
    ramTotal = int(psutil.virtual_memory().total/(1024*1024)) #in GB
    ramUsage = int(psutil.virtual_memory().used/(1024*1024)) #in GB
    ramUsagePercent = psutil.virtual_memory().percent
    diskTotal = int(psutil.disk_usage('/').total/(1024*1024*1024)) #in GB
    diskUsed = int(psutil.disk_usage('/').used/(1024*1024*1024)) #in GB
    diskPercent = psutil.disk_usage('/').percent

    msg = '''
Server Info
---------
Distr: {}OS: {}Hostname: {}IP Addr: {}---------
Uptime: {}---------
CPU Usage: {} %
RAM Used: {} %
RAM Total: {} MB
RAM Usage: {} MB
---------
HDD Used: {} %
HDD Total: {} GB
HDD Usage: {} GB
---------
\n'''.format(distr,uname,host,ipAddr,
             upTime,cpuUsage,ramUsagePercent,
             ramTotal,ramUsage,diskPercent,
             diskTotal,diskUsed)
    await bot.send_message(message.chat.id,msg)

@bot.message_handler(commands=['status'])
@private_access()
async def status(message):
    """Returns services status (/status)"""

# service 1 - Matrix web page status code
    service_1_status_raw = (requests.get(service_1_url)).status_code
    
    if service_1_status_raw == 200:
        service_1_status = 'Ok'
    else:
        service_1_status = 'Not ok!'

# service 2 - Matrix main process status
    service_2_procs = {proc.pid: proc.name() for proc 
                       in psutil.process_iter() 
                       if proc.username() == service_2_user and 
                       proc.name() == service_2_process}

    if len(service_2_procs) == 1:
        service_2_status = 'Ok'
    elif len(service_2_procs) == 0:
        service_2_status = 'Not ok!'
    else:
        service_2_status = 'Strange?'

# service 3 - Matrix DB status
    conn = None

    try:
        # connect to the local PostgreSQL Matrix DB
        conn = psycopg2.connect(
            host='localhost',
            database=os.getenv('DB_1_NAME'),
            user=os.getenv('DB_1_USER'),
            password=os.getenv('DB_1_PASS'))
        # if OK
        service_3_status = 'Ok'
        conn.close()

    except (Exception, psycopg2.DatabaseError) as error:
        # if error
        service_3_status = 'Not ok!'

    finally:
        if conn is not None:
            conn.close()

# service 5 - web page status code
    service_5_status_raw = (requests.get(service_1_url)).status_code
    
    if service_5_status_raw == 200:
        service_5_status = 'Ok'
    else:
        service_5_status = 'Not ok!'

# compose answer message
    smsg = '''
Services Status
---------
{} - {}
{} - {}
{} - {}
{} - {}
---------
    '''.format(service_1_name,service_1_status,
               service_2_name,service_2_status,
               service_3_name,service_3_status,
               service_5_name,service_5_status)
        
    await bot.send_message(message.chat.id,smsg)

@bot.message_handler(commands=['matrix'])
@private_access()
async def m_users(message):
    """Returns matrix users list (/matrix)"""
    conn = None
    try:
        # connect to the local PostgreSQL Matrix DB
        conn = psycopg2.connect(
            host='localhost',
            database=os.getenv('DB_1_NAME'),
            user=os.getenv('DB_1_USER'),
            password=os.getenv('DB_1_PASS'))
        cur = conn.cursor()
	    # get data from table
        cur.execute('''SELECT name,creation_ts 
                    FROM "users" ORDER BY creation_ts DESC;
                    ''')
        # write cursor data to var
        users_raw = cur.fetchall()
        cur.close()

        # make m_users_raw readable + 3 hours
        users_list = [(e[0], 
                      datetime.datetime.utcfromtimestamp(e[1] 
                      + 10800).strftime('%Y-%m-%d %H:%M')) 
                      for e in users_raw]

        # filter user list to remote test accounts
        users_real = []
        for user in users_list:
            if (user[0] in ('test' in user[0])):
                continue
            users_real.append(user)

        # get total real user count
        users_count = len(users_real)
        # formating user list
        users_table = tabulate(users_real,
                               headers=[
                                   'Username', 
                                   'Registered (MSK)'
                                   ])

        await bot.send_message(message.chat.id, '```\n' 
                               + users_table 
                               + '\n\nTotal: ' 
                               + str(users_count) 
                               + '\n```', 
                               parse_mode='MarkdownV2')

    except (Exception, psycopg2.DatabaseError) as error:
        # send meassage if error
        await bot.send_message(message.chat.id, 
                               'DB connection error: ' 
                               + str(error))

    finally:
        if conn is not None:
            conn.close()

@bot.message_handler(commands=['nextcloud'])
@private_access()
async def n_users(message):
    """Returns NextCloud users, data usage and 
    last timestamp list (/nextcloud)
    Based on data created via cron script!
    """
    file = None
    try:
        # try to read file
        file = open(service_4_usage_path, 'r')
        # writing all data to var
        file_data = file.readlines()
        # closing file connection
        file.close()

        # empty list creation
        file_data_list = []

        # file data parsing and formating
        for line in file_data:
            f_size, f_date, f_user = line.split("\t")

            # username formating
            user_formated = f_user.split("/")[-1].strip()
            if (user_formated in 
                ('lost+found','data') or 
                'appdata_' in user_formated):
                continue

            # folder size formating and demo files size subtracting
            size_int = int(f_size.strip()) - 23456

            #if folder size less then 100KB it's empty
            if int(size_int) <= 100:
                size_int = 0

            #folder size formating to pretty representation
            size_formated = size(size_int*1024)

            #append line to main list
            file_data_list.append((user_formated,size_formated,f_date))

        #get datafile update time + 3 hours
        file_update_raw = (os.path.getmtime(
                           '/opt/pyTeleMonBot/.data/usage.txt') 
                           + 10800)
        #datafile update time formating
        file_update_time = (datetime.datetime
                            .fromtimestamp(file_update_raw)
                            .strftime("%Y-%m-%d %H:%M"))
        
        file_data_list_count = len(file_data_list)
        # formating user list
        file_data_table = tabulate(file_data_list, 
                                   headers=[
                                       'Username', 
                                        'Usage', 
                                        'Last Change (MSK)'
                                        ])

        await bot.send_message(message.chat.id, 
                               '```\n' + file_data_table 
                               + '\n' + '\nTotal: ' 
                               + str(file_data_list_count) 
                               + '\n' + 'Last update: ' 
                               + str(file_update_time) 
                               + '\n```',
                               parse_mode='MarkdownV2')

    except Exception as error:
        # send meassage if something wrong
        await bot.send_message(message.chat.id,
                               'File read error: ' 
                               + str(error))
    
    finally:
        if file is not None:
            file.close()

@bot.message_handler(commands=['id'])
async def id(message):
    """Returns current chat ID (/id)"""

    await bot.send_message(message.chat.id,
                           'This chat ID: ' 
                           + str(message.chat.id))

@bot.message_handler(commands=['bot_users'])
@private_access()
async def b_users(message):
    """Returns bot users list (/bot_users)"""
    users = '\n'.join([f'@{e}' for e in list_of_users])

    await bot.send_message(message.chat.id, 'Bot Users: \n' + users)

@bot.message_handler(func=lambda message: True, content_types=['text'])
@private_access()
async def command_default(message):
    """Default handler for every other text.
    Should be the last bot message handler!
    """

    await bot.send_message(message.chat.id, 
                           "I don't understand \'" 
                           + message.text 
                           + "\'\nMaybe try the help page at /help")


"""
========================================================================
aioschedule monitor logic
========================================================================
"""

async def monitor_service1():
    """Monitor job 1 - Matrix main web page check"""
    
    # try to get webpage response status code
    service_1_status_raw = (requests.get(service_1_url)).status_code

    # send alarm if code not 200
    if service_1_status_raw != 200:
        service_1_status = service_1_name + ' is not ok!'
        for id in list_of_users_chats:
            await bot.send_message(id, service_1_status)

async def monitor_service2():
    """Monitor job 2 - Matrix main python service check"""

    # try to find matrix process
    service_2_procs = {proc.pid: proc.name() for 
                       proc in psutil.process_iter() if 
                       proc.username() == service_2_user and 
                       proc.name() == service_2_process}
    
    # send alarm if service was not found
    if len(service_2_procs) == 0:
        service_2_status = service_2_name + ' is not ok!'
        for id in list_of_users_chats:
            await bot.send_message(id, service_2_status)

async def monitor_service3():
    """Monitor job 3 - Matrix postgres DB connection check"""
    conn = None
    try:
        # connect to the PostgreSQL server
        conn = psycopg2.connect(
            host='localhost',
            database=os.getenv('DB_1_NAME'),
            user=os.getenv('DB_1_USER'),
            password=os.getenv('DB_1_PASS'))
        conn.close()

    except (Exception, psycopg2.DatabaseError) as error:
        # send alarm id DB connection was unsuccessful
        for id in list_of_users_chats:
            await bot.send_message(id, service_3_name 
                                   + ' is not ok! '
                                   + 'DB connection error: ' 
                                   + error)

    finally:
        if conn is not None:
            conn.close()

async def monitor_service4():
    """Monitor job 4 - Matrix postgres DB new user alert.
    Additionally this job is exporting Matrix users list to local file.
    """
    global m_users_tmp_len

    try:
        # connect to the PostgreSQL server
        conn = psycopg2.connect(
            host='localhost',
            database=os.getenv('DB_1_NAME'),
            user=os.getenv('DB_1_USER'),
            password=os.getenv('DB_1_PASS'))
        
        # create a cursor
        cur = conn.cursor()

	    # get data from table
        cur.execute('''SELECT name,creation_ts 
                    FROM "users" ORDER BY creation_ts DESC;
                    ''')

        # write cursor data to var
        m_users_raw = cur.fetchall()
        cur.close()

        # user count
        m_users_raw_len = len(m_users_raw)

        # make m_users_raw readable
        m_users_list = [(e[0], 
                        datetime.datetime.utcfromtimestamp(e[1] 
                        + 10800).strftime('%Y-%m-%d %H:%M')) for 
                        e in m_users_raw]

        # !optional part start 
        # exporting real Matrix user to local file

        # prepare list of real users for export
        m_users_export = []
        for user in m_users_list:
            if user[0] in ('test' in user[0]):
                continue
            m_users_export.append(user)

        #export real user list to file 
        file = None
        try:
            #try write to file
            file = open(m_service_4_export_path, 'w')
            #writing data per line
            for line in m_users_export:
                file.write(line[0])
                file.write('\n')
            file.close()

        except Exception as error:
            # send meassage if something wrong
            for id in list_of_users_chats:
                await bot.send_message(id, 
                                       'File write error: ' 
                                       + str(error))
    
        finally:
            if file is not None:
                file.close()
        # !optional part end 

        if m_users_tmp_len == 0:
            # initial cicle stamp 
            m_users_tmp_len = m_users_raw_len

        elif m_users_tmp_len < m_users_raw_len:
            # new user count
            new_m_users_len = m_users_raw_len - m_users_tmp_len
            # take new users in to dedicated var
            new_m_users_list = m_users_list[:new_m_users_len]
            # formating new user list
            new_m_users_table = tabulate(new_m_users_list, 
                                         headers=[
                                             'Username', 
                                             'Registered (MSK)'
                                             ])

            # message constructing
            msg = ''
            if new_m_users_len == 1:
                msg = '1 new user registered!'
            else: 
                msg = str(new_m_users_len) + ' new users registered!'

            # send messages to users
            for id in list_of_users_chats:
                await bot.send_message(id, msg)
                await bot.send_message(id, 
                                       '```\n' 
                                       + new_m_users_table 
                                       + '\n```', 
                                       parse_mode='MarkdownV2')
            
            # set new cicle stamp
            m_users_tmp_len = m_users_raw_len        

    except (Exception, psycopg2.DatabaseError) as error:
        for id in list_of_users_chats:
                await bot.send_message(id, 
                                       'DB connection error: ' 
                                       + error)

    finally:
        if conn is not None:
            conn.close()

async def monitor_service5():
    """Monitor job 5 - NextCloud main web page check"""
    
    # try to get webpage response status code
    service_5_status_raw = (requests.get(service_5_url)).status_code

    # send alarm if code not 200
    if service_5_status_raw != 200:
        service_5_status = service_5_name + ' is not ok!'
        for id in list_of_users_chats:
            await bot.send_message(id, service_5_status)

async def monitor_service10():
    """Monitor job 10 - Recent server reboot check"""
    
    # reading uptime raw data
    try:
        f = open( '/proc/uptime' )
        contents = f.read().split()
        f.close()
    except:
        return 'Cannot open uptime file: /proc/uptime'
    
    # convert to seconds
    total_seconds = float(contents[0])

    # if uptime less then 10 minutes send alert
    if total_seconds < 600:
        upTime = subprocess.check_output(['uptime','-p']).decode('UTF-8')
        for id in list_of_users_chats:
            await bot.send_message(id, "Attention! Server rebooted recently!" + '\nUptime: ' + upTime)


"""
========================================================================
aioschedule monitor job schedules
========================================================================
"""

aioschedule.every(300).seconds.do(monitor_service1)
aioschedule.every(300).seconds.do(monitor_service2)
aioschedule.every(300).seconds.do(monitor_service3)
aioschedule.every(120).seconds.do(monitor_service4)
aioschedule.every(300).seconds.do(monitor_service5)
aioschedule.every(300).seconds.do(monitor_service10)


"""
========================================================================
asyncio service loops
========================================================================
"""

async def scheduler():
    """Sheduler loop"""
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def main():
    """Gatherer loop"""
    await asyncio.gather(bot.infinity_polling(), scheduler())

if __name__ == '__main__':
    asyncio.run(main())
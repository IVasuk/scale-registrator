#!/usr/bin/env python3
import threading
import argparse
import sc_dbms
import src.sc_scales as sc_scales

from datetime import datetime
from time import sleep

LOCK = threading.Lock()

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--host', required=False, type=str, default='localhost')
    parser.add_argument('-p', '--port', required=False, type=str, default='5432')
    parser.add_argument('-d', '--dbname', required=False, type=str, default='scaledb')
    parser.add_argument('-u', '--user', required=False, type=str, default='scale')
    parser.add_argument('-pas', '--password', required=False, type=str, default='scale')
    parser.add_argument('-ct', '--create_tables', action='store_true')
    parser.add_argument('-srv', '--server', action='store_true')
    parser.add_argument('-pub', '--create_publication', choices=['all', 'status', 'calculations', 'photos'], required=False, type=str, default=None)
    parser.add_argument('-sub', '--create_subscriptions', choices=['all', 'status', 'calculations', 'photos'], required=False, type=str, default=None)
    parser.add_argument('-sa', '--server_host', required=False, type=str)

    return parser

def registering(id, port, baudrate, sleep_timeout, command_timeout, commands):
    scale = sc_scales.XK3118T1(id, port, baudrate, sleep_timeout, command_timeout, commands)

    cl = len(commands)

    while True:
        try:
            sc_dbms.sc_connect()

            sc_scale = sc_dbms.ScScales.get_by_id(id)
            sc_indications = sc_dbms.ScScaleIndications
            sc_calculations = sc_dbms.ScCalculations

#            print(f'{id}: connecting to port ...')
#            scale.connect()
#            print(f'{id}: connecting to port OK')

            while True:
                scale.connect()

#                print(f'{id}: getting data ...')
                res = scale.get()
#                print(f'{id}: getting data OK {res}')

                scale.close()

                if len(res) == cl:
                    now_str = datetime.now().astimezone()#.strftime('%Y-%m-%d %H:%M:%S %z')

                    sc_scale.last_seen = now_str

                    for indicator, value in res.items():
                        sc_indicator = sc_indications.get_by_id((id,indicator))

                        if sc_scale.basic_indication == indicator:
                            sc_scale.basic_value = value

                        if value == sc_indicator.value:
                            delta = value - sc_indicator.stab_value

                            if delta != 0:
                                sc_calculations.create(scale=sc_scale,begin_timestamp=sc_indicator.stab_timestamp,end_timestamp=now_str,
                                                       indication=indicator,delta=delta,rest=value,operation=sc_scale.operation)

                                sc_indicator.stab_value = value

                            sc_indicator.stab_timestamp = now_str
                        else:
                            sc_indicator.value = value

                        sc_indicator.value_timestamp = now_str

                        sc_indicator.save()

                    sc_scale.save()

#                    with LOCK:
#                        print(f'{now_str} {id}: {res}')
                else:
                    with LOCK:
                        print(f'{id}: break {res}')

                    break
        except BaseException as ex:
            with LOCK:
                print(ex)
        finally:
            if not sc_dbms.sc_is_closed():
#                print(f'{id}: closing dbms ...')
                sc_dbms.sc_close()
#                print(f'{id}: closing dbms OK')

            if scale.is_open():
#                print(f'{id}: closing port ...')
                scale.close()
#                print(f'{id}: closing port OK')

        sleep(command_timeout)

        break


def main():
    parser = create_parser()
    namespace = parser.parse_args()

    sc_dbms.sc_init_database(namespace.dbname,namespace.user,namespace.password,namespace.host,namespace.port)

    try:
        sc_dbms.sc_connect()

        if namespace.create_tables:
            if namespace.server:
                sc_dbms.sc_create_tables('server')
            else:
                sc_dbms.sc_create_tables('registrator')
        elif namespace.create_publication is not None:
            sc_dbms.sc_create_publications(namespace.create_publication)
        elif namespace.create_subscriptions is not None:
            sc_dbms.sc_create_subscriptions('all',namespace.server_host,namespace.port,namespace.dbname,namespace.user,namespace.password)
        else:
            sc_dbms.sc_init_tables()

            threads = []

            for connection in sc_dbms.ScConnections.select():
                commands = []

                for indication in connection.scale.indications:
                    commands.append(indication.indication)

                thr = threading.Thread(target=registering, args=(connection.scale.id, connection.port, connection.baudrate, connection.sleep_timeout, connection.command_timeout, commands), daemon=True)
                thr.start()

                threads.append(thr)

            for thr in threads:
                thr.join()
    except BaseException as ex:
        print(f'service stopped: {ex}')
    finally:
        sc_dbms.sc_close()

if __name__ == '__main__':
    main()

import argparse, sys

from squaredeal import SquareDeal


argparser = argparse.ArgumentParser(prog='pysquaredeal.py')

argparser.add_argument('sqd_file', metavar='SQD_FILE', help='path to SQD file')
argparser.add_argument('--sqk-file', metavar='SQK_FILE', help='path to SQK file, if not provided, deduced from SQD file', required=False)

subparsers = argparser.add_subparsers(title='command-specific arguments', metavar='COMMAND', dest='command')

argparser_create = subparsers.add_parser('create', help='create new SQD/SQK pair')
argparser_create.add_argument('--event-name', required=False, metavar='EVENT_NAME', help='event name (description)')
argparser_create.add_argument('--delayed-information', required=False, metavar='DELAYED_INFO', help='(description of) delayed information')

argparser_name = subparsers.add_parser('set_name', help='edit event name')
argparser_name.add_argument('event_name', metavar='EVENT_NAME', help='event name (description)')

argparser_di = subparsers.add_parser('set_di', help='edit event delayed information (or its value)')
argparser_di.add_argument('delayed_information', metavar='DELAYED_INFO', help='(description of) delayed information')

arguments = argparser.parse_args()

if arguments.command == 'create':
    sd = SquareDeal()
    sd.name = arguments.event_name
    sd.delayed_info = arguments.delayed_information
    sd.tofile(arguments.sqd_file, sqkpath=arguments.sqk_file)
elif arguments.command == 'set_name':
    sd = SquareDeal()
    sd.fromfile(arguments.sqd_file, sqkpath=arguments.sqk_file)
    sd.name = arguments.event_name
    sd.tofile(arguments.sqd_file, sqkpath=arguments.sqk_file)
elif arguments.command == 'set_di':
    sd = SquareDeal()
    sd.fromfile(arguments.sqd_file, sqkpath=arguments.sqk_file)
    sd.delayed_info = arguments.delayed_information
    sd.tofile(arguments.sqd_file, sqkpath=arguments.sqk_file)

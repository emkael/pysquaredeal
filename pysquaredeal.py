import argparse, os, re, sys

from squaredeal import SquareDeal, squaredeal_board_range


argparser = argparse.ArgumentParser(prog='pysquaredeal.py')

argparser.add_argument('sqd_file', metavar='SQD_FILE', help='path to SQD file')
argparser.add_argument('--sqk-file', metavar='SQK_FILE', help='path to SQK file, if not provided, deduced from SQD file', required=False)
argparser.add_argument('--encoding', required=False, default='utf-8', metavar='ENCODING', help='SQD/SQK input file encoding, defaults to UTF-8, output is always UTF-8')
argparser.add_argument('--bigdealx-path', required=False, default=os.environ.get('BIGDEALX_PATH'), metavar='BIGDEALX_PATH', help='path to bigdealx executable, defaults to BIGDEALX_PATH environment variable')

subparsers = argparser.add_subparsers(title='command-specific arguments', metavar='COMMAND', dest='command')

argparser_create = subparsers.add_parser('create', help='create new SQD/SQK pair')
argparser_create.add_argument('--event-name', required=False, metavar='EVENT_NAME', help='event name (description)')
argparser_create.add_argument('--delayed-information', required=False, metavar='DELAYED_INFO', help='(description of) delayed information')
argparser_create.add_argument('--overwrite', action='store_true', help='overwrite output file if exists, otherwise error is raised')

argparser_name = subparsers.add_parser('set_name', help='edit event name')
argparser_name.add_argument('event_name', metavar='EVENT_NAME', help='event name (description)')

argparser_di = subparsers.add_parser('set_di', help='edit event delayed information (its description ahead of time)')
argparser_di.add_argument('delayed_information', metavar='DELAYED_INFO', help='description of delayed information')

argparser_phase = subparsers.add_parser('add_phase', help='add event phase')
argparser_phase.add_argument('sessions', metavar='NO_SESSIONS', help='number of sessions in phase', type=int)
argparser_phase.add_argument('boards', metavar='NO_BOARDS', help='number of boards in each session, also accepts syntax like "1-10,11-20,21-30", "3x7" is expanded to "1-7,8-14,15-21"', type=squaredeal_board_range)
argparser_phase.add_argument('prefix', metavar='PREFIX', help='ouput file prefix ("#" will be replaced by session number)')
argparser_phase.add_argument('description', nargs='?', metavar='DESCRIPTION', help='phase description')

argparser_publish = subparsers.add_parser('publish', help='mark SQD as published')

argparser_di = subparsers.add_parser('set_dv', help='edit event delayed information (its value)')
argparser_di.add_argument('delayed_information', metavar='DELAYED_INFO', help='value of delayed information')

argparser_generate = subparsers.add_parser('generate', help='generate PBN')
argparser_generate.add_argument('phase', nargs='?', metavar='PHASE', help='phase number or range, if empty, all phases will be generated')
argparser_generate.add_argument('session', nargs='?', metavar='SESSION', help='session number or range, if empty, all sessions will be generated')
argparser_generate.add_argument('--reserve', action='store_true', help='generate reserve board set')

arguments = argparser.parse_args()


SquareDeal.BIGDEALX_PATH = arguments.bigdealx_path

sq = SquareDeal(arguments.sqd_file, sqk_file=arguments.sqk_file, encoding=arguments.encoding)
getattr(sq, arguments.command)(**vars(arguments))

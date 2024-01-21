import argparse, os, re, sys

from squaredeal import SquareDeal, SquareDealError, SquareDealPhase, generate_session_key, validate_board_range_str


def board_range(arg_str):
    ranges = []
    for range_str in arg_str.split(','):
        range_match = re.match(r'^([0-9]+)x([0-9]+)$', range_str)
        if range_match:
            subrange_count = int(range_match.group(2))
            ranges += ['%d-%d' % (i*subrange_count+1, (i+1)*subrange_count) for i in range(0, int(range_match.group(1)))]
            continue
        ranges += [validate_board_range_str(range_str)]
    return ','.join(ranges)


argparser = argparse.ArgumentParser(prog='pysquaredeal.py')

argparser.add_argument('sqd_file', metavar='SQD_FILE', help='path to SQD file')
argparser.add_argument('--sqk-file', metavar='SQK_FILE', help='path to SQK file, if not provided, deduced from SQD file', required=False)
argparser.add_argument('--encoding', required=False, default='utf-8', metavar='ENCODING', help='SQD/SQK input file encoding, defaults to UTF-8, output is always UTF-8')
argparser.add_argument('--bigdealx-path', required=False, metavar='BIGDEALX_PATH', help='path to bigdealx executable, defaults to BIGDEALX_PATH environment variable')

subparsers = argparser.add_subparsers(title='command-specific arguments', metavar='COMMAND', dest='command')

argparser_create = subparsers.add_parser('create', help='create new SQD/SQK pair')
argparser_create.add_argument('--event-name', required=False, metavar='EVENT_NAME', help='event name (description)')
argparser_create.add_argument('--delayed-information', required=False, metavar='DELAYED_INFO', help='(description of) delayed information')

argparser_name = subparsers.add_parser('set_name', help='edit event name')
argparser_name.add_argument('event_name', metavar='EVENT_NAME', help='event name (description)')

argparser_di = subparsers.add_parser('set_di', help='edit event delayed information (its description ahead of time)')
argparser_di.add_argument('delayed_information', metavar='DELAYED_INFO', help='description of delayed information')

argparser_phase = subparsers.add_parser('add_phase', help='add event phase')
argparser_phase.add_argument('sessions', metavar='NO_SESSIONS', help='number of sessions in phase', type=int)
argparser_phase.add_argument('boards', metavar='NO_BOARDS', help='number of boards in each session, also accepts syntax like "1-10,11-20,21-30", "3x7" is expanded to "1-7,8-14,15-21"', type=board_range)
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


# TODO: this should be an interface class, also rename SquareDeal to SQD or sth and this to SquareDeal
if arguments.command == 'create':
    sd = SquareDeal()
    sd.name = arguments.event_name
    sd.delayed_info = arguments.delayed_information
    sd.tofile(arguments.sqd_file)
elif arguments.command == 'set_name':
    sd = SquareDeal()
    sd.fromfile(arguments.sqd_file, sqkpath=arguments.sqk_file)
    if sd.published:
        raise SquareDealError('Cannot change name: event already published')
    sd.name = arguments.event_name
    sd.tofile(arguments.sqd_file)
elif arguments.command == 'set_di':
    sd = SquareDeal()
    sd.fromfile(arguments.sqd_file, sqkpath=arguments.sqk_file)
    if sd.published:
        raise SquareDealError('Cannot change delayed information description: event already published')
    sd.delayed_info = arguments.delayed_information
    sd.tofile(arguments.sqd_file)
elif arguments.command == 'add_phase':
    sd = SquareDeal()
    sd.fromfile(arguments.sqd_file, sqkpath=arguments.sqk_file)
    if sd.published:
        raise SquareDealError('Cannot add phase: event already published')
    sdphase = SquareDealPhase()
    sdphase.sessions = arguments.sessions
    sdphase.boards = arguments.boards
    sdphase.prefix = arguments.prefix
    sdphase.info = arguments.description
    sd.phases.append(sdphase)
    sd.tofile(arguments.sqd_file)
elif arguments.command == 'publish':
    sd = SquareDeal()
    sd.fromfile(arguments.sqd_file, sqkpath=arguments.sqk_file)
    if sd.published:
        raise SquareDealError('Cannot mark as published: event already published')
    if not sd.name:
        raise SquareDealError('Cannot mark as published: event name is not set')
    if not sd.delayed_info:
        raise SquareDealError('Cannot mark as published: delayed information is not set')
    if not sd.phases:
        raise SquareDealError('Cannot mark as published: no phases are defined')
    for sdphase in sd.phases:
        sdphase.s_keys = [generate_session_key() for s in range(0, sdphase.sessions)]
    sd.published = True
    sd.tofile(arguments.sqd_file, sqkpath=arguments.sqk_file)
elif arguments.command == 'set_dv':
    sd = SquareDeal()
    sd.fromfile(arguments.sqd_file, sqkpath=arguments.sqk_file)
    if not sd.published:
        raise SquareDealError('Cannot set delayed information value: event not published')
    sd.delayed_value = arguments.delayed_information
    sd.tofile(arguments.sqd_file, sqkpath=arguments.sqk_file)
elif arguments.command == 'generate':
    if arguments.bigdealx_path is None:
        arguments.bigdealx_path = os.environ.get('BIGDEALX_PATH', None)
    SquareDeal.BIGDEALX_PATH = arguments.bigdealx_path
    sd = SquareDeal()
    sd.fromfile(arguments.sqd_file, sqkpath=arguments.sqk_file)
    if not sd.published:
        raise SquareDealError('Cannot generate PBN files: event info is not marked as published')
    if not sd.delayed_value:
        raise SquareDealError('Cannot generate PBN files: delayed information value not set')
    sd.generate(arguments.phase, arguments.session, reserve=arguments.reserve)

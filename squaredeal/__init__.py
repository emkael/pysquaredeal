import os

from squaredeal.sqd import SQD, SQDPhase, generate_session_key, validate_board_range_str


class SquareDealError(Exception):
    pass


def squaredeal_board_range(arg_str):
    ranges = []
    for range_str in arg_str.split(','):
        range_match = re.match(r'^([0-9]+)x([0-9]+)$', range_str)
        if range_match:
            subrange_count = int(range_match.group(2))
            ranges += ['%d-%d' % (i*subrange_count+1, (i+1)*subrange_count) for i in range(0, int(range_match.group(1)))]
            continue
        ranges += [validate_board_range_str(range_str)]
    return ','.join(ranges)


class SquareDeal(object):

    def __init__(self):
        self.sqd = SQD()

    def create(self, **arguments):
        self.sqd.name = arguments.get('event_name')
        self.sqd.delayed_info = arguments.get('delayed_information')
        self.sqd.tofile(arguments.get('sqd_file'))

    def set_name(self, **arguments):
        self.sqd.fromfile(arguments.get('sqd_file'), sqkpath=arguments.get('sqk_file'))
        if self.sqd.published:
            raise SquareDealError('Cannot change name: event already published')
        self.sqd.name = arguments.get('event_name')
        self.sqd.tofile(arguments.get('sqd_file'))

    def set_di(self, **arguments):
        self.sqd.fromfile(arguments.get('sqd_file'), sqkpath=arguments.get('sqk_file'))
        if self.sqd.published:
            raise SquareDealError('Cannot change delayed information description: event already published')
        self.sqd.delayed_info = arguments.get('delayed_information')
        self.sqd.tofile(arguments.get('sqd_file'))

    def add_phase(self, **arguments):
        self.sqd.fromfile(arguments.get('sqd_file'), sqkpath=arguments.get('sqk_file'))
        if self.sqd.published:
            raise SquareDealError('Cannot add phase: event already published')
        sdphase = SQDPhase()
        sdphase.sessions = arguments.get('sessions')
        sdphase.boards = arguments.get('boards')
        sdphase.prefix = arguments.get('prefix')
        sdphase.info = arguments.get('description')
        self.sqd.phases.append(sdphase)
        self.sqd.tofile(arguments.get('sqd_file'))

    def publish(self, **arguments):
        self.sqd.fromfile(arguments.get('sqd_file'), sqkpath=arguments.get('sqk_file'))
        if self.sqd.published:
            raise SquareDealError('Cannot mark as published: event already published')
        if not self.sqd.name:
            raise SquareDealError('Cannot mark as published: event name is not set')
        if not self.sqd.delayed_info:
            raise SquareDealError('Cannot mark as published: delayed information is not set')
        if not self.sqd.phases:
            raise SquareDealError('Cannot mark as published: no phases are defined')
        for sdphase in self.sqd.phases:
            sdphase.s_keys = [generate_session_key() for s in range(0, sdphase.sessions)]
        self.sqd.published = True
        self.sqd.tofile(arguments.get('sqd_file'), sqkpath=arguments.get('sqk_file'))

    def set_dv(self, **arguments):
        self.sqd.fromfile(arguments.get('sqd_file'), sqkpath=arguments.get('sqk_file'))
        if not self.sqd.published:
            raise SquareDealError('Cannot set delayed information value: event not published')
        self.sqd.delayed_value = arguments.get('delayed_information')
        self.sqd.tofile(arguments.get('sqd_file'), sqkpath=arguments.get('sqk_file'))

    def generate(self, **arguments):
        if arguments.get('bigdealx_path') is None:
            arguments['bigdealx_path'] = os.environ.get('BIGDEALX_PATH', None)
        SQD.BIGDEALX_PATH = arguments.get('bigdealx_path')
        self.sqd.fromfile(arguments.get('sqd_file'), sqkpath=arguments.get('sqk_file'))
        if not self.sqd.published:
            raise SquareDealError('Cannot generate PBN files: event info is not marked as published')
        if not self.sqd.delayed_value:
            raise SquareDealError('Cannot generate PBN files: delayed information value not set')
        self.sqd.generate(arguments.get('phase'), arguments.get('session'), reserve=arguments.get('reserve'))

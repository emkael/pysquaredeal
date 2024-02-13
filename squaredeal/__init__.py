import base64, os, re, subprocess

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


def parse_range_str(range_str, max_count):
    range_start = 0
    range_end = max_count
    if range_str:
        try:
            range_start = int(range_str) - 1
            range_end = range_start + 1
        except ValueError:
            range_match = re.match(r'([0-9]+)-([0-9]+)', range_str)
            if range_match:
                range_start = int(range_match.group(1))-1
                range_end = int(range_match.group(2))
            else:
                raise ValueError('Invalid range string: %s' % (range_str))
    if range_start < 0:
        raise ValueError('Value out of range: 0')
    if range_end > max_count:
        raise ValueError('Value out of range: %d' % (range_end))
    return range(range_start, range_end)


class SquareDeal(object):

    BIGDEALX_PATH = None

    def __init__(self, sqd_file, sqk_file=None, encoding=None):
        self.sqd = SQD()
        self.sqd_file = sqd_file
        self.sqk_file = sqk_file
        self.sqd_encoding = encoding

    def create(self, event_name=None, delayed_information=None, overwrite=False, **kwargs):
        self.sqd.name = event_name
        self.sqd.delayed_info = delayed_information

        if os.path.exists(self.sqd_file) and not overwrite:
            raise FileExistsError(self.sqd_file)

        self.sqd.tofile(self.sqd_file)

    def set_name(self, event_name, **kwargs):
        self.sqd.fromfile(self.sqd_file, sqkpath=self.sqk_file, encoding=self.sqd_encoding)

        if self.sqd.published:
            raise SquareDealError('Cannot change name: event already published')

        self.sqd.name = event_name

        self.sqd.tofile(self.sqd_file)

    def set_di(self, delayed_information, **kwargs):
        self.sqd.fromfile(self.sqd_file, sqkpath=self.sqk_file, encoding=self.sqd_encoding)

        if self.sqd.published:
            raise SquareDealError('Cannot change delayed information description: event already published')

        self.sqd.delayed_info = delayed_information

        self.sqd.tofile(self.sqd_file)

    def add_phase(self, sessions, boards, prefix, description='', **kwargs):
        self.sqd.fromfile(self.sqd_file, sqkpath=self.sqk_file, encoding=self.sqd_encoding)

        if self.sqd.published:
            raise SquareDealError('Cannot add phase: event already published')

        sdphase = SQDPhase()
        sdphase.sessions = sessions
        sdphase.boards = boards
        sdphase.prefix = prefix
        sdphase.info = description
        self.sqd.phases.append(sdphase)

        self.sqd.tofile(self.sqd_file)

    def publish(self, **kwargs):
        self.sqd.fromfile(self.sqd_file, sqkpath=self.sqk_file, encoding=self.sqd_encoding)

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

        self.sqd.tofile(self.sqd_file, sqkpath=self.sqk_file)

    def set_dv(self, delayed_information, **kwargs):
        self.sqd.fromfile(self.sqd_file, sqkpath=self.sqk_file, encoding=self.sqd_encoding)

        if not self.sqd.published:
            raise SquareDealError('Cannot set delayed information value: event not published')

        self.sqd.delayed_value = delayed_information

        self.sqd.tofile(self.sqd_file)

    def generate(self, phase, session, reserve=False, **kwargs):
        if not SquareDeal.BIGDEALX_PATH:
            raise SquareDealError('Path to BigDeal is not set, initialize SquareDeal.BIGDEALX_PATH value')

        self.sqd.fromfile(self.sqd_file, sqkpath=self.sqk_file, encoding=self.sqd_encoding)

        if not self.sqd.published:
            raise SquareDealError('Cannot generate PBN files: event info is not marked as published')
        if not self.sqd.delayed_value:
            raise SquareDealError('Cannot generate PBN files: delayed information value not set')

        try:
            phases_to_generate = parse_range_str(phase, len(self.sqd.phases))
            for phase_idx in phases_to_generate:
                phase = self.sqd.phases[phase_idx]
                delayed_info = base64.b64encode(self.sqd.delayed_value.encode('utf-8')).decode()
                sessions_to_generate = parse_range_str(session, phase.sessions)
                board_ranges = phase.parse_board_ranges(phase.boards)
                for session in sessions_to_generate:
                    session_key = phase.s_keys[session]
                    session_key_len = int(len(session_key)/2)
                    session_left = session_key[0:session_key_len]
                    session_right = session_key[session_key_len:]
                    reserve_info = 'reserve' if reserve else 'original'
                    args = [SquareDeal.BIGDEALX_PATH,
                            '-W', session_left,
                            '-e', session_right,
                            '-e', delayed_info,
                            '-e', reserve_info,
                            '-p', phase.output_file_name(session+1, reserve),
                            '-n', board_ranges[session]]
                    subprocess.run(
                        args,
                        cwd=os.path.realpath(os.path.dirname(self.sqd.sqd_path)) if self.sqd.sqd_path else None,
                        capture_output=True, check=True)
        except subprocess.CalledProcessError as ex:
            raise SquareDealError('BigDeal invocation failed: %s' % (ex.stderr))

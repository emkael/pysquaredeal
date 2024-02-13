import hashlib, os, random, re, shutil, string, subprocess


def generate_session_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=60))


def validate_board_range_str(range_str):
    if range_str.isdigit():
        return range_str
    if re.match(r'^[0-9]+-[0-9]+$', range_str):
        return range_str
    raise ValueError('Invalid board range definition: %s' % (range_str))


class SQDPhase(object):
    def __init__(self):
        self.sessions = 0
        self.boards = 0
        self.prefix = '#'
        self.info = ''
        self.s_keys = []

    def fromstring(self, phasestr):
        parts = phasestr.split(':')
        if len(parts) != 4:
            raise ValueError('Malformed phase definition: %s' % (phasestr))
        self.sessions = int(parts[0])
        self.boards = parts[1]
        self.prefix = parts[2]
        self.info = parts[3]

    def tostring(self):
        return ':'.join([str(self.sessions), str(self.boards), self.prefix, self.info or ''])

    def output_file_name(self, session, reserve=False):
        prefix = self.prefix
        session_search = re.findall(r'#+', prefix)
        for session_match in sorted(session_search, reverse=True):
            session_str = ('%0'+str(len(session_match))+'d') % (session)
            prefix = prefix.replace(session_match, session_str)
        if reserve:
            prefix += 'reserve'
        return prefix

    def parse_board_ranges(self, range_def):
        ranges = [range_str.strip() for range_str in range_def.split(',')]
        for range_str in ranges:
            validate_board_range_str(range_str)
        output_ranges = []
        while len(output_ranges) < self.sessions:
            output_ranges += ranges
        return output_ranges[0:self.sessions]



class SQD(object):

    def __init__(self):
        self._init_values()

    def _init_values(self):
        self.name = ''
        self.delayed_info = ''
        self.delayed_value = ''
        self.hash = ''
        self.phases = []
        self.published = False
        self.sqd_path = None

    def fromfile(self, sqdpath, sqkpath=None, encoding=None):
        if not encoding:
            encoding = 'utf-8'
        with open(sqdpath, encoding=encoding) as sqdfile:
            contents = [line.strip() for line in sqdfile.readlines()]
        self._init_values()
        for idx, line in enumerate(contents):
            if line.startswith('#'):
                continue
            linetype, _, linecontents = line.partition(' ')
            if linetype == 'TN':
                self.name = linecontents
            elif linetype == 'DI':
                self.delayed_info = linecontents
            elif linetype == 'DV':
                self.delayed_value = linecontents
            elif linetype == 'KH':
                self.hash = linecontents
                self.published = True
            elif linetype == 'SN':
                phase = SQDPhase()
                phase.fromstring(linecontents)
                self.phases.append(phase)
            else:
                raise ValueError('Unrecognized tag %s on line %d' % (linetype, idx))
        if self.published:
            for phase in self.phases:
                phase.s_keys = [None] * phase.sessions
            if sqkpath is None:
                sqkpath = self._deduce_sqk_path(sqdpath)
            try:
                with open(sqkpath, encoding=encoding) as sqkfile:
                    contents = [line.strip() for line in sqkfile.readlines()]
            except FileNotFoundError:
                raise FileNotFoundError('Unable to locate SQK file for %s' % (sqdpath))
            for line in contents:
                if not line.strip():
                    continue
                lineparts = line.split(':')
                if len(lineparts) != 2:
                    raise ValueError('Malformed SQK line: %s' % (line))
                session = lineparts[0].split(',')
                if len(session) != 2:
                    raise ValueError('Malformed SQK line: %s' % (line))
                phase_no = int(session[0])
                session_no = int(session[1])
                try:
                    self.phases[phase_no-1].s_keys[session_no-1] = lineparts[1]
                except IndexError:
                    raise IndexError(
                        'Session %s from SQK not declared in SQD' % (lineparts[0]))
            for ph_idx, phase in enumerate(self.phases):
                for s_idx, s_key in enumerate(phase.s_keys):
                    if s_key is None:
                        raise IndexError(
                            'Session %d,%d missing a key in SQK' % (ph_idx+1, s_idx+1))
            sqk_hash = self._get_file_hash(sqkpath)
            if sqk_hash != self.hash:
                raise ValueError(
                    'SQK hash mismtach: %s in SQD, % actual' % (self.hash, sqk_hash))
            self.sqd_path = sqdpath

    def _deduce_sqk_path(self, sqdpath):
        sqkpath = list(os.path.splitext(sqdpath))
        sqkpath[-1] = '.sqk'
        return ''.join(sqkpath)

    def _get_file_hash(self, path):
        with open(path, 'rb') as hashed_file:
            hash = hashlib.sha256()
            while True:
                chunk = hashed_file.read(1024)
                if not chunk:
                    break
                hash.update(chunk)
            return hash.hexdigest()

    def _make_backups(self, sqdpath, sqkpath):
        for f in [sqdpath, sqkpath]:
            if os.path.exists(f):
                shutil.copy(f, f + '.bak')

    def _write_session_keys(self, sqkpath):
        with open(sqkpath, 'wb') as sqkfile:
            for ph_idx, phase in enumerate(self.phases):
                for s_idx, session_key in enumerate(phase.s_keys):
                    if session_key is None:
                        raise IndexError(
                            'Missing session key for session %d,%d' % (ph_idx+1, s_idx+1))
                    sqkfile.write(
                        ('%d,%d:%s\r\n' % (ph_idx+1, s_idx+1, session_key)).encode('utf8'))
        self.hash = self._get_file_hash(sqkpath)

    def tofile(self, sqdpath, sqkpath=None, make_backups=True):
        if sqkpath is None:
            sqkpath = self._deduce_sqk_path(sqdpath)
        if make_backups:
            self._make_backups(sqdpath, sqkpath)
        if self.published:
            self._write_session_keys(sqkpath)
        sqd_contents = []
        sqd_contents.append('TN %s\n' % (self.name or ''))
        sqd_contents.append('DI %s\n' % (self.delayed_info or ''))
        if self.published:
            sqd_contents.append('DV %s\n' % (self.delayed_value or ''))
        for phase in self.phases:
            sqd_contents.append('SN %s\n' % (phase.tostring()))
        if self.published:
            sqd_contents.append('KH %s\n' % (self.hash))
        with open(sqdpath, 'w') as sqdfile:
            sqdfile.writelines(sqd_contents)

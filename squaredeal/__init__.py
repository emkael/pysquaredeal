import base64, hashlib, os, random, shutil, string, subprocess


class SquareDealError(Exception):
    pass


class SquareDealPhase(object):
    def __init__(self):
        self.sessions = 0
        self.boards = 0
        self.prefix = '#'
        self.info = ''
        self.s_keys = []

    def fromstring(self, phasestr):
        parts = phasestr.split(':')
        if len(parts) != 4:
            raise SquareDealError('Malformed phase definition: %s' % (phasestr))
        self.sessions = int(parts[0])
        self.boards = int(parts[1])
        self.prefix = parts[2]
        self.info = parts[3]
        self.s_keys = [None] * self.sessions

    def tostring(self):
        return ':'.join([str(self.sessions), str(self.boards), self.prefix, self.info or ''])

    def _output_file_name(self, session):
        return self.prefix.replace('#', str(session))

    def generate(self, session, delayed_info, reserve=False):
        if not SquareDeal.BIGDEALX_PATH:
            raise SquareDealError('Path to BigDeal is not set, initialize SquareDeal.BIGDEALX_PATH value')
        delayed_info = base64.b64encode(delayed_info.encode('utf-8')).decode()
        sessions_to_generate = range(0, self.sessions) if session is None else [session-1]
        for session in sessions_to_generate:
            session_key = self.s_keys[session]
            session_key_len = int(len(session_key)/2)
            session_left = session_key[0:session_key_len]
            session_right = session_key[session_key_len:]
            reserve_info = 'reserve' if reserve else 'original'
            args = [SquareDeal.BIGDEALX_PATH,
                    '-W', session_left,
                    '-e', session_right,
                    '-e', delayed_info,
                    '-e', reserve_info,
                    '-p', self._output_file_name(session+1),
                    '-n', str(self.boards)]
            subprocess.run(args, cwd=os.path.realpath(SquareDeal.BIGDEALX_PATH))


class SquareDeal(object):

    BIGDEALX_PATH=None

    def __init__(self):
        self.name = ''
        self.delayed_info = ''
        self.hash = ''
        self.phases = []
        self.published = False

    def fromfile(self, sqdpath, sqkpath=None, encoding='utf-8'):
        with open(sqdpath, encoding=encoding) as sqdfile:
            contents = [line.strip() for line in sqdfile.readlines()]
        for idx, line in enumerate(contents):
            linetype, _, linecontents = line.partition(' ')
            if linetype == 'TN':
                self.name = linecontents
            elif linetype == 'DI':
                self.delayed_info = linecontents
            elif linetype == 'KH':
                self.hash = linecontents
            elif linetype == 'PU':
                self.published = True
            elif linetype == 'SN':
                phase = SquareDealPhase()
                phase.fromstring(linecontents)
                self.phases.append(phase)
            else:
                raise SquareDealError('Unrecognized tag %s on line %d' % (linetype, idx))
        if sqkpath is None:
            sqkpath = self._deduce_sqk_path(sqdpath)
        try:
            with open(sqkpath, encoding=encoding) as sqkfile:
                contents = [line.strip() for line in sqkfile.readlines()]
        except FileNotFoundError:
            raise SquareDealError('Unable to locate SQK file for %s' % (sqdpath))
        for line in contents:
            if not line.strip():
                continue
            lineparts = line.split(':')
            if len(lineparts) != 2:
                raise SquareDealError('Malformed SQK line: %s' % (line))
            session = lineparts[0].split(',')
            if len(session) != 2:
                raise SquareDealError('Malformed SQK line: %s' % (line))
            phase_no = int(session[0])
            session_no = int(session[1])
            try:
                self.phases[phase_no-1].s_keys[session_no-1] = lineparts[1]
            except IndexError:
                raise SquareDealError('Session %s from SQK not declared in SQD' % (lineparts[0]))
        for ph_idx, phase in enumerate(self.phases):
            for s_idx, s_key in enumerate(phase.s_keys):
                if s_key is None:
                    raise SquareDealError('Session %d,%d missing a key in SQK' % (ph_idx+1, s_idx+1))
        sqk_hash = self._get_file_hash(sqkpath)
        if sqk_hash != self.hash:
            raise SquareDealError('SQK hash mismtach: %s in SQD, % actual' % (self.hash, sqk_hash))

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
                        raise SquareDealError('Missing session key for session %d,%d' % (ph_idx+1, s_idx+1))
                    sqkfile.write(('%d,%d:%s\r\n' % (ph_idx+1, s_idx+1, session_key)).encode('utf8'))
        self.hash = self._get_file_hash(sqkpath)

    def tofile(self, sqdpath, sqkpath=None, make_backups=True):
        if sqkpath is None:
            sqkpath = self._deduce_sqk_path(sqdpath)
        if make_backups:
            self._make_backups(sqdpath, sqkpath)
        self._write_session_keys(sqkpath)
        sqd_contents = []
        sqd_contents.append('TN %s\n' % (self.name or ''))
        sqd_contents.append('KH %s\n' % (self.hash))
        sqd_contents.append('DI %s\n' % (self.delayed_info or ''))
        for phase in self.phases:
            sqd_contents.append('SN %s\n' % (phase.tostring()))
        if self.published:
            sqd_contents.append('PU\n')
        with open(sqdpath, 'w') as sqdfile:
            sqdfile.writelines(sqd_contents)

    def _generate_session_key(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=60))

    def add_phase(self, session_count, board_count, file_prefix, description=None):
        phase = SquareDealPhase()
        phase.sessions = session_count
        phase.boards = board_count
        phase.prefix = file_prefix
        phase.info = description
        for i in range(0, phase.sessions):
            phase.s_keys.append(self._generate_session_key())
        self.phases.append(phase)

    def generate(self, phase, session):
        phases_to_generate = range(0, len(self.phases)) if phase is None else [phase-1]
        for phase in phases_to_generate:
            self.phases[phase].generate(session, self.delayed_info)

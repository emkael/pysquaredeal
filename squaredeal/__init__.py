import hashlib, os


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


class SquareDeal(object):
    def __init__(self):
        self.name = ''
        self.delayed_info = ''
        self.hash = ''
        self.phases = []
        self.published = False

    def fromfile(self, sqdpath, encoding='utf-8', sqkpath=None):
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
            sqkpath = list(os.path.splitext(sqdpath))
            sqkpath[-1] = '.sqk'
            sqkpath = ''.join(sqkpath)
        try:
            with open(sqkpath, encoding=encoding) as sqkfile:
                contents = [line.strip() for line in sqkfile.readlines()]
        except FileNotFoundError:
            raise SquareDealError('Unable to locate SQK file for %s' % (sqdpath))
        for line in contents:
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
        with open(sqkpath, 'rb') as sqkfile:
            sqk_hash = hashlib.sha256()
            while True:
                sqk_chunk = sqkfile.read(1024)
                if not sqk_chunk:
                    break
                sqk_hash.update(sqk_chunk)
            sqk_hash = sqk_hash.hexdigest()
        if sqk_hash != self.hash:
            raise SquareDealError('SQK hash mismtach: %s in SQD, % actual' % (self.hash, sqk_hash))

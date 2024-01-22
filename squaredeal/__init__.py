class SquareDealError(Exception):
    pass


def squaredeal_board_range(arg_str):
    from squaredeal.sqd import validate_board_range_str
    ranges = []
    for range_str in arg_str.split(','):
        range_match = re.match(r'^([0-9]+)x([0-9]+)$', range_str)
        if range_match:
            subrange_count = int(range_match.group(2))
            ranges += ['%d-%d' % (i*subrange_count+1, (i+1)*subrange_count) for i in range(0, int(range_match.group(1)))]
            continue
        ranges += [validate_board_range_str(range_str)]
    return ','.join(ranges)

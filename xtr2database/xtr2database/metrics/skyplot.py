from collections import defaultdict


def _extract_coord(f, data):
    next(f) # entête partie

    line = next(f)
    while line != "\n":
        splitted = line.split()

        constel = splitted[0][0:3]
        coord = splitted[0][3:7]

        data[constel][coord].append(
            [int(v) if v != "-" else -1 for v in splitted[4:]]
        )

        line = next(f)


def extract_elevation_azimut(f):
    data = defaultdict(lambda: dict(ELE=list(), AZI=list()))

    # elevation
    _extract_coord(f, data)

    # azimut
    _extract_coord(f, data)

    return data
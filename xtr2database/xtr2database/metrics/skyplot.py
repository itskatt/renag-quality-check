from collections import defaultdict
import datetime as dt


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


def extract_individual_multipath(f, date):
    data = defaultdict(lambda: defaultdict(list))

    while True:
        line = next(f)

        if line == "\n":
            # est-ce que on se situe entre deux bandes ou à
            # la fin des données à extraire
            line = next(f)
            if line == "\n":
                # fin des données à extraire
                break

        # on peut commencer à extraire
        splitted = line.split()

        constel = splitted[0][0:3]
        band = splitted[0][4:7]

        time = dt.time.fromisoformat(splitted[2])
        line_datetime = dt.datetime.combine(date, time)

        data[constel][band].append((
            line_datetime,
            [int(v) if v != "-" else -1 for v in splitted[4:]]
        ))

    return data

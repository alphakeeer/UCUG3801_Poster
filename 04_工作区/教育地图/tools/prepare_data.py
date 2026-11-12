"""Prepare compact, traceable school records and an offline OSM basemap."""

import csv
import json
import math
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
LIBRARY = ROOT / '03_背景/教育专题'
OUT = PROJECT / 'dist/assets'


def read_csv(name):
    with (LIBRARY / '数据' / name).open(encoding='utf-8-sig') as handle:
        return list(csv.DictReader(handle))


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')))


def project(lon, lat):
    radius = 6378137
    origin_lat = math.radians(23.121)
    x = radius * math.radians(lon - 113.332)
    y = radius * (math.log(math.tan(math.pi / 4 + origin_lat / 2)) -
                  math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))
    return [round(x, 1), round(y, 1)]


def campus_center(geometry):
    """Find a small campus polygon's area centroid using a local origin."""
    origin = geometry[0]
    vertices = [(point['lon'] - origin['lon'], point['lat'] - origin['lat'])
                for point in geometry]
    twice_area = longitude = latitude = 0
    for first, second in zip(vertices, vertices[1:] + vertices[:1]):
        cross = first[0] * second[1] - second[0] * first[1]
        twice_area += cross
        longitude += (first[0] + second[0]) * cross
        latitude += (first[1] + second[1]) * cross
    if abs(twice_area) < 1e-14:
        return (sum(point['lon'] for point in geometry) / len(geometry),
                sum(point['lat'] for point in geometry) / len(geometry))
    return (origin['lon'] + longitude / (3 * twice_area),
            origin['lat'] + latitude / (3 * twice_area))


def normalized_name(name):
    return name.replace('广州市', '').replace('天河区', '').replace(' ', '')


def points(geometry):
    result = []
    for point in geometry:
        if 'lon' in point and 'lat' in point:
            coordinate = project(point['lon'], point['lat'])
            if not result or coordinate != result[-1]:
                result.append(coordinate)
    return result


def join_segments(segments):
    remaining = [list(segment) for segment in segments if len(segment) > 1]
    rings = []
    while remaining:
        chain = remaining.pop()
        changed = True
        while changed and chain[0] != chain[-1]:
            changed = False
            for index, segment in enumerate(remaining):
                if chain[-1] == segment[0]:
                    chain.extend(segment[1:])
                elif chain[-1] == segment[-1]:
                    chain.extend(segment[-2::-1])
                elif chain[0] == segment[-1]:
                    chain = segment[:-1] + chain
                elif chain[0] == segment[0]:
                    chain = segment[:0:-1] + chain
                else:
                    continue
                remaining.pop(index)
                changed = True
                break
        rings.append(chain)
    return rings


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = json.loads((LIBRARY / '地图/OSM_猎德周边_20261112.json').read_text())
    elements = raw['elements']
    osm = {(row['type'], row['id']): row for row in elements}
    geocodes = json.loads((LIBRARY / '地图/学校地理编码检索.json').read_text())
    by_record = {record_id: row for row in geocodes for record_id in row['ids']}
    # Match campus-specific names, retaining the OSM name as an auditable alias.
    campus_matches = {
        'E004-045': ('node', 11032482824), 'E004-052': ('way', 1288223512),
        'E004-053': ('way', 860062302), 'E004-054': ('node', 11032417060),
        'E006-021': ('node', 13608309010), 'E006-078': ('node', 11032417055),
        'E006-087': ('way', 993462500), 'E006-105': ('node', 12916526050),
        'P01': ('way', 585942444), 'J01': ('way', 585942444),
        'P02': ('way', 662685556), 'J02': ('way', 662685558),
        'P03': ('way', 731236117), 'P04': ('way', 299684380),
        'P06': ('way', 206226405), 'P07': ('way', 561739692),
        'P08': ('way', 1288222584), 'P09': ('way', 858600100),
        'J03': ('way', 206226293), 'J04': ('way', 426075307),
        'J05': ('way', 585943745), 'P10': ('way', 662685584),
        'J06': ('way', 662685584), 'P11': ('way', 662689775),
        'P12': ('way', 1313653478), 'J07': ('way', 1313653478),
        'P13': ('way', 1484142606),
    }
    sources = {row['source_id']: dict(id=row['source_id'], title=row['title'],
               url=row['url'], date=row.get('document_date', ''),
               note=row.get('scope_note', ''))
               for row in json.loads((LIBRARY / '下载清单.json').read_text())}
    plans = read_csv('研究点位招生计划.csv')
    charges = {row['record_id']: row for row in read_csv('逐校收费核验状态.csv')}
    school_records = []
    raw_records = read_csv('猎德及周边幼儿园候选.csv') + read_csv('小学初中校区学段.csv')
    for row in raw_records:
        record_id = row['record_id']
        kindergarten = record_id.startswith('E')
        stage = 'kg' if kindergarten else 'primary' if row['stage'] == '小学' else 'junior'
        organizer = row.get('organizer') or row.get('ownership')
        owner = 'private' if organizer == '民办' else 'other' if organizer == '国有企业办' else 'public'
        short = row['name'].replace('广州市天河区', '').replace('广州市', '')
        if row.get('campus') and row['campus'] != '本部':
            short += ' · ' + row['campus']
        school = dict(id=record_id, name=row['name'], short=short, stage=stage,
                      campus=row.get('campus', '本园'), address=row['address'],
                      institution=row.get('institution_id', record_id), owner=owner,
                      organizer=organizer, inclusive=row.get('inclusive_raw') == '普惠性',
                      grade=row.get('grade', ''), phone=row.get('phone', ''),
                      spatial=row['spatial_status'], rules=row.get('access_rule') or row.get('access_rules'),
                      street=row.get('inspection_street') or row.get('street', ''),
                      source=row.get('source_id') or row.get('address_source_id'),
                      locator=f"原表第{row['source_serial']}项" if kindergarten else row.get('admission_locator', ''),
                      inspection=row.get('inspection_2025', ''), position=None)
        match = campus_matches.get(record_id)
        if match:
            feature = osm[match]
            geometry = feature.get('geometry', [])
            if geometry and geometry[0] == geometry[-1]:
                geometry = geometry[:-1]
            lon, lat = campus_center(geometry) if geometry else (feature['lon'], feature['lat'])
            school['position'] = dict(lon=lon, lat=lat, xy=project(lon, lat),
                name=feature.get('tags', {}).get('name', ''),
                url=f'https://www.openstreetmap.org/{match[0]}/{match[1]}',
                method='校园面几何中心' if geometry else 'OSM设施点',
                note='地图旧名为东校区，校区别名与实际入口待进一步核验' if record_id == 'P03' else '入口位置与实地路线待审计')
        else:
            search = by_record.get(record_id, {})
            candidates = search.get('results', [])
            candidates = [item for item in candidates
                          if item.get('type') in ['school', 'kindergarten']
                          and normalized_name(item.get('name', '')) == normalized_name(row['name'])]
            if len(candidates) == 1:
                candidate = candidates[0]
                lon, lat = float(candidate['lon']), float(candidate['lat'])
                school['position'] = dict(lon=lon, lat=lat, xy=project(lon, lat),
                    name=candidate.get('name', ''),
                    url=f"https://www.openstreetmap.org/{candidate['osm_type']}/{candidate['osm_id']}",
                    method='OSM地理编码设施点', note='入口位置与实地路线待审计')
        if kindergarten:
            school['classes'] = int(row['planned_classes'])
            if row.get('social_lottery_total'):
                school['lottery'] = dict(total=int(row['social_lottery_total']),
                    owners=int(row['owner_children']), random=int(row['remaining_random_lottery']))
        school['plans'] = [dict(category=item['plan_category'], amount=int(item['amount']),
            unit=item['unit'], note=item['note'], source=item['source_id'], locator=item['locator'])
            for item in plans if item['target_id'] in [record_id, school['institution']]]
        charge = charges[record_id]
        school['tuition'] = int(charge['approved_tuition_amount']) if charge.get('approved_tuition_amount') else 0 if stage != 'kg' and owner != 'private' else None
        school['tuitionSource'] = charge.get('approved_tuition_source') or ('E011' if school['tuition'] == 0 else '')
        school['tuitionPeriod'] = charge.get('approved_tuition_period', '')
        school_records.append(school)

    coordinate_path = LIBRARY / '地图/学校点位_WGS84.csv'
    with coordinate_path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            'record_id', 'name', 'stage', 'longitude', 'latitude',
            'coordinate_system', 'method', 'map_name', 'source_url', 'note', 'checked_date'])
        writer.writeheader()
        for school in school_records:
            position = school['position'] or {}
            writer.writerow(dict(record_id=school['id'], name=school['name'], stage=school['stage'],
                longitude=position.get('lon', ''), latitude=position.get('lat', ''),
                coordinate_system='WGS84' if position else '',
                method=position.get('method', '位置待核'), map_name=position.get('name', ''),
                source_url=position.get('url', ''),
                note=position.get('note', '已保存官方地址，未取得可靠校园位置'), checked_date='2026-11-12'))

    roads, water, parks, boundaries, labels = [], [], [], [], []
    for element in elements:
        tags = element.get('tags', {})
        geometry = element.get('geometry', [])
        if geometry and tags.get('highway'):
            road_class = tags['highway']
            roads.append([road_class, points(geometry)])
            if tags.get('name') and road_class in ['primary', 'secondary', 'tertiary'] and len(geometry) > 2:
                middle = geometry[len(geometry) // 2]
                labels.append(dict(name=tags['name'], xy=project(middle['lon'], middle['lat']), kind='road'))
        if geometry and tags.get('natural') == 'water':
            water.append([points(geometry)])
        if geometry and tags.get('leisure') == 'park':
            parks.append(points(geometry))
            if tags.get('name') in ['珠江公园', '花城广场', '海心沙亚运公园', '广州发展公园']:
                lon = sum(x['lon'] for x in geometry) / len(geometry)
                lat = sum(x['lat'] for x in geometry) / len(geometry)
                labels.append(dict(name=tags['name'], xy=project(lon, lat), kind='park'))
        if element['type'] == 'relation' and tags.get('natural') == 'water':
            outer = join_segments([points(member.get('geometry', [])) for member in element['members'] if member.get('role') == 'outer'])
            inner = join_segments([points(member.get('geometry', [])) for member in element['members'] if member.get('role') == 'inner'])
            water.append(outer + inner)
        if element['type'] == 'relation' and tags.get('boundary'):
            rings = join_segments([points(member.get('geometry', [])) for member in element['members'] if member.get('role') == 'outer'])
            boundaries.append(dict(name=tags['name'], rings=rings,
                                   url=f"https://www.openstreetmap.org/relation/{element['id']}"))
    relations = read_csv('小学初中对口与派位关系.csv')
    write_json('schools.json', dict(updated='2026-11-10', geographyUpdated='2026-11-12',
        schools=school_records, sources=sources, relations=relations,
        rules=read_csv('招生渠道与家庭类别.csv')))
    write_json('basemap.json', dict(roads=roads, water=water, parks=parks,
        boundaries=boundaries, labels=labels,
        bounds=[project(113.305, 23.145), project(113.385, 23.100)],
        attribution='© OpenStreetMap contributors · ODbL',
        timestamp=raw.get('osm3s', {}).get('timestamp_osm_base', '')))
    print('Records', len(school_records), 'Mapped', sum(bool(s['position']) for s in school_records))
    print('Local geography bytes', (OUT / 'basemap.json').stat().st_size)


if __name__ == '__main__':
    main()

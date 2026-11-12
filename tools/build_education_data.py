"""Extract official education tables with source and row provenance."""

import csv
import json
from pathlib import Path

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / '03_背景/教育专题'
DATA = LIBRARY / '数据'


def write_csv(name, records, columns=None):
    if columns is None:
        columns = list(dict.fromkeys(key for row in records for key in row))
    with (DATA / name).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)


def expanded_rows(table):
    """Expand HTML merged cells, retaining original row numbers separately."""
    occupied = {}
    result = []
    for row_index, row in enumerate(table.xpath('.//tr')):
        column = 0
        for cell in row.xpath('./td|./th'):
            while (row_index, column) in occupied:
                column += 1
            value = ' '.join(' '.join(cell.itertext()).split())
            for vertical in range(int(cell.get('rowspan', 1))):
                for horizontal in range(int(cell.get('colspan', 1))):
                    occupied[row_index + vertical, column + horizontal] = value
            column += int(cell.get('colspan', 1))
        columns = [key[1] for key in occupied if key[0] == row_index]
        result.append([occupied.get((row_index, index), '') for index in range(max(columns, default=-1) + 1)])
    return result


def main():
    DATA.mkdir(exist_ok=True)
    sources = {row['source_id']: row for row in json.loads((LIBRARY / '下载清单.json').read_text())}
    extracted = []
    tables = {}
    for source_id in ['E004', 'E005', 'E006', 'E025', 'E026', 'E027', 'E028', 'E029', 'E036']:
        record = sources[source_id]
        document = html.fromstring((ROOT / record['local_file']).read_bytes())
        table = document.xpath('//table')[0]
        rows = expanded_rows(table)
        tables[source_id] = rows
        for row_number, values in enumerate(rows, 1):
            extracted.append(dict(source_id=source_id, html_row=row_number,
                                  cells_json=json.dumps(values, ensure_ascii=False),
                                  source_url=record['url']))
    write_csv('官方名录原表逐行.csv', extracted)

    kindergartens = []
    for source_id in ['E004', 'E005', 'E006']:
        for row_number, values in enumerate(tables[source_id], 1):
            if not values[0].isdigit():
                continue
            row = dict(record_id=f'{source_id}-{int(values[0]):03}', source_id=source_id,
                       source_serial=int(values[0]), html_row=row_number, year=2026,
                       stage='幼儿园小班', name=values[1], address=values[2],
                       source_url=sources[source_id]['url'])
            if source_id == 'E004':
                row.update(organizer='教育部门办', planned_classes=values[3],
                           social_lottery_total=values[4], owner_children=values[5],
                           remaining_random_lottery=values[6], phone=values[7], notes=values[8])
                row['lottery_relationship'] = '分项相加等于社会派位总数'
                if int(values[5]) + int(values[6]) != int(values[4]):
                    row['lottery_relationship'] = '分项超出社会派位总数，结合E003业主优先延展规则核验'
            elif source_id == 'E005':
                row.update(organizer=values[3], grade=values[4], phone=values[5],
                           planned_classes=values[6], notes=values[7])
            else:
                row.update(organizer='民办', license=values[3], grade=values[4], phone=values[5],
                           inclusive_raw=values[6], inspection_2024=values[7],
                           planned_classes=values[8], notes=values[9])
            kindergartens.append(row)
    write_csv('2026天河幼儿园完整名录.csv', kindergartens)

    selection = {
        'E004': [13, 31, 36, 41, 42, 43, 45, 52, 53, 54, 57],
        'E005': [15, 32],
        'E006': [21, 24, 25, 59, 60, 61, 72, 73, 74, 78, 79, 80, 87, 95, 105, 108, 114],
    }
    verified_core = {'E004-036', 'E004-052', 'E004-054', 'E005-032'}
    address_core = {'E006-072', 'E006-073', 'E006-074', 'E006-078', 'E006-079', 'E006-105'}
    inspection_path = DATA / '民办学校幼儿园年检原表逐行.csv'
    inspections = {}
    if inspection_path.exists():
        with inspection_path.open(encoding='utf-8-sig') as handle:
            for record in csv.DictReader(handle):
                values = json.loads(record['cells_json'])
                if record['source_id'] == 'E058-A001' and isinstance(values[0], (int, float)):
                    inspections[values[1].strip()] = dict(
                        inspection_street=values[4], inspection_2025=values[5],
                        inspection_source='E058-A001', inspection_locator=f"{record['sheet']}第{record['row']}行")
    nearby = []
    for row in kindergartens:
        if row['source_serial'] not in selection[row['source_id']]:
            continue
        status = '周边候选，距离待核'
        basis = '相邻冼村、天河南或员村片区地址检索，尚未计算1/2公里缓冲'
        if row['record_id'] in verified_core:
            status = '猎德主体，官方街道归属文本'
            basis = 'E025街道归属及现址交叉核验' if row['source_id'] == 'E004' else 'E024明确利民社区、猎德街，E005核现址'
        if row['record_id'] in address_core:
            status = '猎德主体候选，地址四至核验'
            basis = '地址落于历史街道四至所指片区，现行精确界线及入口待核'
        inspection = inspections.get(row['name'], {})
        if inspection:
            status = '猎德主体，官方街道归属文本' if inspection['inspection_street'] == '猎德街道' else '周边候选，距离待核'
            basis = f"2026发布的2025年度最终年检表，列属{inspection['inspection_street']}，结合E006核2026招生地址"
        nearby.append(dict(row, spatial_status=status, spatial_basis=basis,
                           longitude='', latitude='', coordinate_system='',
                           fee_status='逐园2026公示待核', access_rule='K1' if row['source_id'] == 'E004' else 'K2' if row['source_id'] == 'E005' else 'K3', **inspection))
    write_csv('猎德及周边幼儿园候选.csv', nearby)
    report = ['# 幼儿园逐园资料卡', '', '资料核对日为2026-11-10。园区为计数单位，周边候选尚待固定半径空间筛选。', '',
              'K1为教育部门办招生规则，K2为其他部门办园规则，K3为民办园规则。细节见招生渠道与费用报告。', '']
    for row in nearby:
        report += [f"## {row['record_id']}　{row['name']}", '',
                   f"- 地址为{row['address']}。范围登记为{row['spatial_status']}。",
                   f"- 举办类型为{row['organizer']}，2026小班计划{row['planned_classes']}班。"]
        if row['source_id'] == 'E004':
            report.append(f"- 面向社会电脑派位{row['social_lottery_total']}人，含业主子女{row['owner_children']}人，剩余随机派位{row['remaining_random_lottery']}人。")
        else:
            report.append(f"- 办园等级按原表为{row.get('grade', '')}。普惠字段为{row.get('inclusive_raw', '该表无此字段')}。")
        if row.get('inspection_source'):
            report.append(f"- 2025年度最终年检为{row['inspection_2025']}，列属{row['inspection_street']}。2026发布的{row['inspection_source']}，{row['inspection_locator']}。")
        report += [f"- 招生规则关联{row['access_rule']}，逐园配套范围及收费公示待核。",
                   f"- 园所咨询电话按公开名录为{row['phone']}。",
                   f"- 来源为{row['source_id']}第{row['source_serial']}项，HTML第{row['html_row']}行。[官方原表]({row['source_url']})", '']
    (LIBRARY / '幼儿园逐园资料卡.md').write_text('\n'.join(report) + '\n')
    print('Official raw rows', len(extracted), 'Kindergarten campuses', len(kindergartens), 'Selected candidates', len(nearby))


if __name__ == '__main__':
    main()

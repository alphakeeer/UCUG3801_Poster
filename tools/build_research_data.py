"""Build reproducible research tables from archived sources and documented extractions."""

import csv
import hashlib
import json
import re
from pathlib import Path

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / '03_背景/资料库'
DATA = ROOT / '03_背景/数据'
CATALOG = json.loads((LIBRARY / '下载清单.json').read_text())
SOURCES = {row['source_id']: row for row in CATALOG}


def write_csv(name, rows):
    with (DATA / name).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def directory_rows(source_id):
    source = SOURCES[source_id]
    tree = html.parse(str(ROOT / source['local_file']))
    rows = []
    for element in tree.xpath('//tr'):
        cells = [' '.join(cell.text_content().split()) for cell in element.xpath('./td')]
        if cells and cells[0].isdigit() and len(cells) == 7:
            rows.append(dict(zip(
                ['serial', 'name', 'address', 'opening_time_raw', 'area_sqm_raw', 'phone', 'authority'],
                cells,
            )))
    assert len(rows) > 250 and len({row['serial'] for row in rows}) == len(rows)
    for row in rows:
        row.update(source_id=source_id, publication_date=source['web_publication_date'],
                   retrieved_date='2026-11-09', evidence_type='official_directory')
    return rows


def schedule_intervals(raw):
    normalized = raw.replace('，', '').replace(' ', '')
    if normalized == '星期一至星期日9:00-12:00、14:00-18:00':
        return [(day, start, end) for day in range(1, 8) for start, end in [(9, 12), (14, 18)]]
    if normalized == '星期一至星期五9:00-18:00星期六9:00-12:00':
        return [(day, 9, 18) for day in range(1, 6)] + [(6, 9, 12)]
    raise ValueError(f'Unreviewed opening schedule: {raw}')


def build_service_tables():
    current = directory_rows('S23')
    previous = directory_rows('S24')
    write_csv('01_天河区文化设施目录_20260522_原始267条.csv', current)
    write_csv('02_天河区文化设施目录_20251107_原始265条.csv', previous)
    old_by_name = {row['name']: row for row in previous}
    selected = [row for row in current if row['name'].startswith('猎德街')]
    assert len(selected) == 8
    facilities, intervals, comparisons, scenarios = [], [], [], []
    availability = {
        'C1_工作日10至12时': [(day, 10, 12) for day in range(1, 6)],
        'C2_工作日19至21时': [(day, 19, 21) for day in range(1, 6)],
        'C3_周末10至12时': [(6, 10, 12), (7, 10, 12)],
        'C4_工作日12至14时': [(day, 12, 14) for day in range(1, 6)],
    }
    for index, row in enumerate(selected, 1):
        facility_id = f'LD{index:02d}'
        times = schedule_intervals(row['opening_time_raw'])
        total = sum(end - start for day, start, end in times)
        weekend = sum(end - start for day, start, end in times if day >= 6)
        after18 = sum(max(0, end - max(18, start)) for day, start, end in times)
        facilities.append(dict(
            facility_id=facility_id, name=row['name'],
            facility_level='街道文化站' if index == 1 else '社区综合性文化服务中心',
            address=row['address'], area_sqm=float(row['area_sqm_raw']),
            opening_time_raw=row['opening_time_raw'], listed_weekly_hours=total,
            listed_weekend_hours=weekend, weekend_share_pct=round(100 * weekend / total, 4),
            listed_after18_hours=after18, source_id='S23', source_row=row['serial'],
            publication_date='2026-05-22', observed_on_site='未核验',
            scope_note='目录标示时段；临时活动、节假日及实际开放情况待核验',
        ))
        for day, start, end in times:
            intervals.append(dict(facility_id=facility_id, name=row['name'], weekday_iso=day,
                                  start_time=f'{start:02d}:00', end_time=f'{end:02d}:00',
                                  hours=end-start, source_id='S23'))
        old = old_by_name[row['name']]
        same_times = schedule_intervals(old['opening_time_raw']) == times
        area_delta = float(row['area_sqm_raw']) - float(old['area_sqm_raw'])
        comparisons.append(dict(
            facility_id=facility_id, name=row['name'], old_source_id='S24', new_source_id='S23',
            old_serial=old['serial'], new_serial=row['serial'],
            old_area_sqm=old['area_sqm_raw'], new_area_sqm=row['area_sqm_raw'],
            listed_area_delta_sqm=area_delta, same_address=old['address'] == row['address'],
            same_opening_intervals=same_times,
            change_interpretation='面积记载发生变化，原因与口径待核验' if area_delta else '面积及时段记载一致，部分标点和序号变化',
        ))
        for scenario_id, windows in availability.items():
            overlap = sum(max(0, min(end, available_end) - max(start, available_start))
                          for day, start, end in times
                          for available_day, available_start, available_end in windows
                          if day == available_day)
            scenarios.append(dict(
                scenario_id=scenario_id, facility_id=facility_id, name=row['name'],
                data_kind='constructed_scenario', available_hours=sum(b-a for d,a,b in windows),
                listed_overlap_hours=overlap, source_id='S23',
                assumption='假设可用时窗，尚未加入出行、预约、资格、容量及活动类型约束',
            ))
    write_csv('03_猎德街8项设施_开放时段与面积.csv', facilities)
    write_csv('04_猎德街8项设施_逐日开放区间.csv', intervals)
    write_csv('05_猎德街目录_2025与2026版本比较.csv', comparisons)
    write_csv('06_开放时段交集_假设情景.csv', scenarios)
    return facilities, intervals, scenarios


HOUSING_FACTS = [
    ('H01','酒店规划许可用地面积',49933,'平方米','2007-08-07','酒店建设地块','S02','许可正文','单地块用地面积，不能代表整个改造项目'),
    ('H02','村经济发展公司总收入',55215,'万元','2011','猎德村经济发展公司','S03','PDF第458页','公司总收入，与利润、分红及居民收入分别统计'),
    ('H03','公司总收入同比增长',23,'百分比','2011比2010','猎德村经济发展公司','S03','PDF第458页','原件报数，未取得两年完整会计报表'),
    ('H04','改造前总建筑面积',68.6,'万平方米','改造前，统计年份未明','历史猎德村','S04','猎德村变迁图文','建筑面积口径，与用地面积分别保存'),
    ('H05','改造后总建筑用地',13.1,'万平方米','改造后，统计年份未明','档案图文所指建设范围','S04','猎德村变迁图文','用地面积口径，不与H04计算降幅'),
    ('H06','改造后高层住宅栋数',37,'栋','改造后','复建安置区','S04','猎德村变迁图文','栋数无法直接推导户数或独立家庭数'),
    ('H07','研究问卷有效样本',271,'份','2013-03','猎德复建房社区调查','S14','PDF第3页，1.2资料来源','来自既有学术研究，非本组问卷'),
    ('H08','有效样本中的猎德村民',98,'人','2013-03','同H07','S14','PDF第3页，1.2资料来源','与271份整体样本的分析对象区分'),
    ('H09','研究半结构访谈',39,'份','2011-03至2018-02','学术研究滚雪球样本','S14','PDF第3页，1.2资料来源','非本组访谈，无法代表全部居民'),
    ('H10','户籍人口',7329,'人','2018','文章所述猎德社区','S14','PDF第3页，1.1研究区域','历史行政描述，与其他年份及范围的人口不可直接拼接'),
    ('H11','流动人口',8449,'人','2018','文章所述猎德社区','S14','PDF第3页，1.1研究区域','流动人口与村集体成员、住宅租户分类不等同'),
    ('H12','复建房屋出租单位',4042,'套','2025预算文字所述，统计时点未明','猎德复建区','S17','PDF第33页，印刷第31页','预算背景资料，未证实为2025年末实际数'),
    ('H13','居住白领来穗人员',12477,'人','2025预算文字所述，统计时点未明','猎德复建区','S17','PDF第33页，印刷第31页','白领分类及人数口径未披露'),
    ('H14','公司提起的宅基地纠纷案件',8,'件','2007','年鉴所列系列案件','S52','PDF第183页','司法历史记录，与全部协商分歧人数区分'),
    ('H15','系列案件调解后撤诉',2,'件','2007','H14中案件','S52','PDF第183页','同一系列案件子集'),
    ('H16','系列案件其余判决',6,'件','2007','H14中案件','S52','PDF第183至184页','年鉴记有2008年上诉及执行和解后续'),
    ('H17','初步方案增加安置面积购买单价',3500,'元每平方米','2007-06新闻所述初步方案','符合初步方案条件的增加面积','S50','具体措施段落','媒体转述初步方案，未取得正式批复原件，不能作为现行报价'),
]

PERFORMANCE_FACTS = [
    ('P01','常规服务累计人次',14825,'人次','2024-06至2025-06合同期','PDF第3页','重复参与者可能多次计入'),
    ('P02','登记志愿者',1073,'名','报告合同期段落，逐项时点未单列','PDF第3页','登记人数，与服务人次口径不同'),
    ('P03','志愿服务活动',1500,'余场','报告合同期段落，逐项时点未单列','PDF第3页','原文余场，下限表述'),
    ('P04','志愿服务累计服务居民',32992,'人次','报告合同期段落，逐项时点未单列','PDF第3页','不可与P01直接相加为独立服务人数'),
    ('P05','文化活动',42,'场','2024','PDF第3页','活动与培训可能存在项目归类重叠'),
    ('P06','群众瑜伽与舞蹈培训',428,'场次','2024','PDF第3页','年度合计，不能仅据此判定每周达标'),
    ('P07','群众满意度目标下界',95,'百分比','报告目标','PDF第4页','原文95%以上，缺少调查方法和样本数'),
    ('P08','群众满意度报告值',94,'百分比','2024','PDF第4页','报告口径，缺少样本数、抽样框与题目'),
    ('P09','项目预算',121.15,'万元','2024财政年度','PDF第4页','猎德人家建设经费项目'),
    ('P10','项目实际支出',121.15,'万元','2024财政年度','PDF第4页','预算执行率不衡量独立覆盖人口或分配公平'),
    ('P11','物业管理费支出',20.23,'万元','2024财政年度','PDF第4页','P10支出分项'),
    ('P12','水电费支出',7.92,'万元','2024财政年度','PDF第4页','P10支出分项'),
    ('P13','委托业务费支出',85,'万元','2024财政年度','PDF第4页','P10支出分项'),
    ('P14','办公费支出',2.9,'万元','2024财政年度','PDF第4页','P10支出分项'),
    ('P15','其他商品和服务支出',5.1,'万元','2024财政年度','PDF第4页','P10支出分项'),
    ('P16','接待参观调研',139,'场次','报告称本年度，需与合同期区分','PDF第5页','与常规居民服务对象区分'),
    ('P17','参观调研人次',3781,'人次','报告称本年度，需与合同期区分','PDF第5页','与常规居民服务对象区分'),
]

POLICIES = [
    ('S05','广州市城中村改造条例','地方性法规','2024-03-30','2024-05-01','人大库标示现行有效','现阶段更新制度背景','S47核验状态，S48全文PDF','2007年补偿合同和方案另行核验'),
    ('S07','农村集体经济组织法','法律','2024-06-28','2025-05-01','已施行，未发现废止信息','集体成员及收益分配制度讨论','成员、财产经营与收益分配相关条款','猎德改制公司的法律形态及直接适用性待核验'),
    ('S08','广州市公共租赁住房管理办法','行政规范性文件','2024-07-26','自印发之日起，版记2024-07-29','文本规定有效期5年','住房保障制度分类','第54条，S09同版PDF','区分类别与申请、续租，不能概括所有来穗人员'),
    ('S10','来穗务工人员公租房期满审查续租方案','专项实施方案','以原件落款为准','方案所定续租批次','面向已有合同及期满审查','来穗务工人员续租制度','适用对象及资格条款','已有承租人的续租范围与新申请资格不同'),
    ('S46','广州市公共租赁住房保障申请审查实施细则','行政规范性文件','2025-02-28','自印发之日起','有效期5年，穗建规字〔2025〕4号','特定保障对象资格审核','适用范围、条件、流程及第32条','该类户籍对象的细则不能概括所有保障住房渠道'),
    ('S26','公共文化服务保障法','法律','2016-12-25','2017-03-01','法律已施行，未发现废止信息','公共文化服务原则与免费或优惠开放','第4、30、31条等','开放原则与个别活动收费规则分别解释'),
    ('S27','广州市文化馆站室服务规范','行政规范性文件','2020-07-17','2020版','官方标题明确已失效','历史开放时长基准','第11条、第29条','街道42小时、社区35小时属于历史基准，2026合规须查现行依据'),
    ('S28','广州市、区文化馆、站（室）服务规范附件','历史附件，版本待核','未核实','未核实','与2020文本的版本关系待核','历史制度检索','PDF标题及条款逐条核验','不得自动与S27视为同一版'),
    ('S29','广州市公共文化设施收费管理办法','行政规范性文件','2025-03-28','自印发之日起','有效期5年，穗发改规字〔2025〕1号','基础免费项目与其他收费项目边界','第6条、第23条及两份附件','免费范围、收费条件及核定标准分别核对'),
    ('S31','广州市关于推动社会力量参与公共文化设施运营的实施办法','行政规范性文件','2024-07-09','2024-07-09','有效期5年','委托运营、合同与绩效治理','全文及第20条','运营主体改变不自动改变基本公共服务责任'),
    ('S32','基本公共文化服务实施标准2023修订','规划期实施标准','2023-04-28','2021—2025规划期','规划期已结束，后续版本未核实','解释历史服务目标','2021—2025年标题及修订正文','不直接推为2026现行考核标准'),
    ('S45','广州市公共文化设施管理办法2019版','行政规范性文件','2019版','原文第32条','原文有效期5年，延续状态未核实','历史开放公示、错时服务、面积原则','第16、17、19、32条','2026年具体效力需另核续期或替代文本'),
]


def build_evidence_tables():
    facts = [dict(fact_id=i, indicator=m, value=v, unit=u, reference_period=t,
                  spatial_or_sample_unit=g, source_id=s, locator=p, limitation=n,
                  evidence_type='published_document')
             for i,m,v,u,t,g,s,p,n in HOUSING_FACTS]
    write_csv('07_住房更新_历史事实与研究数据.csv', facts)
    performance = [dict(fact_id=i, indicator=m, value=v, unit=u, reference_period=t,
                        source_id='S21', locator=p, limitation=n, evidence_type='official_performance_report')
                   for i,m,v,u,t,p,n in PERFORMANCE_FACTS]
    write_csv('08_猎德人家_绩效与财政口径.csv', performance)
    policies = [dict(source_id=s, title=t, legal_form=f, issue_date=d, effective_date=e,
                     status_as_checked=v, analytical_use=a, locator=l, scope_limit=n,
                     checked_date='2026-11-09') for s,t,f,d,e,v,a,l,n in POLICIES]
    write_csv('09_政策适用与版本矩阵.csv', policies)
    comparison = [
        dict(case='猎德村', source_id='S11', locator='PDF第12页，表2及讨论',
             affected_households='超过3000', institutional_label='Bottom-up approach',
             finance='私人开发商，经地方政府', approximate_demolition_months=3,
             evidence_scope='既有研究的案例比较，非本组观察，拆除期定义依作者'),
        dict(case='杨箕村', source_id='S11', locator='PDF第12页，表2及讨论',
             affected_households='约1480', institutional_label='Developer-led approach',
             finance='私人开发商', approximate_demolition_months=37,
             evidence_scope='既有研究的案例比较，非本组观察，拆除期定义依作者'),
        dict(case='林和村', source_id='S11', locator='PDF第12页，表2及讨论',
             affected_households='约700', institutional_label='Partnership approach',
             finance='私人开发商', approximate_demolition_months=3,
             evidence_scope='既有研究的案例比较，非本组观察，拆除期定义依作者'),
    ]
    write_csv('10_住房更新_文献内部三案例比较.csv', comparison)
    assert round(sum(row['value'] for row in performance if row['fact_id'] in ['P11','P12','P13','P14','P15']),2) == 121.15
    return facts, performance, policies


def audit_and_index(summary):
    failures = []
    for row in CATALOG:
        if row['status'] == 'failed':
            failures.append(row['source_id'])
            continue
        path = ROOT / row['local_file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], row['source_id']
        if row.get('text_file'):
            assert (ROOT / row['text_file']).is_file(), row['source_id']
        if row.get('ocr_text_file'):
            assert (ROOT / row['ocr_text_file']).is_file(), row['source_id']
    summary.update(registered_sources=len(CATALOG), acquired_sources=len(CATALOG)-len(failures),
                   failed_sources=failures, archived_bytes=sum(row.get('bytes',0) for row in CATALOG),
                   total_pdf_pages=sum(row.get('page_count',0) for row in CATALOG))
    (DATA / '计算与校验摘要.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    lines = ['# 资料库索引', '', '核对日期为2026-11-09。来源编号贯穿分析文档和CSV。原始文件按来源保存，正文用于检索，引用回到原件。', '',
             f"登记 {len(CATALOG)} 项，已取得 {summary['acquired_sources']} 项，失败 {len(failures)} 项。按网址登记计数，同文不同载体分别计入。", '',
             '| 编号 | 来源与性质 | 本地原件与检索正文 | 下载状态 | 日期与适用提醒 |', '| --- | --- | --- | --- | --- |']
    for row in CATALOG:
        paths = []
        for key,label in [('local_file','原件'),('text_file','正文'),('ocr_text_file','OCR检索稿')]:
            if row.get(key):
                import os
                relative = os.path.relpath(ROOT / row[key], LIBRARY)
                paths.append(f'[{label}](<{relative}>)')
        note = (row.get('document_date','')+' '+row.get('scope_note','')).replace('|','／')
        lines.append(f"| {row['source_id']} | [{row['title']}]({row['url']})<br>{row['kind']} | {' / '.join(paths) or '未取得'} | {row['status']} | {note} |")
    lines += ['', '## 下载失败记录', '']
    for sid in failures:
        row = SOURCES[sid]
        lines += [f"- {sid} {row['title']}。{row.get('error','未记录错误')}。原始链接见上表。"]
    lines += ['', 'S06的条例全文已通过S48取得。S49与S55是同一报告的不同地址，本轮均未取得。S41及S54所指论文全文仍按未取得处理，S57保存了大学机构库书目与摘要。', '',
              '## 可重建处理', '', '`python3 tools/collect_research.py` 按清单下载并校验原件，失败项会再次尝试。', '',
              '`python3 tools/build_research_data.py` 从已存目录和人工核对事实重建CSV、计算摘要及此索引。Python依赖为lxml和pypdf。', '',
              '扫描件OCR使用macOS Vision。示例命令见 `tools/ocr_pdf.swift` 文件开头。OCR文本可能有误识别，使用数据前核对原页。', '']
    (LIBRARY / '资料索引.md').write_text('\n'.join(lines))


def build_fee_tables():
    training = []
    categories = [
        ('体育类', [40, 60, 80]), ('声乐类', [50, 70, 100]),
        ('器乐类', [60, 85, 105]), ('舞蹈类', [40, 60, 80]),
        ('美术类', [40, 60, 75]), ('戏曲戏剧类', [45, 70, 85]),
        ('科学类', [60, 80, 100]), ('综合实践类', [50, 75, 95]),
    ]
    for category, prices in categories:
        for class_size, price in zip(['31人以上', '16至30人', '15人以下'], prices):
            training.append(dict(category=category, class_size=class_size, listed_price=price,
                                 unit='元/小时，按附件原表', source_id='S29-A01',
                                 cross_check='S30 PDF第21页，印刷第19页',
                                 price_kind='政府指导价附件基准，非猎德实际报价'))
    training.append(dict(category='一对一培训', class_size='1人', listed_price=260,
                         unit='元/小时，按附件原表', source_id='S29-A01',
                         cross_check='S30 PDF第21页，印刷第19页',
                         price_kind='政府指导价附件基准，非猎德实际报价'))
    write_csv('11_公共文化收费_培训指导价基准.csv', training)
    activities = [
        ('篮球室外', '散客', 10, '元/人', '室内可按1.2倍'),
        ('篮球室外', '包场', 300, '元/小时', '室内可按1.2倍'),
        ('足球人造草场', '5人场', 350, '元/小时', '天然草场按不超过2.5倍'),
        ('足球人造草场', '7人场', 500, '元/小时', '天然草场按不超过2.5倍'),
        ('足球人造草场', '11人场', 1000, '元/小时', '天然草场按不超过2.5倍'),
        ('羽毛球', '场地', 90, '元/小时', ''),
        ('网球室外', '场地', 100, '元/小时', '室内可按1.2倍'),
        ('游泳非恒温', '个人', 40, '元/人', '恒温可按1.2倍'),
        ('乒乓球', '场地', 40, '元/小时', ''),
        ('滑轮滑板攀岩台球等', '小众活动', 50, '元/人', '原文项目名称保留滑轮表述'),
        ('展示展览文艺表演沉浸式体验等', '临时活动', 100, '元/人', ''),
    ]
    rows = [dict(project=p, specification=s, listed_price=v, unit=u, annex_note=n,
                 source_id='S29-A02', cross_check='S30 PDF第22页，印刷第20页',
                 price_kind='政府指导价附件基准，非猎德实际报价')
            for p,s,v,u,n in activities]
    write_csv('12_公共文化收费_设施与活动指导价基准.csv', rows)


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    facilities, intervals, scenarios = build_service_tables()
    facts, performance, policies = build_evidence_tables()
    build_fee_tables()
    audit_and_index(dict(
        research_date='2026-11-09', current_directory_rows=267, previous_directory_rows=265,
        liede_facility_records=len(facilities), opening_intervals=len(intervals),
        constructed_scenario_rows=len(scenarios), housing_facts=len(facts),
        performance_facts=len(performance), policy_records=len(policies),
        community_weekly_hours=48, community_weekend_hours=3,
        street_weekly_hours=49, street_weekend_hours=14,
        community_weekend_share_pct=6.25, street_weekend_share_pct=round(1400/49,4),
        station_area_2025_sqm=1822, station_area_2026_sqm=1618,
        station_listed_area_delta_sqm=-204,
        expenditure_component_sum_wan=121.15,
        satisfaction_target_lower_bound_pct=95, reported_satisfaction_pct=94,
        satisfaction_difference_percentage_points=-1,
        verification='原件SHA256、样本数量及计算断言通过；现场核验待补',
    ))
    print('Research data and archive index built successfully.')


if __name__ == '__main__':
    main()

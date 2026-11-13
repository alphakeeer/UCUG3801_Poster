"""导出面向组员的中文资料目录、综合工作簿和现用图；不改写专题原件。"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import subprocess
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '交接资料'
SPATIAL = '04_工作区/研究分析/图表与数据补充/ucug3801-housing-education-spatial'
COMPOSITE = '04_工作区/研究分析/图表与数据补充/ucug3801-composite-figures'
OLD = '06_数据整合/outputs/data'
VERSION = '中文交接版-2026-11-13-v1'
GITHUB = 'https://github.com/alphakeeer/UCUG3801_Poster/blob/main/'


def read_csv(path):
    return list(csv.DictReader((ROOT / path).open(encoding='utf-8-sig', newline='')))


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def link(path):
    return GITHUB + quote(str(path), safe='/')


def number(value):
    return float(value) if value not in ('', None) else None


LABEL = {
    'primary': '小学', 'kindergarten': '幼儿园', 'grade_1': '一年级',
    'small_class': '小班', 'public': '公办', 'private': '民办',
    'education_department': '教育部门办', 'other_department': '其他部门办',
    'campus': '园区／校区', 'institution': '机构（不能按校区重复计）',
    'classes': '招生班数', 'intake_places': '招生人数',
    'maximum_channel_places': '渠道名额上限', 'owner_children_places': '业主子女名额（分项）',
    'remaining_random_places': '剩余随机派位名额（分项）',
    'social_lottery_total': '社会派位总数（勿与分项相加）',
    'person': '人', 'class': '班', 'private_points_school_maximum': '民办积分渠道上限',
    'address_linked': '条件性地段对应', 'affiliated_owner_priority': '配套业主优先',
    'campus_specific_admission': '依园校当年公告', 'district_coordination': '区统筹',
    'general_lottery': '一般随机派位', 'hk_macao_ranked': '港澳渠道积分排序',
    'migrant_points': '来穗积分渠道',
    'age_and_tianhe_hukou_or_policy_care': '适龄、天河户籍或政策性照顾',
    'approved_migrant_points_applicant': '获准来穗积分申请人',
    'campus_notice_required': '须查园校公告和家庭材料',
    'matching_full_home_and_hukou': '满足完整人户与住房条件',
    'publicly_cleared_hk_macao_points_applicant': '通过公示的港澳渠道申请人',
    'qualifying_affiliated_owner': '符合条件的配套业主',
    'qualifying_relocation_household': '符合条件的拆迁安置家庭',
    'qualifying_tenant': '符合条件的穗籍租户',
    'affiliated_address_and_documents_unverified': '配套门牌和家庭材料待核',
    'campus_notice_and_household_documents_unverified': '当年公告和家庭材料待核',
    'conditional_address_link_reference': '仅为条件性地段对应',
    'conditional_pathway_reference': '仅为条件性渠道参考',
    'coordination_destination_unknown': '统筹去向未知',
    'listed_option_ranking_preferences_unverified': '名单内选项；积分和志愿未观察',
    'not_address_linked_in_reviewed_catchment_table': '已核地段表未对应此校',
    'not_available_in_published_2026_plan': '该园区2026公布业主名额为0',
    'not_designated_in_reviewed_hk_primary_plan': '未列入已核港澳小学计划',
    'not_in_2026_public_points_plan': '不在2026公办小学积分计划',
    'rank_order_plan_individual_result_unobserved': '按积分排序；个人结果未观察',
    'policy_standard': '政策标准', 'approved_school_standard': '逐校官方批复',
    'collection_status': '收集状态（不是收费标准）', 'conditional_estimate': '有条件推定',
    'conditional_subsidy': '有条件减免／补助', 'historical_quote': '历史报价',
    'historical_third_party': '历史第三方记录', 'known_policy_or_reported_value': '已有政策或报告值',
    'not_collected': '冻结表未收齐公示', 'unknown': '未知', 'unobserved': '未观察',
    'true': '是', 'false': '否', 'not_recorded': '未记录', '/': '原表未注明',
    'comparable': '纳入同平台项目月参考价', 'comparable_price_missing': '缺同口径参考价',
    'other_price_metric': '其他价格口径（不进入色阶）',
    'product_not_comparable': '住房权利／产品口径不可比（不进入色阶）',
    'fang_monthly_community_reference': '房天下项目月参考价',
    'fang_monthly_market_report_average': '房天下月报均值（独立口径）',
    'fang_resale_listing_page_average': '房天下挂牌页面均值（独立口径）',
    'market_reference_sale_cny_m2': '平台出售参考价',
    'platform_listing_page_average_cny_m2': '平台挂牌页面均值',
    'platform_transaction_sale_cny_m2': '平台标示成交价（沿用原核验强度）',
    'policy_rent_cny_m2_month': '政策配租月租标准（元／平方米／月）',
    'rent_cny_m2_month': '租金（元／平方米／月）',
    'rent_cny_month': '整套月租（元／月）', 'sale_ask_cny_m2': '出售挂牌折算单价',
    'cny_per_m2': '元／平方米', 'cny_per_m2_month': '元／平方米／月',
    'cny_per_month': '元／月',
    'external_declared_page_checked': '补证方声明已核页面（沿用原核验强度）',
    'publisher_rechecked': '原整理方已复核平台',
    'reported_repository': '仓库已摘录', 'reported_repository_extract': '仓库摘录记录',
    'archive_metadata': '本地归档登记',
    'repository_file': '仓库文件来源', 'external_verified_facts_csv': '外部补证CSV登记',
    'local_manifest': '本地来源清单', 'source_reference': '来源引用',
    'local_snapshot': '本地快照', 'reported_in_repository_or_import': '仓库或补证引用，按原记录核验',
    'transport_only': '原交通独立样本',
    'published_2026_tuition_or_care_fee': '2026逐园校学费／保教费公示收集项',
    'conditional_care_fee': '有条件推定保教费', 'historical_care_fee': '历史保教费',
    'historical_meal_fee': '历史伙食费',
    'cny_per_person_day': '元／人／天', 'cny_per_person_month': '元／人／月',
    'ordinary_poi_estimate_gate_unverified': '普通地图点位估算，校门未核',
    'legacy_name_address_matched_poi_gate_unverified': '旧名地址暂定匹配，仅作带标识补充',
    'excluded_subchord_distance': '异常排除：规划长度短于端点直距',
    'open': '待补／待核（部分涉及历史方向）',
    'supplemented_requires_review': '已补证，须结合当前版本判断',
    'retired_scope_erratum': '已按范围勘误退役',
    'archive_available_multipart': '分卷原件已有存档',
    'P0': '优先核查', 'P1': '重要缺口', 'P2': '补充背景',
}


def zh(value):
    if not value:
        return None
    return LABEL.get(value, value.replace('CNY', '元'))


def array(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return [value]


ASSETS = []
for stem, title, formats, purpose in [
    ('housing-education-full', '01_住房与园校分布_完整图', ['png', 'pdf', 'svg'], '现用空间主图；替代旧图A'),
    ('housing-education-poster', '02_住房与园校分布_裁切图', ['png', 'pdf', 'svg'], '同一分析的核心视图；供海报负责人选用'),
    ('same-address-admission-scenarios', '03_同址四类家庭招生情境', ['png', 'svg'], '现用南国花园情境图；与三住宅路线图互补'),
    ('kindergarten-walks-and-places', '04_幼儿园步行与招生名额', ['png', 'svg'], '现用补充图；园区计划不能随住宅重复相加'),
    ('housing-price-and-nearby-campuses', '05_参考价与附近候选园校', ['png', 'svg'], '现用描述性比较；不解释家庭收入或因果'),
    ('figure_B_admission_accessibility', '06_三住宅招生渠道与步行比较', ['png', 'pdf', 'svg'], '沿用已审路线图；与同址四类家庭图互补'),
]:
    base = f'{SPATIAL}/maps' if stem.startswith('housing-education') else (
        '06_数据整合/outputs/figures' if stem.startswith('figure_B') else COMPOSITE)
    for ext in formats:
        ASSETS.append({'原文件': f'{base}/{stem}.{ext}', '现用文件': f'交接资料/图表/{title}.{ext}', '用途': purpose})


def domain(path):
    if path.startswith('01_'): return '作业与范围'
    if path.startswith('02_'): return '现场照片与检索线索'
    if '文献' in path or '阅读' in path or '课件' in path: return '文献与课程概念'
    if '图表与数据补充' in path: return '现用空间数据与综合图'
    if '房价分布' in path: return '住房与价格'
    if '交通可达性' in path: return '路线与接送情境'
    if '定向证据补全' in path: return '后续补证与问题记录'
    if '教育专题' in path: return '园校、招生与收费'
    if path.startswith('交接资料'): return '现用交接成品'
    if path.startswith('06_'): return '整合证据与历史基线'
    if '资料库' in path or path.startswith('03_'): return '历史背景与其他选题资料'
    return '研究方案与历史成品'


TITLES = {
    'UCUG3801_course_syllabus_20260814_mz':'课程大纲（8月14日版）',
    'UCUG3801_course_syllabus_202627Fall_0916':'课程大纲（9月16日版）',
    'UCUG3801_fieldposter':'海报作业原始要求', 'Field-Trip-Guiding-Questions':'实地考察指导问题',
    'route-tables':'交通路线逐项表', 'liede-transport-accessibility-2026':'2026交通可达性研究报告',
    'commute-burden-scenarios':'通学负担假设情境', 'household-scenarios':'家庭申请条件情境',
    'primary-migrant-points-plan-2026':'2026来穗积分小学计划',
    'supplementary-route-audit':'补充路线核查', 'threshold-sensitivity':'可达阈值敏感性',
    'evidence':'专题证据记录', 'figure-1-educational-accessibility-map':'教育可达性地图',
    'figure-2-kindergarten-walking-access':'幼儿园步行可达性',
    'figure-3-primary-school-walking-access':'小学步行可达性',
    'figure-4-admission-channels-walking-time':'招生渠道与步行时间',
    'poster-admission-channels-walking-time':'海报用招生渠道与步行时间图',
    'housing-price-and-nearby-campuses-sensitivity':'参考价与近邻园校敏感性',
    'housing-price-and-nearby-campuses':'参考价与附近候选园校',
    'kindergarten-walks-and-places':'幼儿园步行与园区计划',
    'same-address-admission-scenarios':'同址四类家庭招生情境',
    'supplementary-figure-notes':'补充综合图说明', 'amap_poi_checks':'高德项目与园校位置核对',
    'campus_proximity':'不同直线半径的候选园校计数', 'campuses':'现用园校空间基表',
    'housing_price_observations':'现用住房价格观察', 'housing_projects':'现用住宅项目基表',
    'map_layers':'地图各图层对象清单', 'map_scope':'制图范围参数',
    'osm_basemap_2026-11-12.json':'2026年11月12日OSM底图存档',
    'price_proximity_summary':'价格分组与附近园校汇总', 'price_rechecks':'价格逐项复核',
    'prior_coordinate_crosswalk':'旧新参考点对应与差异', 'proximity_pairs_within_800m':'800米内住宅园校直线距离',
    'housing-education-full':'住房与园校完整空间图（现用）',
    'housing-education-poster':'住房与园校裁切空间图（现用）',
    'spatial-findings-report':'新增空间研究报告', 'liede-research-poster-v2':'前期公共文化海报第二版',
    'liede-research-poster':'前期海报第一版', 'FIGURE_LEGENDS':'上一轮图注',
    'FINAL_EVIDENCE_BRIEF':'上一轮核心证据简报（空间覆盖已更新）',
    'HANDOFF':'上一轮交接说明', 'QUALITY_SUMMARY':'上一轮数据质量摘要', 'REVIEW_RESPONSE':'独立审查问题处置',
    'accessibility_comparisons':'渠道与路线比较', 'admission_channel_contexts':'住宅园校渠道适用背景',
    'admission_conditions':'家庭申请细分条件', 'admission_evidence':'新增招生证据',
    'admission_plans':'逐校区或机构招生计划', 'admission_rules':'招生一般规则',
    'campus_admission_rules':'园校与规则参考对应', 'capacity_notices':'容量预警与目标年份',
    'district_primary_points_plan':'全区小学积分计划', 'education_campuses':'上一轮园校规范表',
    'education_fees':'收费与减免证据', 'entity_crosswalk':'对象匹配与原编号对照',
    'escort_scenarios':'接送假设情境', 'evidence_matrix':'跨专题证据矩阵',
    'fee_applicability':'费用适用背景（不能判定负担）', 'household_scenarios':'家庭渠道假设情境',
    'housing_education_links':'路线与参考证据联表', 'housing_observations':'上一轮住房观察',
    'import_quarantine':'导入隔离与未通过记录', 'institutions':'机构参考登记',
    'plan_corroboration':'招生计划旁证', 'positions':'上一轮位置与角色登记',
    'research_gaps':'历史累计研究缺口', 'residence_cost_summary':'住宅成本口径摘要',
    'residences':'上一轮18住宅规范表', 'source_registry':'来源登记表',
    'transport_routes':'42条原始路线规范表', 'verified_facts':'后续事实规范导入记录',
    'walking_sensitivity':'原六园步速敏感性', 'work_evidence':'45条定向补证整合',
    'figure_qa':'图件质量核对', 'figure_A_campuses':'旧图A园校来源',
    'figure_A_housing':'旧图A住宅来源', 'figure_A_unresolved':'旧图A未决点位',
    'figure_B_comparisons':'三住宅路线图比较源表', 'figure_B_housing_context':'路线图住房背景参考',
    'figure_B_secondary_channels':'路线图补充渠道',
    'figure_A_housing_education':'旧图A（已替代）', 'figure_B_admission_accessibility':'三住宅渠道路线图（继续使用）',
    'quality_report':'自动质量核查记录', 'run_manifest':'历史数据版本与文件登记',
    'schemas':'历史规范表字段结构', 'table_C_evidence_matrix':'跨专题证据矩阵可读版',
    'manifest':'文件与分卷清单', 'atlas.pdf':'官方地图图集',
}


def inventory(sources):
    bypath = {s['local_file']: s for s in sources if s['local_file']}
    byid = {s['id']:s for s in sources}
    for file in ('03_背景/资料库/来源清单.json','03_背景/资料库/补充选题资料/补充来源清单.json','03_背景/教育专题/来源清单.json'):
        for s in json.loads((ROOT/file).read_text()):
            byid.setdefault(s['source_id'],dict(s,id=s['source_id']))
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    rows = []
    for path in sorted(set(paths)):
        if not path or not (ROOT / path).is_file(): continue
        if path in ('README.md', '研究资料总览.md'): continue
        if path.startswith(('交接资料/', '06_数据整合/maintenance/')): continue
        if not path.startswith(('01_', '02_', '03_', '04_工作区/研究分析/', '05_', '06_数据整合/outputs/')): continue
        if any(x in path for x in ('/node_modules/', '/.state/', '/.venv/')): continue
        suffix = Path(path).suffix.lower()
        if suffix not in {'.md','.pdf','.doc','.docx','.xls','.xlsx','.csv','.png','.jpg','.jpeg','.svg','.html','.txt','.json','.jsonl','.gz','.001','.002','.003'}: continue
        source_code = re.match(r'^([EST]\d+(?:-A\d+)?)',Path(path).stem)
        s = bypath.get(path) or byid.get(source_code.group(1) if source_code else '', {})
        title = s.get('title') or TITLES.get(Path(path).stem) or Path(path).stem
        if Path(path).stem == 'README': title = Path(path).parent.name+'：阅读说明'
        if source_code: title = source_code.group(1)+'｜'+title
        group = domain(path)
        status = '专题原件／核查材料'
        if '图表与数据补充' in path: status = '现用空间来源／图包原件'
        elif path.startswith('06_'): status = '已审历史基线；现用空间统计见中文工作簿'
        elif any(x in path for x in ['双方向', '方向一', '方向二', '海报v2', 'poster_final', '公共文化', '补充选题']): status = '历史方向，保留参考'
        elif path.startswith('04_'): status = '组员专题材料；沿用原作者版本'
        if any(x in path for x in ['初中', '中学', '小升初']): status += '；含初中内容，仅取小学／幼儿园相关部分'
        if suffix == '.txt': status += '；文字提取件，与对应原件不算独立证据'
        kind = {'.md':'可读说明／分析', '.pdf':'PDF原件／成图', '.csv':'数据表', '.xlsx':'Excel表格', '.xls':'Excel原表', '.docx':'Word材料', '.doc':'Word材料', '.png':'图片', '.jpg':'现场图片', '.jpeg':'图片', '.svg':'可编辑图', '.html':'网页存档', '.txt':'提取文字', '.json':'结构化原始／查询记录', '.jsonl':'结构化原始记录', '.gz':'压缩原始数据'}.get(suffix,'分卷文件')
        count = None
        if suffix == '.csv':
            try: count = len(read_csv(path))
            except (UnicodeError, csv.Error): pass
        description = s.get('scope_note') or {
            '作业与范围': '作业原要求、课程安排及勘误；当前研究只含小学和幼儿园',
            '现场照片与检索线索': '现场视觉材料或地图检索线索；不等同家庭访谈或实走记录',
            '文献与课程概念': '供理论组独立判断概念、方法与解释；文献案例不是本组实测',
            '住房与价格': '住宅、参考价、租售个案及质量说明；须保留时间和价格口径',
            '路线与接送情境': '高德路线、出行假设与招生渠道案例；不是实际通学观察',
            '园校、招生与收费': '名录、制度条款、计划、收费及原件；总项分项不可重复计数',
            '后续补证与问题记录': '定向补证事实、证据链接和未解决问题；核验强度按原记录',
            '现用空间数据与综合图': '22住宅、43园校及价格／定位复核；新图包原件保持不变',
            '整合证据与历史基线': '上一轮已审联表、证据链与质量记录；旧定位覆盖已被新图替代',
            '历史背景与其他选题资料': '城市更新、产权、文化服务等背景；不自动转为当前教育结论',
            '研究方案与历史成品': '既有研究方案或历史交付；不修改组员撰写内容',
        }[group]
        rows.append([group, title, kind, status, description, count,
                     s.get('document_date') or s.get('publication_date') or '原件／条目中查阅',
                     s.get('url') or None, link(path), path, s.get('id') or None])
    # 交接入口与图排在前面，组员首先看到当前可用成品。
    front = [['现用交接成品','图文交接手册','图文说明','优先阅读','直接展示已有材料、综合发现和使用边界',None,'2026-11-13',None,link('README.md'),'README.md',None],
             ['现用交接成品','中文综合工作簿','Excel表格','优先使用','按住宅、园校及主题筛选；来源与待核问题随行保留',None,'2026-11-13',None,link('交接资料/研究资料与综合数据.xlsx'),'交接资料/研究资料与综合数据.xlsx',None]]
    for a in ASSETS:
        front.append(['现用交接成品',Path(a['现用文件']).stem,Path(a['现用文件']).suffix[1:].upper(),a['用途'],'原图逐字节复制；中英文原图保持原貌',None,'2026-11-13',None,link(a['现用文件']),a['现用文件'],None])
    # 交互地图作为整体列出，避免大量网页程序淹没资料清单。
    front.append(['园校、招生与收费','前期交互教育地图（整体入口）','交互地图','前期版本，含初中；未同步本次新图数据','可查看历史地图展示，不作为本次现用统计来源',None,'见原说明',None,link('04_工作区/教育地图/README.md'),'04_工作区/教育地图/README.md',None])
    return front + rows


def make_workbook():
    OUT.mkdir(exist_ok=True)
    sources = read_csv(f'{OLD}/source_registry.csv')
    source_by_id = {s['id']: s for s in sources}
    homes = read_csv(f'{SPATIAL}/data/housing_projects.csv')
    campuses = read_csv(f'{SPATIAL}/data/campuses.csv')
    hnames = {r['residence_id']: r['name'] for r in homes}
    cnames = {r['campus_id']: r['name'] for r in campuses}
    institutions = {}
    for c in campuses: institutions.setdefault(c['institution_id'], []).append(c['name'])
    hname = lambda key: hnames.get(key, key or '未指定住宅')
    cname = lambda key: cnames.get(key, key or '非单一园校／目的地未知')

    def refs(ids):
        return '\n'.join(source_by_id[k]['title'] for k in array(ids) if k in source_by_id)

    def urls(ids):
        return '\n'.join(dict.fromkeys(source_by_id[k]['url'] for k in array(ids) if k in source_by_id and source_by_id[k]['url']))

    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.creator = 'UCUG3801研究资料整理'
    wb.properties.title = '猎德教育研究：资料清单与综合数据'
    wb.properties.created = wb.properties.modified = datetime(2026, 11, 13)
    sheet_rows = {}

    def sheet(name, note, headers, rows):
        ws = wb.create_sheet(name)
        ws.append([name + '｜' + VERSION])
        ws.append([note])
        for row in (1, 2): ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(headers))
        ws.row_dimensions[1].height = 29
        ws.row_dimensions[2].height = 52
        ws.cell(1,1).font = Font(name='微软雅黑', size=16, bold=True, color='16324F')
        ws.cell(2,1).alignment = Alignment(wrap_text=True, vertical='center')
        ws.append(headers)
        for row in rows:
            ws.append(row)
        ws.freeze_panes = 'C4'
        ws.sheet_view.showGridLines = False
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.orientation = 'landscape'
        ws.page_setup.paperSize = ws.PAPERSIZE_A3
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.print_title_rows = '1:3'
        ws.print_options.horizontalCentered = True
        tab = Table(displayName=f'Data{len(wb.worksheets)}', ref=f'A3:{ws.cell(ws.max_row,len(headers)).coordinate}')
        tab.tableStyleInfo = TableStyleInfo(name='TableStyleMedium2', showRowStripes=True)
        ws.add_table(tab)
        for c in ws[3]: c.font = Font(name='微软雅黑',bold=True,color='FFFFFF'); c.fill = PatternFill('solid',fgColor='245477')
        for j, header in enumerate(headers, 1):
            width = 26
            if any(x in header for x in ('说明','边界','条件','限制','发现','待核','内容','名称','依据','备注')): width = 46
            if any(x in header for x in ('链接','出处','来源')): width = 42
            if any(x in header for x in ('数值','人数','秒','分钟','米）','年份','金额','半径','班数','记录数')): width = 18
            if '编号' in header: width = 27
            ws.column_dimensions[ws.cell(3,j).column_letter].width = width
        for row in ws.iter_rows(min_row=4):
            for c in row:
                c.font = Font(name='微软雅黑',size=10)
                c.alignment = Alignment(vertical='top',wrap_text=True)
                if isinstance(c.value, str):
                    # 原始文本作为文本保存，防止其被Excel当作公式。
                    c.data_type = 's'
                    if c.value.startswith(('https://','http://')) and '\n' not in c.value:
                        c.hyperlink = c.value
                        c.font = Font(name='微软雅黑',size=10,color='0563C1',underline='single')
                elif isinstance(c.value,(int,float)):
                    c.number_format = '0.000000' if any(x in headers[c.column-1] for x in ('经度','纬度')) else '#,##0.########'
            ws.row_dimensions[row[0].row].height = 62 if name == '资料清单' else 76
        sheet_rows[name] = len(rows)
        return ws

    inv = inventory(sources)
    sheet('资料清单','先按“资料领域”或“使用状态”筛选，再点“文件链接”。清单逐项呈现现用资料、原件和历史材料；同文PDF/网页/提取文字不是三份独立证据。',
          ['资料领域','资料名称','资料形式','使用状态','内容与用途','表内记录数','来源年份／日期','原网站链接','文件链接','仓库位置','来源编号'],inv)
    notes = [
        ['研究范围','猎德及周边的小学一年级与幼儿园小班为主；不纳入初中，不要求两个社区。大班收费减免单列。'],
        ['先看什么','资料清单展示所有已有材料；住宅综合和园校综合回答有什么对象；同址案例、招生规则、收费证据和步行路线用于跨专题分析。'],
        ['当前数量','22个目的性住宅项目、43条候选园校（13小学、30幼儿园）、66条住房观察；地图全部有参照点，不代表已核校门或完整区域名录。'],
        ['版本怎样衔接','住宅／位置／价格用新图包；招生／收费／42路线用审查后基线。原18住宅和43园校编号逐项核对一致；新4住宅没有补造路线或家庭材料。'],
        ['怎样引用','记录对象、年份、指标与原网站条款；资料清单提供原件，来源登记提供证据出处。正文结论同时带解释边界。'],
        ['空白与零','空白是未知或未收集。只有原证据明确的零才显示0，例如金穗本园业主计划。公办免学费不代表家庭教育总支出为零。'],
        ['价格口径','参考价、挂牌均值、个案售价、租金、人才配租分开；16个项目月参考价可作有限描述，月份混合，不代表收入或成交。'],
        ['距离口径','附近园校为WGS84转UTM49N后的直线POI距离；路线表为高德步行POI估算。两者不互换，门对门及接送时段未核。'],
        ['资格与结果','招生规则是一般参考，渠道条件是待核情境；没有家庭申请、录取和实缴数据，不能统计可申请／可负担园校或录取概率。'],
        ['计划计数','机构和校区分开；天河第一小学7班只计机构一次。社会派位总数与业主／剩余分项不相加，路线重复引用园区计划不增加学位。'],
        ['异常路线','D3到K7原18米短于端点直距约51.6米，保留原记录但排除分析；新定位不能使异常路线变有效。D1/D2到K7仅带标识补充。'],
        ['没有观察到什么','家庭收入／预算、真实申请录取、核心幼儿园新小班实缴、完整配套门牌、真实接送；不能推断住房性质的因果效应。'],
        ['技术维护','普通组员无需安装软件或运行Python。脚本只是把现有资料导出成此工作簿；维护入口见06_数据整合/maintenance/维护说明.md。'],
    ]
    sheet('使用说明','可直接阅读的口径说明；所有工作表首行都保留相应边界。',['项目','说明'],notes)

    proximity = read_csv(f'{SPATIAL}/data/campus_proximity.csv')
    near500 = {r['residence_id']:r for r in proximity if float(r['radius_m']) == 500}
    rows = []
    for h in homes:
        p = near500[h['residence_id']]
        rows.append([h['name'],h['adjudicated_address'],h['housing_type'],zh(h['research_group']),
                     number(h['map_price_cny_m2']),h['price_period'],zh(h['map_price_status']),
                     zh(h['price_metric']),number(h['observed_price_cny_m2']),
                     number(p['total']),number(p['primary_public']),number(p['primary_private']),
                     number(p['kg_education_department']),number(p['kg_other_department']),number(p['kg_private']),
                     '已有路线／渠道情境' if h['residence_id'] in ('RES001','RES005','RES018') else '无本项目已测路线，不能按附近园校补值',
                     number(h['longitude_wgs84']),number(h['latitude_wgs84']),h['match_note'],
                     h['price_source_url'],h['price_recheck_url'],h['coordinate_source_url'],h['residence_id']])
    # 三个路线住宅按原表自动确认，避免依靠人记编号。
    route_home_ids = {r['residence_id'] for r in read_csv(f'{OLD}/transport_routes.csv')}
    for r,h in zip(rows,homes): r[15] = '已有路线／渠道情境' if h['residence_id'] in route_home_ids else '无本项目已测路线，不能按附近园校补值'
    sheet('住宅综合','每行一个住宅项目。附近计数限候选清单内500米直线范围，不是可申请数；项目月参考价空白不等于0，其他口径单列。',
          ['住宅名称','项目地址','住房性质原描述','原调查分组','图用参考价（元／平方米）','价格参考月份','价格使用状态','原指标口径','原指标数值（元／平方米）','500米候选总数','500米公办小学','500米民办小学','500米教育部门园','500米其他部门园','500米民办园','路线与情境资料','经度（WGS84）','纬度（WGS84）','匹配依据与注意事项','价格来源','价格复核来源','位置来源','住宅编号'],rows)
    sheet('园校综合','每行一个物理园区／校区。全部有制图参照，不代表校门实地核验；机构计划与园区计划分别在招生计划表。',
          ['园校名称','学段','办学类别','官方地址','普惠性记录','名录年份','地图参照名称','地图参照地址','经度（WGS84）','纬度（WGS84）','点位匹配依据','官方来源','位置来源','园校编号','机构参考编号'],
          [[c['name'],zh(c['stage']),zh(c['organizer_type']),c['official_address'],zh(c['inclusive_status']),c['listing_year'],c['map_name'],c['map_address'],number(c['longitude_wgs84']),number(c['latitude_wgs84']),c['match_note'],c['official_url'],c['coordinate_source_url'],c['campus_id'],c['institution_id']] for c in campuses])
    observations = read_csv(f'{SPATIAL}/data/housing_price_observations.csv')
    sheet('住房观察','66条是观察记录，不是66个项目；同项目不同日期和指标分别保留。珠江都荟原指标改为挂牌页面均值，原口径保留在最后一列。',
          ['住宅名称','价格／租赁指标','数值','单位','参考时期','观察日期','面积（平方米）','个案总挂牌价（元）','原核验状态','备注与限制','来源链接','本地原件','原表定位','观察编号','住宅编号','更正前指标'],
          [[hname(r['residence_id']),zh(r['metric']),number(r['value']),zh(r['unit']),r['reference_period'],r['observed_on'],number(r['area_m2']),number(r['total_ask_cny']),zh(r['verification_status']),r['note'],r['source_url'] or source_by_id.get(r['source_id'],{}).get('url'),r['source_path'],r['source_locator'],r['id'],r['residence_id'],zh(r['previous_metric'])] for r in observations])
    conditions = read_csv(f'{OLD}/admission_conditions.csv')
    rules = read_csv(f'{OLD}/admission_rules.csv')
    sheet('招生规则','一般规则仅供参考，不能据此判定具体家庭合格。条件还取决于当年门牌、户籍、产权、备案及证明材料。',
          ['学段','入学年级','政策年份','申请资格原文摘要','招生渠道','细分家庭条件','解释边界','来源名称','来源链接','原文定位','规则编号'],
          [[zh(r['stage']),zh(r['intake_grade']),r['policy_year'],r['eligibility_text'],r['pathway'],'\n'.join(zh(c['household_category'])+'：'+c['conditions'] for c in conditions if c['rule_id']==r['id']),r['interpretation_boundary'],refs(r['source_ids']),urls(r['source_ids']),r['source_locator'],r['id']] for r in rules])
    plans = read_csv(f'{OLD}/admission_plans.csv')
    sheet('招生计划','总项和子项不能相加；人和班不互换；机构与校区分别计。天河第一小学7班是两校区机构总计划，只出现一次。',
          ['计划对应对象','统计层级','学段','入学年级','政策年份','计划指标','数量','单位','计划类别','备注与限制','来源名称','来源链接','原表定位','计划编号','对象编号'],
          [[cname(r['subject_id']) if r['subject_type']=='campus' else '／'.join(institutions.get(r['subject_id'],[r['subject_id']])),zh(r['subject_type']),zh(r['stage']),zh(r['intake_grade']),r['policy_year'],zh(r['metric']),number(r['value']),zh(r['unit']),zh(r['plan_category']),r['note'],refs(r['source_id']),urls(r['source_id']),r['source_locator'],r['id'],r['subject_id']] for r in plans])
    contexts = read_csv(f'{OLD}/admission_channel_contexts.csv')
    sheet('渠道条件','这是住宅×园校×渠道的核查背景，不是家庭样本或资格判决。未核材料不填“合格”；统筹目的地未知时不强行挂学校。',
          ['住宅名称','园校／目的地','学段','政策年份','招生渠道','家庭类别','适用情况','必要条件／待核事项','当年园区业主名额（人）','个体资格','实际录取','可据此统计合格园校','来源名称','来源链接','住宅编号','园校编号','路线编号','情境编号'],
          [[hname(r['residence_id']),cname(r['campus_id']),zh(r['stage']),r['policy_year'],zh(r['channel']),zh(r['household_category']),zh(r['applicability_status']),r['requirements'],number(r['published_owner_children_places']),'未核','未观察','否',refs(r['source_ids']),urls(r['source_ids']),r['residence_id'],r['campus_id'],r['route_id'],r['id']] for r in contexts])
    scenarios = read_csv(f'{COMPOSITE}/same-address-admission-scenarios.csv')
    scenario_labels = ['满足地段条件的业主','满足备案等条件的穗籍私房租户','获准来穗积分申请人','通过港澳单列渠道审核的申请人']
    scenario_requirements = ['天河户籍、合格产权、实际居住、学位未占用等完整条件','穗籍、全市无房、唯一住址、合格租赁备案等条件','积分申请通过审核及公示；志愿、排序、录取仍未观察','符合单列规则并通过公示；按积分排名安排南国小学部，直至45名额用完']
    sheet('同址案例','四行是假设情境，不是四户受访家庭。都以南国花园为起点；租户去向未知。2.8与28.4分钟是两个指定POI的路线估算。',
          ['住宅名称','家庭情境','资格条件摘要','学校／目的地','目的地性质','步行原始秒数','单程步行分钟','收费证据','实际录取','家庭实缴','政策出处','条款定位','积分计划原附件','路线编号'],
          [[hname(r['residence_id']),scenario_labels[i],scenario_requirements[i],r['destination'] or '未知',r['destination_status'],number(r['raw_walk_seconds']),number(r['estimated_one_way_walk_min']),r['fee_evidence'],'未观察','未观察',r['policy_url'],r['policy_locator'],r['official_attachment_url'],r['route_id']] for i,r in enumerate(scenarios)])
    fees = read_csv(f'{OLD}/education_fees.csv')
    sheet('收费证据','政策标准、逐校批复、历史、推定、减免条件和收集状态分开。43条“未收齐”是原冻结表状态，不表示没有任何其他费用证据；未观察家庭净支出。',
          ['园校／适用对象','学段','费用项目','证据层级','金额','单位','数值状态','适用时期','证据年份','适用条件','说明与限制','家庭净支出','能否据此判定可负担','来源名称','来源链接','原文定位','费用编号'],
          [[cname(r['campus_id']) if r['campus_id'] else r['target_raw'],zh(r['stage']),zh(r['metric']),zh(r['evidence_layer']),number(r['value']),zh(r['unit']),zh(r['value_status']),r['reference_period'],r['evidence_year'],r['applicability'],r['note'],None,'否',refs(r['source_ids']),urls(r['source_ids']),r['source_locator'],r['id']] for r in fees])
    routes = read_csv(f'{OLD}/transport_routes.csv')
    route_by_id = {r['id']:r for r in routes}
    comparisons = read_csv(f'{OLD}/accessibility_comparisons.csv')
    channel_labels = {'address_linked_conditional':'条件性地段学校', 'migrant_points_listed_example':'来穗积分名单内志愿例', 'hk_macao_ranked':'港澳单列积分排序', 'hk_macao_listed_channel':'港澳单列积分排序'}
    sheet('小学路线比较','9个渠道情境引用8条独立路线；南国花园两个渠道目的地重合。差值由原始秒数计算，不能用已舍入的分钟倒算。不是实际录取／最近可申请校。',
          ['住宅名称','目的小学','渠道情境','单程原始秒数','单程分钟','地段基准原始秒数','比基准多几分钟','个人资格','实际录取','解释边界','来源链接','路线编号'],
          [[hname(r['residence_id']),cname(r['campus_id']),channel_labels.get(r['channel'],zh(r['channel'])),number(route_by_id[r['route_id']]['duration_s']),round(float(route_by_id[r['route_id']]['duration_s'])/60,1),number(route_by_id[r['baseline_route_id']]['duration_s']),round((float(route_by_id[r['route_id']]['duration_s'])-float(route_by_id[r['baseline_route_id']]['duration_s']))/60,1),'未核；仅条件性渠道','未观察',r['interpretation_boundary'],urls(r['source_ids']),r['route_id']] for r in comparisons])
    sheet('步行路线','42条原记录完整保留：39条普通估算、2条旧名暂定补充、1条异常排除；全部不是实走。新增地图POI不替换旧路线起终点。',
          ['住宅名称','目的园校','规划日期','步行距离（米）','步行原始秒数','单程分钟','端点直距（米）','质量与用途','可进入带标签分析','排除理由','校门实核','实际通学','路线来源链接','原始资料文件','原起点编号','原终点编号','路线编号','住宅编号','园校编号'],
          [[hname(r['residence_id']),cname(r['campus_id'] or r['candidate_campus_id']),r['route_date'],number(r['distance_m']),number(r['duration_s']),round(float(r['duration_s'])/60,1),number(r['endpoint_chord_m']),zh(r['review_quality']),zh(r['analytical_eligible']),r['exclusion_reason'],'未核','未观察',r['route_url'],r['source_path'],r['origin_position_id'],r['destination_position_id'],r['id'],r['residence_id'],r['campus_id'] or r['candidate_campus_id']] for r in routes])
    sheet('附近园校','22项目×300／500／800米=66行；计数限已定位43候选。这里是直线邻近，不是步行时间、学位容量、学校质量或合格学校数。',
          ['住宅名称','直线半径（米）','图用参考价（元／平方米）','价格月份','公办小学数','民办小学数','教育部门园数','其他部门园数','民办园数','候选园校总数','最近候选小学直距（米）','最近候选幼儿园直距（米）','住宅编号'],
          [[hname(r['residence_id']),number(r['radius_m']),number(r['price_cny_m2']),r['price_period'],*[number(r[c]) for c in ('primary_public','primary_private','kg_education_department','kg_other_department','kg_private','total','nearest_primary_m','nearest_kg_m')],r['residence_id']] for r in proximity])
    pairs = read_csv(f'{SPATIAL}/data/proximity_pairs_within_800m.csv')
    sheet('直线距离','仅列800米内住宅—候选园校配对。使用项目／校园POI，坐标WGS84转UTM49N；不能据此认定校门、步行或申请资格。',
          ['住宅名称','园校名称','学段','办学类别','直线距离（米）','住宅编号','园校编号'],
          [[hname(r['residence_id']),cname(r['campus_id']),zh(r['stage']),zh(r['organizer_type']),number(r['distance_m']),r['residence_id'],r['campus_id']] for r in pairs])
    evidence = read_csv(f'{OLD}/evidence_matrix.csv')
    evidence_rows = []
    for r in evidence:
        status = '沿用已审发现，须保留原解释边界'
        if r['id']=='F01': status = '旧覆盖统计已替代：现用43/43园校、22/22住宅有制图参照'
        if r['id']=='F02': status = '沿用口径原则；现用空间表已更正珠江都荟指标'
        if r['id']=='F10': status = '仅历史挂牌租赁个案；现另有南国9月项目月参考价90272元／平方米'
        evidence_rows.append([r['id'],status,r['finding'],r['interpretation_boundary'],r['limitation'],refs(r['source_ids']),urls(r['source_ids']),r['supporting_data']])
    for eid,finding,limit,data in [
        ('S01','现用地图22住宅、43园校；完整图与裁切图范围分别标明','目的性住宅样本和候选园校，不代表全区普查；地图点不是实核校门','住宅综合；园校综合'),
        ('S02','16个同平台项目月参考价；价格分组的附近园校计数对月份和半径敏感','混合2026年8—11月；直线邻近；不能用价格代替收入或推断资本化因果','住宅综合；附近园校'),
        ('S03','同址的业主、租户、来穗积分与港澳渠道有不同条件和目的地情境','统筹去向、积分志愿、个人资格和实际录取未观察；示例不是分配','同址案例；渠道条件；步行路线'),
    ]: evidence_rows.append([eid,'现用图包整合发现',finding,limit,limit,'新增图包原报告与逐项来源',link(f'{SPATIAL}/spatial-findings-report.md'),data])
    sheet('证据索引','既呈现可用发现，也保留旧结论的版本状态。F01为旧定位覆盖，不能在现用地图上引用；原证据矩阵并未被覆盖。',
          ['发现编号','现用状态','研究发现／原记录','解释边界','研究局限','支持来源名称','支持来源链接','支持数据定位'],evidence_rows)
    gaps = read_csv(f'{OLD}/research_gaps.csv')
    sheet('研究缺口','102条为历史累计登记，不能当成102项仍未解决。已退役／已补证分别保留状态；旧定位缺口须结合本次完整地图判断。',
          ['优先级','登记状态','对象','原问题','需要什么证据','现用版本说明','来源名称','来源链接','缺口编号'],
          [[zh(r['priority']),zh(r['status']),hnames.get(r['subject_id'],cnames.get(r['subject_id'],r['subject_id'])),r['finding'],r['needed_evidence'],'坐标／覆盖类请先看现用园校综合与住宅综合；家庭资格、净费、真实接送仍未观察',refs(r['source_ids']),urls(r['source_ids']),r['id']] for r in gaps])
    new_source_rows = []
    existing_urls = {s['url'] for s in sources if s['url']}
    collected = {}
    for r in homes + campuses + observations:
        for key,val in r.items():
            if 'url' in key and val.startswith(('http://','https://')) and val not in existing_urls:
                collected.setdefault(val, r.get('name') or hnames.get(r.get('residence_id')) or '图包引用来源')
    for i,(url,title) in enumerate(sorted(collected.items()),1):
        new_source_rows.append([title,url,'见原表参考时期','2026-11-13图包整合','新图包引入；核验依据沿用原包，未重新网页检索',None,'新增空间包；参照价格复核和匹配备注',f'SPATIAL-SOURCE-{i:03d}'])
    sheet('来源登记','267条旧登记保留，加列新图包独有URL。不同文件／网页载体不等于独立证据；来源覆盖多学段时，研究仅提取小学和幼儿园。',
          ['来源名称','原网站链接','文献／政策日期','整理获取日期','来源状态','本地文件','备注','来源编号'],
          [[s['title'],s['url'],s['document_date'] or s['publication_date'],s['retrieved_at'],zh(s['provenance_status']),s['local_file'],s['note'],s['id']] for s in sources] + new_source_rows)
    versions = [[Path(a['现用文件']).name,a['用途'],a['现用文件'],a['原文件'],'原始字节复制，原图中的英文保留'] for a in ASSETS]
    versions += [
        ['旧图A（住房与园校分布）','已替代，仅历史核查','不再列为现用图','06_数据整合/outputs/figures/figure_A_housing_education.png','旧覆盖5/18住宅与26/43园校，不能与现用43/43混用'],
        ['上一轮最终核心证据简报','制度与路线发现继续使用；旧定位段落已过时','现用内容见仓库首页','06_数据整合/outputs/FINAL_EVIDENCE_BRIEF.md','原18住宅基线保留；本工作簿整合新22住宅与66观察'],
        ['原六园步速敏感性','继续保留的补充分析','06_数据整合/outputs/data/walking_sensitivity.csv','06_数据整合/outputs/data/walking_sensitivity.csv','原六园固定样本，不能用新43位置点重写分母'],
    ]
    sheet('图表与版本','新完整空间图正式替代旧图A。其余图按问题互补；没有修改任何成员的Poster或报告。PNG直接使用，PDF适合打印，SVG供编辑。',
          ['材料名称','现用关系／用途','现用文件','原件／历史文件','版本与使用注意'],versions)
    for a in ASSETS:
        target = ROOT / a['现用文件']
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/a['原文件'],target)

    workbook = OUT / '研究资料与综合数据.xlsx'
    wb.save(workbook)
    # 固定ZIP元数据，让相同输入可生成相同工作簿字节。
    raw = io.BytesIO(workbook.read_bytes())
    with zipfile.ZipFile(raw) as src, zipfile.ZipFile(workbook,'w',zipfile.ZIP_DEFLATED) as dst:
        for name in src.namelist():
            info = zipfile.ZipInfo(name, (2026,11,13,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            content = src.read(name)
            if name == 'docProps/core.xml':
                # openpyxl保存时会重设修改时间，同时固定文档内部时间。
                content = re.sub(rb'(<dcterms:modified[^>]*>)[^<]+(</dcterms:modified>)',
                                 lambda m:m[1]+b'2026-11-13T00:00:00Z'+m[2],content)
            dst.writestr(info,content)

    # 可读的完整文件目录，另页承载，避免仓库首页淹没在路径里。
    groups = {}
    for r in inv: groups.setdefault(r[0], []).append(r)
    lines = ['# 已有资料逐项目录','',
             '这页展示可交接材料的全貌。按研究问题阅读请回到[图文手册](../README.md)；筛选、排序与跨专题分析请下载[中文工作簿](研究资料与综合数据.xlsx)。',
             '', '目录基于已纳入Git的材料，不包括他人尚未提交的草稿。表内记录数不是独立样本量；同一内容的原件、网页和提取件分别列出以便追溯。', '']
    for group, items in groups.items():
        lines += [f'## {group}（{len(items)}项载体）','', '|资料|形式|使用状态|', '|---|---|---|']
        for r in items:
            title = r[1].replace('|','／').replace('\n',' ')
            lines.append(f'|[{title}]({r[8]})|{r[2]}|{r[3]}|')
        lines.append('')
    (OUT/'资料目录.md').write_text('\n'.join(lines),encoding='utf-8')
    checks = validate(workbook, homes, campuses, observations, plans, routes, contexts)
    inputs = [f'{SPATIAL}/data/{x}.csv' for x in ('housing_projects','campuses','housing_price_observations','campus_proximity','proximity_pairs_within_800m')]
    inputs += [f'{OLD}/{x}.csv' for x in ('source_registry','admission_rules','admission_conditions','admission_plans','admission_channel_contexts','education_fees','transport_routes','evidence_matrix','research_gaps')]
    inputs += [f'{COMPOSITE}/same-address-admission-scenarios.csv']
    inputs += ['03_背景/资料库/来源清单.json','03_背景/资料库/补充选题资料/补充来源清单.json','03_背景/教育专题/来源清单.json']
    manifest = {'交接版本':VERSION,'说明':'空间用新图包，政策、费用、路线用已审基线；不回写专题原件',
                '导出程序sha256':digest('06_数据整合/maintenance/build_handoff.py'),
                '工作表记录数':sheet_rows,'资料领域载体数':{g:len(v) for g,v in groups.items()},
                '输入':{p:digest(p) for p in inputs},
                '现用图':[{**a,'sha256':digest(a['现用文件'])} for a in ASSETS],
                '工作簿sha256':digest('交接资料/研究资料与综合数据.xlsx'),'校验':checks}
    (OUT/'交接版本与核对记录.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'版本':VERSION,'工作表':sheet_rows,'校验':checks},ensure_ascii=False,indent=2))


def validate(workbook, homes, campuses, observations, plans, routes, contexts):
    checks = []
    def check(ok, label):
        if not ok: raise AssertionError(label)
        checks.append(label)
    check(len(homes)==len({r['residence_id'] for r in homes})==22,'22住宅编号唯一')
    check(len(campuses)==len({r['campus_id'] for r in campuses})==43,'43园校编号唯一，13小学与30幼儿园')
    check(Counter(c['stage'] for c in campuses)=={'primary':13,'kindergarten':30},'现用园校只含小学与幼儿园')
    old_homes = read_csv(f'{OLD}/residences.csv')
    old_campuses = read_csv(f'{OLD}/education_campuses.csv')
    check({r['id'] for r in old_homes}.issubset({r['residence_id'] for r in homes}),'原18住宅编号全部沿用')
    check({r['id'] for r in old_campuses}=={r['campus_id'] for r in campuses},'原43园校编号逐项沿用')
    check(len(observations)==len({r['id'] for r in observations})==66,'66住房观察编号唯一')
    old_obs = read_csv(f'{OLD}/housing_observations.csv')
    check({r['id'] for r in old_obs}.issubset({r['id'] for r in observations}),'原63住房观察均保留')
    current_obs = {r['id']:r for r in observations}
    check(all(all(r[k]==current_obs[r['id']][k] for k in ('residence_id','value','unit','reference_period','observed_on')) for r in old_obs),'原住房观察的对象、数值、单位和时期不被静默改写')
    check(sum(h['map_price_status']=='comparable' for h in homes)==16,'16项目纳入同平台月参考价')
    changed = [r for r in observations if r['previous_metric']]
    check(len(changed)==1 and changed[0]['metric']=='platform_listing_page_average_cny_m2','珠江都荟挂牌均值更正及旧指标保留')
    check(all(h['map_crs']=='EPSG:4326' and h['longitude_wgs84'] and h['latitude_wgs84'] for h in homes+campuses),'22住宅及43园校使用WGS84制图坐标')
    check(len(plans)==73 and all(p['stage'] in ('primary','kindergarten') for p in plans),'73计划保持学段范围')
    check(any(p['subject_id']=='CAP-E004-053' and p['metric']=='owner_children_places' and float(p['value'])==0 for p in plans),'金穗本园2026业主名额明确为0')
    check(sum(p['subject_type']=='institution' and p['metric']=='classes' and float(p['value'])==7 for p in plans)==1,'天河第一小学7班机构计划仅一次')
    check(len(routes)==42 and sum(r['analytical_eligible']=='true' for r in routes)==41,'42原路线保留，41可作带标识分析')
    excluded = [r for r in routes if r['analytical_eligible']=='false']
    check(len(excluded)==1 and excluded[0]['origin_legacy_id']=='D3' and excluded[0]['destination_legacy_id']=='K7','D3至K7异常路线继续排除')
    check(sum(r['review_quality']=='legacy_name_address_matched_poi_gate_unverified' for r in routes)==2,'两条K7旧名路线标为补充')
    check(all(c['can_count_eligible_campuses']=='false' for c in contexts),'渠道情境不据以统计合格园校')
    book = load_workbook(workbook, data_only=False)
    check(book.sheetnames[0]=='资料清单','工作簿首先展示完整资料清单')
    check(all(any('\u4e00'<=c<='\u9fff' for c in r[1].value) for r in book['资料清单'].iter_rows(min_row=4)),'资料名称使用中文可读说明')
    check(book['住宅综合'].max_row-3==22 and book['园校综合'].max_row-3==43,'工作簿主体对象数正确')
    check(book['同址案例'].cell(5,6).value is None,'租户未知路线保持空白，不填零')
    check(all(c.value is None for row in book['收费证据'].iter_rows(min_row=4,min_col=12,max_col=12) for c in row),'未知家庭净支出保持空白')
    check(book['小学路线比较'].cell(12,7).value==25.7,'南国花园两指定路线差值以原始秒数算为25.7分钟')
    check(not any(c.data_type=='f' for ws in book for row in ws for c in row),'工作簿不含意外公式')
    check(all(digest(a['原文件'])==digest(a['现用文件']) for a in ASSETS),'15份现用图逐字节等于原图')
    check(all((ROOT/row[0].value).exists() for row in book['资料清单'].iter_rows(min_row=4,min_col=10,max_col=10)),'资料清单所有本地文件均存在')
    return checks


if __name__ == '__main__':
    make_workbook()

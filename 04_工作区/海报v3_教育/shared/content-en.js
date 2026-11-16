// English edition of Design E. Same structure as content2.js (window.K); numbers and sources are identical.
window.K = {
  lang: "en",
  ui: {
    rq: "Research question",
    s: { "01": "Where is Liede", "02": "Three concepts", "03": "Methods", "04": "Finding 1", "05": "Finding 2 · Housing status and eligibility", "06": "Sociological analysis", "07": "Limitations & reflexivity", "08": "References" },
    concl: "CONCLUSION",
    inLiede: "In Liede: ",
    chHead: ["Household", "Documents required", "Route"],
    refl: "Reflexivity",
    hiQuestion: [["house prices, hukou, or housing status", "<b>house prices</b>, <b>hukou</b>, or <b>housing status</b>"]],
  },
  courseName: "Social Inequality and Social Mobility",
  week: "Week 7: Education, Migration & Hukou",
  fieldShort: "Fieldwork 7 Nov 2026",
  members: "Zhiwei Ma · Zebin Chen · Xiaoyu Fang · Qiuyu Zhao · Yueyang Rao",

  title: ["Schools Next Door in Liede:", "Hukou and Housing Status Decide Entry"],
  titleHi: "Hukou and Housing Status",
  subtitle: "House prices barely change how many schools are nearby; within one catchment, resettled villagers, owners and renters enter with different documents.",
  question:
    "Among families living equally close to schools in Liede, what drives the gap in admission: house prices, hukou, or housing status?",
  coverCaption: "Cover: Liede ancestral hall roof and Zhujiang New Town towers. Team photo, 7 Nov 2026",

  background:
    "Liede Village was redeveloped from 2007; villagers returned to the rebuilt Liede Garden in 2010, Guangzhou's first urban-village renewal [9]. Its ancestral halls now sit among Zhujiang New Town's towers, with resettled villagers, owners, renters and migrants a kilometre or two apart, at CNY 54,500–173,700/m² [11].",
  timeline: [
    ["2007", "Redevelopment [9]"],
    ["2010", "Villagers return [9]"],
    ["2026", "Agreements count [4]"],
  ],

  concepts: [
    { key: "Social closure", who: "Weber, 1978 [1]", week: "Course week 2", def: "Groups restrict access to resources through eligibility rules.", use: "Each route has entry conditions; living nearby is not one." },
    { key: "Hukou stratification", who: "Wu & Treiman, 2004 [3]", week: "Course week 7", def: "Hukou sorts people into different public-service entitlements.", use: "One estate; local, migrant, HK/Macao families, three routes." },
    { key: "Legibility", who: "Scott, 1998 [2]", week: "Further reading", def: "States see people through registered, standardised records.", use: "Residence counts only as a deed, agreement or filed lease." },
  ],

  methods: [
    { k: "A", t: "Field observation", d: "All-day walk, 7 Nov: housing, school gates, streets. Buildings only; no children; no interviews." },
    { k: "B", t: "Price & environment audit", d: "22 estates and 43 schools geocoded; 16 comparable prices; 6 walking routes." },
    { k: "C", t: "Policy & literature", d: "Tianhe's 2026 admission rules and quotas; sociological literature." },
  ],

  kpi1: { n: "6<i>:</i>7", t: "Median schools within 500 m", s: "Estates ≥ vs < CNY 100k/m²" },
  kpi2: { n: "5", t: "routes into school", s: "Sorted by hukou and housing status" },

  f1: {
    title: "Nearby schools barely track house prices",
    leadE: "Within 800 m both groups have a median of 11 schools; the priciest and cheapest estates share a catchment.",
    caption: "Fig. 1  Shading: schools within 500 m; dots: estates by price rank. Prices are platform reference values; counts are not school places [10–12].",
  },

  f2: {
    title: "Same catchment, different paperwork",
    leadE: "Tianhe's 2026 rules route families in one catchment by their documents [4–7]. Right: resettlement vs commodity estate.",
    rows: [
      { who: "Local-hukou owner", doc: "Deed + hukou book; living at the address", ch: "Catchment place" },
      { who: "Resettled villager", doc: "Relocation agreement + Guangzhou hukou", ch: "Allocation, catchment 1st" },
      { who: "Guangzhou renter", doc: "No home in city + filed lease (to Aug 2028)", ch: "District allocation" },
      { who: "Migrant family", doc: "Points review, ranking, preferences", ch: "Points admission" },
      { who: "HK/Macao resident", doc: "Special eligibility; 45 places at Nanguo", ch: "HK/Macao quota" },
    ],
    note: "Routes set by policy, not observed families; admission outcomes unknown.",
  },

  compare: {
    a: { name: "Liede Garden", type: "Rebuilt resettlement housing (2010)" },
    b: { name: "Nanguo Garden", type: "Commodity housing, Zhujiang New Town" },
  },
  cmpRows: [
    { k: "Reference price", a: { big: "—", s: "No comparable price [8]" }, b: { big: "9.03", u: "CNY 10k/m²", s: "Asking rent 69–73/m²/month" } },
    { k: "Schools within 500 m", a: { big: "3" }, b: { big: "8" } },
    { k: "Walk to catchment primary", a: { big: "5.9", u: "min", s: "Liede Exp. Primary" }, b: { big: "2.8", u: "min", s: "Nanguo School Primary" } },
    { k: "Owner-priority kindergarten places", a: { big: "85<small>/135</small>", s: "Liede Kindergarten [6]" }, b: { big: "24<small>/68</small>", s: "Tianhe No.2 Exp. KG [6]" } },
  ],
  cmpNote: "Fig. 2  Left: Liede ancestral hall (team). Right: Nanguo School (web). Walks: Amap one-way estimates; gates and owner-priority buildings unverified.",
  kgPhoto: { t: "Fig. 3  Liede Kindergarten (33 Haiyue Rd)", c: "In 2026, 85 of 135 places go first to eligible owners' children in matched estates [6]. Web photo (2022), date unverified." },

  analysis: [
    { h: "Who gets in next door", t: "Local-hukou owners living at their deeded address get catchment places; resettled villagers with relocation agreements come next. Renters and migrants in the same block need filings, points or quotas." },
    { h: "History as a credential", t: "The relocation agreement began as land-and-housing compensation; admission rules now read it as proof of status. Only registered residence counts: legibility in practice." },
    { h: "Implications for mobility", t: "Starting points depend not only on the home a family can buy but on how hukou and housing status combine. Over time the gaps may divide local and migrant families; outcomes were not observed." },
  ],
  conclusion: {
    lead: "In Liede, schools are close;<br>the barrier is paperwork.",
    body: "Higher prices did not buy more nearby schools; within one catchment, hukou and housing status sort families into different routes.",
    next: "Next: Where do allocated renters' children end up?<br>What does assembling the documents cost?",
  },

  limits: [
    ["Sample", "Purposive list, not a census; results hold for this sample only."],
    ["Prices", "Platform reference prices, mixed months, n = 16; sensitive to month and radius."],
    ["Scenarios", "Household types come from policy texts, not real families."],
    ["Fieldwork", "One day on site; no parent interviews or school visits."],
  ],
  reflexivity:
    "We read the system through policy texts and maps, seeing written rules. As students who neither live here nor choose schools, we likely underestimate the paperwork burden.",

  refs: [
    "Weber, M. (1978). <i>Economy and society</i>. Univ. of California Press.",
    "Scott, J. C. (1998). <i>Seeing like a state</i>. Yale University Press.",
    "Wu, X., & Treiman, D. J. (2004). The household registration system and social stratification in China: 1955–1996. <i>Demography, 41</i>(2), 363–384.",
    "Tianhe District Education Bureau. (2026). <i>Compulsory-education admission rules</i> (Annexes 5, 9) [in Chinese].",
    "Tianhe District Education Bureau. (2026). <i>Points-based admission guide</i> [in Chinese].",
    "Tianhe District Education Bureau. (2026). <i>Kindergarten admission plan and quotas</i> [in Chinese].",
    "Tianhe District Education Bureau. (2026). <i>HK and Macao residents' school-place guide</i> [in Chinese].",
    "Liede Subdistrict People's Congress Office. (2020). <i>Liede's rebuilt estates</i> [in Chinese].",
    "Tianhe District Gazetteer Office. (2011). <i>Tianhe Yearbook 2011</i> (Liede Subdistrict) [in Chinese].",
    "OpenStreetMap contributors. (2026). Liede basemap extract (ODbL).",
    "Fang.com. (2026). Estate reference prices and listings, Aug–Nov [in Chinese].",
    "Amap. (2026). Walking-route estimates, 12 Nov 2026 [in Chinese].",
  ],
  credit: "Photos: ancestral hall by the team; school photos from public web reports, sources noted. Basemap © OpenStreetMap contributors.",
};

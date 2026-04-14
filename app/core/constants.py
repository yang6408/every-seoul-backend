from enum import Enum


class RssCategory(str, Enum):
    NOTICE = "notice"
    PRESS = "press"
    EVENT = "event"
    EDU = "edu"


class SeoulDistrict(str, Enum):
    GANGNAM = "Gangnam"
    GANGDONG = "Gangdong"
    GANGBUK = "Gangbuk"
    GANGSEO = "Gangseo"
    GWANAK = "Gwanak"
    GWANGJIN = "Gwangjin"
    GURO = "Guro"
    GEUMCHEON = "Geumcheon"
    NOWON = "Nowon"
    DOBONG = "Dobong"
    DONGDAEMUN = "Dongdaemun"
    DONGJAK = "Dongjak"
    MAPO = "Mapo"
    SEODAEMUN = "Seodaemun"
    SEOCHO = "Seocho"
    SEONGDONG = "Seongdong"
    SEONGBUK = "Seongbuk"
    YANGCHEON = "Yangcheon"
    YEONGDEUNGPO = "Yeongdeungpo"
    YONGSAN = "Yongsan"
    EUNPYEONG = "Eunpyeong"
    JONGNO = "Jongno"
    JUNG = "Jung"
    JUNGNANG = "Jungnang"
    SONGPA = "Songpa"


DISTRICT_RSS_URLS = {
    SeoulDistrict.GANGNAM: {
        RssCategory.NOTICE: "https://www.gangnam.go.kr/portal/rss/rssList.do?bbsId=B_000045&recordCountPerPage=10",
        RssCategory.PRESS: "https://www.gangnam.go.kr/portal/rss/rssList.do?bbsId=B_000031&recordCountPerPage=10",
        RssCategory.EVENT: "https://www.gangnam.go.kr/portal/rss/rssList.do?bbsId=B_000001&menuNo=200095&recordCountPerPage=30",
    },
    SeoulDistrict.GANGDONG: {
        RssCategory.NOTICE: "https://www.gangdong.go.kr/web/newportal/rss/b_068/list?cp=1&baCategory1=U0072",
    },
    SeoulDistrict.GANGBUK: {
        RssCategory.NOTICE: "https://func.seoul.go.kr/data/RSS/rss_news.xml?1=1",
    },
    SeoulDistrict.GANGSEO: {
        RssCategory.NOTICE: "https://www.gangseo.seoul.kr/gs040101.rss?1=1",
        RssCategory.PRESS: "https://www.gangseo.seoul.kr/gs040201.rss?1=1",
    },
    SeoulDistrict.GWANAK: {
        RssCategory.NOTICE: "http://www.gwanak.go.kr/site/gwanak/publicData/PublicData.do?dataid=rss&cbIdx=239",
    },
    SeoulDistrict.GWANGJIN: {
        RssCategory.PRESS: "https://www.gwangjin.go.kr/portal/bbs/B0000002/rssService.do?viewType=CONTBODY&bbsId=B02",
        RssCategory.NOTICE: "https://www.gwangjin.go.kr/portal/bbs/B0000001/rssService.do?viewType=CONTBODY&bbsId=B01",
    },
    SeoulDistrict.GURO: {
        RssCategory.NOTICE: "https://www.guro.go.kr/rssBbsNtt.do?bbsNo=662&integrDeptCode=",
    },
    SeoulDistrict.GEUMCHEON: {
        RssCategory.PRESS: "https://www.geumcheon.go.kr/portal/rssBbsNtt.do?key=297&id=&bbsNo=8&searchCtgry=&pageUnit=10&searchCnd=all&searchKrwd=&integrDeptCode=&searchDeptCode=&pageIndex=1",
    },
    SeoulDistrict.NOWON: {
        RssCategory.NOTICE: "https://www.nowon.kr/www/user/bbs/ND_selectRssList.do?q_bbsCode=1001&q_estnColumn1=11",
    },
    SeoulDistrict.DOBONG: {
        RssCategory.NOTICE: "https://www.dobong.go.kr/WDB_common/rss/bbs.asp?code=10004124",
    },
    SeoulDistrict.DONGJAK: {
        RssCategory.NOTICE: "https://www.dongjak.go.kr/portal/bbs/B0000022/rssService.do?menuNo=200641",
        RssCategory.EVENT: "https://www.dongjak.go.kr/portal/bbs/B0000173/rssService.do?menuNo=201030",
    },
    SeoulDistrict.MAPO: {
        RssCategory.NOTICE: "https://www.mapo.go.kr/site/main/rss/notice/list?1=1",
        RssCategory.EVENT: "https://www.mapo.go.kr/site/culture/rss/culturevent/list?1=1",
    },
    SeoulDistrict.SEODAEMUN: {
        RssCategory.NOTICE: "http://www.sdm.go.kr/rss/rssBoard.do?seq=106",
    },
    SeoulDistrict.SEONGDONG: {
        RssCategory.NOTICE: "https://www.sd.go.kr/rssBbsNtt.do?bbsNo=183",
    },
    SeoulDistrict.YANGCHEON: {
        RssCategory.NOTICE: "https://www.yangcheon.go.kr/rss/yangcheon/board/254.do?siteCd=yangcheon",
        RssCategory.PRESS: "https://www.yangcheon.go.kr/rss/yangcheon/board/290.do?siteCd=yangcheon",
    },
    SeoulDistrict.YONGSAN: {
        RssCategory.NOTICE: "",
    },
    SeoulDistrict.JONGNO: {
        RssCategory.NOTICE: "https://www.jongno.go.kr/Rss.do?fid=Notice",
    },
    SeoulDistrict.JUNGNANG: {
        RssCategory.NOTICE: "https://www.jungnang.go.kr/portal/bbs/rss/B0000002.do?menuNo=200473",
    },
}

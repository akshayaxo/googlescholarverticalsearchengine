from urllib.parse import urlencode
from scrapy import Selector
import scrapy

class GoogleScholarSpider(scrapy.Spider):
    name = 'googlescholarSpider'
    start_url = 'https://pureportal.coventry.ac.uk/en/organisations/coventry-university/persons/'
    count = 1
    def start_requests(self):
        yield scrapy.Request(self.start_url,
                             callback=self.parse
                             )

    def parse(self, response):
        self.logger.debug("started")
        sel = Selector(response)

        for res in sel.css('h3.title'):
            link = res.css('a::attr(href)').extract_first()
            baseAuthorLink = response.urljoin(link)
            yield scrapy.Request(response.urljoin(link), callback=self.parse_link,
                                 cb_kwargs=dict(main_url=baseAuthorLink, page=20)
                                 )

        nextPageButton = response.xpath(
            "//button[@class='gs_btnPR gs_in_ib gs_btn_half gs_btn_lsb gs_btn_srt gsc_pgn_pnx']").extract_first()

        if 'disabled' not in nextPageButton:
            if response.xpath(
                    "//button[@class='gs_btnPR gs_in_ib gs_btn_half gs_btn_lsb gs_btn_srt gsc_pgn_pnx']/@onclick").extract_first() != "":
                next_page_url = response.xpath(
                    "//button[@class='gs_btnPR gs_in_ib gs_btn_half gs_btn_lsb gs_btn_srt gsc_pgn_pnx']/@onclick").extract_first().replace(
                    "\\x3d", "=").replace("\\x26", "?")

            count = next_page_url.count('?')
            after_author = next_page_url.split("?")[count - 1]
            start = next_page_url.split("?")[count]
            join_url = "&" + after_author + "&" + start

            url = self.start_url + join_url
            if start is not None:
                yield scrapy.Request(url, callback=self.parse
                                     )

    def parse_link(self, response, main_url, page):

        sel = Selector(response)
        for res in sel.css('tr.gsc_a_tr'):
            paperUrl = 'https://scholar.google.co.uk' + res.css('td.gsc_a_t > a::attr(data-href)').extract_first()
            yield scrapy.Request(paperUrl, callback=self.parse_paper
                                 )
        show_More = sel.css('#gsc_bpf_more').extract_first()
        loopNext = 'disabled' not in show_More
        if loopNext:
            url = main_url + '&' + urlencode({'cstart': page, 'pagesize': '100'})

            yield scrapy.Request(url, callback=self.parse_link, cb_kwargs=dict(main_url=main_url, page=page + 100))

    def parse_paper(self, response):
        self.count = self.count + 1
        self.logger('Crawled Pages: ' + str(self.count))
        sel = Selector(response)
        paperUrl = sel.css('a.gsc_vcd_title_link::attr(href)').extract_first()
        title = sel.css('a.gsc_vcd_title_link::text').extract_first()
        authors = sel.css('#gsc_vcd_table div:nth-child(n+1) div.gsc_vcd_value::text').extract_first()
        year = sel.css('#gsc_vcd_table div:nth-child(n+2) div.gsc_vcd_value::text').extract_first()
        description = sel.css('#gsc_vcd_descr ::text').extract_first()
        if (not title) or not len(title.strip()):
            title = sel.css('#gsc_vcd_title ::text').extract_first()
            paperUrl = response.url
        if (not description) or not len(description.strip()):
            description = ''
        item = {'title': title, 'PaperUrl': paperUrl, 'Authors': authors, 'PublishedDate': year,
                'description': description}
        yield item

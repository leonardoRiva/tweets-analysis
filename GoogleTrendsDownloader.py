
from pytrends.request import TrendReq


class GoogleTrendsDownloader():
    """
    wrapper for pytrends library
    """


    def __init__(self, language, timezone, keywords, category, timeframe, properties=''):
        self.pytrends = TrendReq(hl=language, tz=timezone)
        self.pytrends.build_payload(keywords, cat=category, 
                            timeframe=timeframe, geo=language, gprop=properties)


    def interest_over_time(self):
        return self.pytrends.interest_over_time()

    
    def related_topics(self):
        return self.pytrends.related_topics()

    
    def related_queries(self):
        return self.pytrends.related_queries()


    def interest_by_region(self):
        return self.pytrends.interest_by_region(resolution='REGION', inc_low_vol=True, inc_geo_code=False)


import re
import random
import urllib
import urllib2 as urllib
import urlparse
import json
from datetime import datetime
from PIL import Image
from cStringIO import StringIO

VERSION_NO = '1.2013.06.02.1'
DATEFORMAT = '%B %d, %Y'
XPATHS = {
        'MetadataDate': '/html/body/div/div/article/section[2]/div/div/div[1]/p'
    }

def any(s):
    for v in s:
        if v:
            return True
    return False



def Start():
    HTTP.CacheTime = CACHE_1DAY

class EXCAgent(Agent.Movies):
   
    name = 'Playboy Plus'
    languages = [Locale.Language.English]
    accepts_from = ['com.plexapp.agents.localmedia']
    primary_provider = True

    def DoPrimarySearch(self,keyword):
        query = 'http://www.playboyplus.com/search/?keywords=' + keyword.replace(" ","+") + '&type=gallery'
        searchResults = HTML.ElementFromURL(query)
        return searchResults.xpath('//a[contains(@class,"title")]')

    def SetDateMetadata(self,date):
        date_object = datetime.strptime(date, DATEFORMAT)
        return date_object

    def search(self, results, media, lang):
        
        title = media.name
        if media.primary_metadata is not None:
            title = media.primary_metadata.title

        Log('*******MEDIA TITLE****** ' + str(title))

        # Search for year
        year = media.year
        if media.primary_metadata is not None:
            year = media.primary_metadata.year

        if 'http://' not in title: 
            searchResults = self.DoPrimarySearch(title)
            for searchResult in searchResults:
                resultTitle = searchResult.text_content()
                curID = searchResult.get('href').replace('/','_')
                score = 100 - Util.LevenshteinDistance(title.lower(), resultTitle.lower())
                results.Append(MetadataSearchResult(id = curID, name = resultTitle, score = score, lang = lang))
        else:
            curID = title.replace('/','_')
            results.Append(MetadataSearchResult(id = curID, name = 'user defined', score = 100, lang = lang))
        results.Sort('score', descending=True)            

    def update(self, metadata, media, lang):

        Log('******UPDATE CALLED*******')
        metadata.studio = 'Playboy Plus'
        if 'http' in str(metadata.id):
            url = str(metadata.id).replace('_','/')
        else:
            url = 'http://www.playboyplus.com/' + str(metadata.id).replace('_','/')

        detailsPageElements = HTML.ElementFromURL(url)
        metadata.title = detailsPageElements.xpath('//h1')[0].text_content()
        metadata.summary = detailsPageElements.xpath('//div[contains(@class,"description")]')[0].text_content().replace("Description:","").strip()
        metadata.originally_available_at = self.SetDateMetadata(detailsPageElements.xpath(XPATHS['MetadataDate'])[0].text_content().replace("Uploaded: ","").strip())
        metadata.year = metadata.originally_available_at.year

        metadata.roles.clear()
        metadata.collections.clear()
     
        starring = None
        starring = detailsPageElements.xpath('//p[contains(@class,"gallery-models")]//a')
        for member in starring:
            role = metadata.roles.new()
            actor = member.text_content().strip()
            role.actor = actor
            metadata.collections.add(member.text_content().strip())

        self.GetPosterArt(metadata,detailsPageElements)

    def GetPosterArt(self,metadata,detailsPageElements):

        posterCounter = 0
	backgroundCounter = 0

        images = detailsPageElements.xpath('//ul[contains(@class,"thumbnail-listing")]//a')

        for i in images:
            src = i.get('href')
            img_file = urllib.urlopen(src)
            im = StringIO(img_file.read())
            resized_image = Image.open(im)
            width, height = resized_image.size
            Log(str(width))
            Log(str(height))
            if(height > width):
                    metadata.posters[src] = Proxy.Preview(HTTP.Request(src, headers={'Referer': 'http://www.google.com'}).content, sort_order = posterCounter)
                    posterCounter = posterCounter + 1
            else:
                    metadata.art[src] = Proxy.Preview(HTTP.Request(src, headers={'Referer': 'http://www.google.com'}).content, sort_order = backgroundCounter)
                    backgroundCounter = backgroundCounter + 1
				
